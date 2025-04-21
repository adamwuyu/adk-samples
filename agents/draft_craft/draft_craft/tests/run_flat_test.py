#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""扁平化架构Sequential Orchestrator的测试脚本。"""

import asyncio
import sys
import os
import argparse
from pprint import pprint
import re
import uuid
from datetime import datetime

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from draft_craft.tools import check_progress

# 解析命令行参数
parser = argparse.ArgumentParser(description='扁平化写作智能体draft_craft的集成测试')
parser.add_argument('--use-llm', action='store_true', help='使用LLM实时生成内容，而不是模拟内容')
args = parser.parse_args()

# 根据命令行参数设置环境变量
if args.use_llm:
    os.environ["USE_LLM_GENERATOR"] = "true"
    print("已启用LLM实时生成内容模式")
else:
    os.environ["USE_LLM_GENERATOR"] = "false"
    print("已启用模拟内容生成模式（默认）")

# 将项目根目录添加到sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    print(f"Added project root to sys.path: {PROJECT_ROOT}")

# 导入Agent和状态管理器
from draft_craft import root_agent
from draft_craft.tools.state_manager import (
    INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, 
    ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)

# 应用和用户常量定义
APP_NAME = "writing_scoring_flat_app"
USER_ID = "flat_test_user"
SESSION_ID = "flat_test_session_001"

# 多组测试数据，便于手动切换
TEST_CASES = [
    # 家长教育主题（原有）
    {
        INITIAL_MATERIAL_KEY: "关于如何帮助孩子适应初中生活的几篇文章摘要：\n"
                            "1. 心理专家张教授指出，初中阶段是孩子心理发展的关键期，家长应更注重与孩子的情感沟通。\n"
                            "2. 多项研究表明，良好的作息习惯和自主学习能力是孩子适应初中学习的关键因素。\n"
                            "3. 某重点中学班主任李老师建议家长帮助孩子提前了解初中学习特点，避免因不适应导致成绩下滑。\n"
                            "4. 心理咨询师王医生强调，初中生社交圈扩大，家长应鼓励孩子参与集体活动，提升社交能力。",
        INITIAL_REQUIREMENTS_KEY: "写一篇面向小学高年级和初中孩子家长的文章，主题为《如何帮助孩子顺利适应初中生活》，"
                               "文章应包含实用建议和案例分析，语言通俗易懂，篇幅800-1000字。",
        INITIAL_SCORING_CRITERIA_KEY: "请从内容相关性、建议可操作性、语言通俗性、结构清晰度、观点积极性、信息可靠性等维度进行评分。"
                                   "特别关注文章是否符合中等教育水平家长的阅读习惯和需求，是否提供了具体可行的建议。",
        "audience_profile": "目标受众是中等收入、中等教育水平的家长，孩子处于小学高年级至高中一年级阶段。"
                           "这些家长高度关注孩子的学业与升学、身心健康、亲子关系、品格与社会适应等方面。"
                           "他们偏好清晰、直白、易懂的语言，喜欢有明确实用建议的内容，乐于为孩子教育投入资源。"
                           "在阅读时，他们更看重内容的实用性、可信度和是否能解决实际问题。"
    },
    # 职场新人适应主题
    {
        INITIAL_MATERIAL_KEY: "关于职场新人如何快速适应新环境的几条建议：\n"
                            "1. 多与同事沟通，主动请教，建立良好人际关系。\n"
                            "2. 了解公司文化和规章制度，避免触碰红线。\n"
                            "3. 主动承担任务，展现责任心和学习能力。\n"
                            "4. 保持积极心态，遇到困难及时寻求帮助。",
        INITIAL_REQUIREMENTS_KEY: "写一篇面向刚入职场的大学毕业生的文章，主题为《如何快速适应职场环境》，"
                               "内容应包含实际建议和典型案例，语言简明，篇幅600-800字。",
        INITIAL_SCORING_CRITERIA_KEY: "请从建议实用性、案例相关性、结构清晰度、语言表达、目标适配性等维度进行评分。",
        "audience_profile": "目标受众为刚刚步入职场的大学毕业生，年龄22-26岁，缺乏实际工作经验，渴望获得实用的职场建议和心理支持。"
                           "他们关注如何快速融入团队、提升工作能力、处理人际关系等问题。"
    },
    # AI写作工具科普主题
    {
        INITIAL_MATERIAL_KEY: "AI写作工具是一种利用人工智能技术帮助人们创作文本内容的软件或应用。\n"
                            "它们通常基于大型语言模型(LLM)，如GPT系列、Claude或Gemini等，能够根据用户提供的提示生成各种类型的文本。\n"
                            "这些工具的功能多种多样，从简单的文本补全、语法检查到完整的文章生成、创意写作等。\n"
                            "市场上常见的AI写作工具包括Jasper、Copy.ai、Rytr、Writesonic等，同时OpenAI的ChatGPT、Anthropic的Claude也被广泛用于写作辅助。\n"
                            "AI写作工具的工作原理是分析大量文本数据，学习语言模式、结构和风格，然后根据用户的需求生成相应的内容。",
        INITIAL_REQUIREMENTS_KEY: "写一篇面向普通互联网用户的科普文章，主题为《AI写作工具是什么，有哪些优缺点》，"
                               "要求内容全面、结构清晰、语言通俗，篇幅700-900字。",
        INITIAL_SCORING_CRITERIA_KEY: "请从内容全面性、结构清晰度、表达准确性、通俗易懂、案例丰富性等维度进行评分。",
        "audience_profile": "目标受众为对AI技术感兴趣但缺乏专业背景的普通互联网用户，年龄18-45岁，关注新技术对生活和工作的影响，"
                           "希望通过文章快速了解AI写作工具的基本原理、应用场景及其优缺点。"
    },
    # 必不及格测试用例
    {
        INITIAL_MATERIAL_KEY: "素材极其简略，仅一句话。",
        INITIAL_REQUIREMENTS_KEY: "写一篇结构复杂、内容丰富、案例详实的长文，要求极高。",
        INITIAL_SCORING_CRITERIA_KEY: "必须有5个真实案例，结构极清晰，语言极优美，创新性强。",
        "audience_profile": "专家级评审",
        "score_threshold": 92
    }
]

# 默认使用必不及格测试用例
TEST_INITIAL_DATA = TEST_CASES[-1]

async def async_main():
    log_path = os.path.join(os.path.dirname(__file__), "logs", "flat_test_debug.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"[RUN START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        def log(msg):
            log_file.write(msg + "\n")
            log_file.flush()
        log("[DEBUG] 测试流程开始")
        print("\n--- 开始扁平化架构测试 (ADK Runner) ---")
        
        # 1. 初始化SessionService
        session_service = InMemorySessionService()
        log("✅ Session Service初始化完成")
        
        # 2. 创建会话并设置初始状态
        log("\n初始数据 (将设置在初始会话状态中):")
        pprint(TEST_INITIAL_DATA)
        
        session = session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state=TEST_INITIAL_DATA
        )
        log(f"✅ Session已创建: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'，已设置初始状态")
        
        # 3. 创建Runner
        runner = Runner(
            agent=root_agent,
            session_service=session_service,
            app_name=APP_NAME
        )
        log(f"✅ 已为Agent '{root_agent.name}'创建Runner")
        
        # 4.1 检查初始数据
        log("\n>>> 第1步: 检查初始数据")
        init_check_message = "请检查初始数据是否齐全。"
        content = types.Content()
        if content.parts is None:
            content.parts = []
        part = types.Part()
        part.text = init_check_message
        content.parts.append(part)
        async for event in runner.run_async(
            new_message=content,
            user_id=USER_ID,
            session_id=SESSION_ID
        ):
            # 简洁日志输出
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts and hasattr(event.content.parts[0], "text") and event.content.parts[0].text:
                    log(f"[FINAL] {event.content.parts[0].text}")
                else:
                    log(f"[FINAL] {event}")
            elif hasattr(event, "get_function_calls") and event.get_function_calls():
                for call in event.get_function_calls():
                    log(f"[TOOL_CALL] {call.name} args={call.args}")
            elif hasattr(event, "get_function_responses") and event.get_function_responses():
                for resp in event.get_function_responses():
                    log(f"[TOOL_RESP] {resp.name} result={resp.response}")
        
        # 4.2 生成初始文稿
        log("\n>>> 第2步: 生成初始文稿")
        create_draft_message = "请根据要求生成文稿。"
        content = types.Content()
        content.parts = [types.Part()]
        content.parts[0].text = create_draft_message
        async for event in runner.run_async(
            new_message=content,
            user_id=USER_ID,
            session_id=SESSION_ID
        ):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts and hasattr(event.content.parts[0], "text") and event.content.parts[0].text:
                    log(f"[FINAL] {event.content.parts[0].text}")
                else:
                    log(f"[FINAL] {event}")
            elif hasattr(event, "get_function_calls") and event.get_function_calls():
                for call in event.get_function_calls():
                    log(f"[TOOL_CALL] {call.name} args={call.args}")
            elif hasattr(event, "get_function_responses") and event.get_function_responses():
                for resp in event.get_function_responses():
                    log(f"[TOOL_RESP] {resp.name} result={resp.response}")
        
        # 4.3 评分文稿
        log("\n>>> 第3步: 评分文稿")
        score_message = "请使用score_for_parents工具对当前文稿进行评分，评分时从中等家长受众的视角出发，参考audience_profile字段中的受众画像，按照评分标准全面评估文稿质量。请确保传递文稿内容、受众画像和评分标准三个参数。"
        content = types.Content()
        content.parts = [types.Part()]
        content.parts[0].text = score_message
        async for event in runner.run_async(
            new_message=content,
            user_id=USER_ID,
            session_id=SESSION_ID
        ):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts and hasattr(event.content.parts[0], "text") and event.content.parts[0].text:
                    log(f"[FINAL] {event.content.parts[0].text}")
                else:
                    log(f"[FINAL] {event}")
            elif hasattr(event, "get_function_calls") and event.get_function_calls():
                for call in event.get_function_calls():
                    log(f"[TOOL_CALL] {call.name} args={call.args}")
            elif hasattr(event, "get_function_responses") and event.get_function_responses():
                for resp in event.get_function_responses():
                    log(f"[TOOL_RESP] {resp.name} result={resp.response}")
        
        # 5. 检查最终会话状态
        final_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        if final_session:
            # 打印关键状态字段，避免打印过长的内容
            state_metadata = {}
            for key, value in final_session.state.items():
                if isinstance(value, str) and len(value) > 100:
                    state_metadata[key] = f"{value[:100]}... (长度: {len(value)}字符)"
                else:
                    state_metadata[key] = value
            # 控制台只输出关键信息
            draft = final_session.state.get(CURRENT_DRAFT_KEY)
            score = final_session.state.get(CURRENT_SCORE_KEY)
            feedback = final_session.state.get(CURRENT_FEEDBACK_KEY)
            iteration = final_session.state.get(ITERATION_COUNT_KEY)
            is_complete = final_session.state.get(IS_COMPLETE_KEY)
            log(f"[最终状态] 草稿: {'有' if draft else '无'}，分数: {score}，反馈: {'有' if feedback else '无'}，迭代: {iteration}，完成: {is_complete}")
            # 结果统计
            log("\n[结果统计]")
            log(f"草稿长度: {len(draft) if draft else 0}")
            log(f"反馈长度: {len(feedback) if feedback else 0}")
            log(f"分数: {score}")
            log(f"是否完成: {is_complete}")
        else:
            log("错误: 无法检索最终会话状态")
        
        log("\n--- 扁平化架构测试 (ADK Runner) 已完成 ---")
        log("[DEBUG] 测试流程结束")


if __name__ == "__main__":
    asyncio.run(async_main()) 