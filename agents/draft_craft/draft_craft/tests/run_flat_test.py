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
import logging
import sys
import os
import argparse
from pprint import pprint
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 解析命令行参数
parser = argparse.ArgumentParser(description='测试扁平化架构Sequential Orchestrator')
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
from draft_craft.tools.logging_utils import setup_logging

# 配置日志
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("测试脚本启动，已配置日志系统")

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
    }
]

# 默认使用第一组数据，便于手动切换
TEST_INITIAL_DATA = TEST_CASES[0]

async def run_agent_and_get_final_response(runner, session_service, app_name, session_id, query=None):
    """运行Agent并获取最终响应"""
    print(f">>> 用户查询 (发送给Runner): {query}")
    
    all_events = []
    score_text = None
    # 使用正确的命名参数
    async for event in runner.run_async(
        new_message=query,
        user_id="flat_test_user",
        session_id=session_id
    ):
        all_events.append(event)
        
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            if any(hasattr(part, 'function_call') for part in event.content.parts):
                function_call_part = next((part for part in event.content.parts if hasattr(part, 'function_call')), None)
                if function_call_part and function_call_part.function_call:
                    function_name = getattr(function_call_part.function_call, 'name', 'unknown')
                    print(f">>> Function call: {function_name}")
                    
                    # 检测保存家长评分结果的工具调用
                    if function_name == "save_parents_scoring_result" and hasattr(function_call_part.function_call, 'args'):
                        if hasattr(function_call_part.function_call.args, 'llm_output'):
                            llm_output = function_call_part.function_call.args.llm_output
                            
                            # 从LLM输出中提取分数
                            score_match = re.search(r'评分：(\d+)', llm_output)
                            if score_match:
                                score = float(score_match.group(1))
                                feedback = llm_output
                                
                                # 手动保存评分和反馈
                                print(f">>> 提取家长评分: {score}, 反馈长度: {len(feedback)}")
                                session = session_service.get_session(
                                    app_name=app_name, 
                                    user_id=USER_ID, 
                                    session_id=session_id
                                )
                                session.state['current_score'] = score
                                session.state['current_feedback'] = feedback
                                session.state['is_complete'] = score >= 90.0  # 家长评分从80分提高到90分
                                
                                # 记录保存状态
                                print(f"✅ 已保存家长评分: {score}")
                                print(f"✅ 已保存家长评价反馈 (长度: {len(feedback)})")
                                print(f"✅ 已设置完成状态: {session.state['is_complete']}")
                    
                    # 如果是save_draft_result，直接保存草稿内容
                    if function_name == "save_draft_result" and hasattr(function_call_part.function_call, 'args') and function_call_part.function_call.args:
                        if hasattr(function_call_part.function_call.args, 'content'):
                            draft_content = function_call_part.function_call.args.content
                            
                            # 手动保存草稿内容
                            print(f">>> 手动保存草稿，长度: {len(draft_content)}")
                            session = session_service.get_session(
                                app_name=app_name, 
                                user_id=USER_ID, 
                                session_id=session_id
                            )
                            session.state['current_draft'] = draft_content
                            session.state['iteration_count'] = 1
            elif any(hasattr(part, 'text') for part in event.content.parts):
                text_part = next((part for part in event.content.parts if hasattr(part, 'text')), None)
                text_content = getattr(text_part, 'text', '')
                if text_content and (len(text_content) > 100 or any(kw in text_content for kw in ['AI写作工具', '人工智能', '创意写作'])):
                    print(f">>> Text Content: {text_content[:100]}... 检测到草稿内容!")
                    
                    # 如果检测到草稿内容，手动保存草稿并调用评分工具
                    session = session_service.get_session(
                        app_name=app_name, 
                        user_id=USER_ID, 
                        session_id=session_id
                    )
                    if not session.state.get('current_draft'):
                        print("未检测到自动保存草稿，手动保存...")
                        session.state['current_draft'] = text_content
                        session.state['iteration_count'] = 1
                        
                        # 手动调用评分工具
                        print("已手动保存草稿，现在执行评分步骤...")
                        
                        # 创建评分请求
                        scoring_request = "请根据评分标准对当前文稿进行评分，给出0-10分的分数和详细反馈。"
                        
                        # 发送评分请求并等待响应
                        scoring_events = []
                        async for scoring_event in runner.run_async(
                            new_message=scoring_request, 
                            user_id=USER_ID,
                            session_id=session_id
                        ):
                            scoring_events.append(scoring_event)
                            
                            # 尝试提取分数和反馈
                            if hasattr(scoring_event, 'content') and scoring_event.content and hasattr(scoring_event.content, 'parts'):
                                text_parts = [part.text for part in scoring_event.content.parts if hasattr(part, 'text')]
                                if text_parts:
                                    score_text = text_parts[0]
                                    if score_text:
                                        # 尝试提取分数
                                        score_match = re.search(r'(\d+(\.\d+)?)(?:/10)?分?', score_text)
                                        feedback = score_text
                                        
                                        if score_match:
                                            score = float(score_match.group(1))
                                            
                                            # 保存分数和反馈
                                            session = session_service.get_session(
                                                app_name=app_name, 
                                                user_id=USER_ID, 
                                                session_id=session_id
                                            )
                                            session.state['current_score'] = score
                                            session.state['current_feedback'] = feedback
                                            session.state['is_complete'] = score >= 9.0  # 阈值从8分提高到9分（十分制）
                                            
                                            # 记录保存状态
                                            print(f"✅ 已保存分数: {score}")
                                            print(f"✅ 已保存反馈 (长度: {len(feedback)})")
                                            print(f"✅ 已设置完成状态: {session.state['is_complete']}")
                                            break
                                        else:
                                            # 没有找到确切的分数，记录问题但不设置默认值
                                            print("⚠️ 警告: 无法从LLM响应中提取评分数据")
                                            print("⚠️ 这可能表明LLM没有按照预期格式生成评分")
                else:
                    print(f">>> Text Content: {text_content}")

    # 确保至少有一个事件被处理
    if all_events and not score_text:
        # 尝试从最后几个事件中提取文本内容
        last_text = ""
        for event in reversed(all_events[-10:]):
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                text_parts = [part.text for part in event.content.parts if hasattr(part, 'text')]
                if text_parts and text_parts[0]:
                    last_text = text_parts[0]
                    break
        
        if last_text:
            session = session_service.get_session(
                app_name=app_name, 
                user_id=USER_ID, 
                session_id=session_id
            )
            # 如果没有draft内容，则设置最后的文本为draft
            if not session.state.get('current_draft') and last_text:
                session.state['current_draft'] = last_text
                session.state['iteration_count'] = 1
                print("⚠️ 警告: 自动保存最后文本为草稿，但未找到评分数据")
    
    # 必须返回整个事件列表
    return all_events


async def async_main():
    """设置ADK组件并运行扁平化写作工作流。"""
    logger.info("开始扁平化架构测试 (ADK Runner)")
    print("\n--- 开始扁平化架构测试 (ADK Runner) ---")
    
    # 1. 初始化SessionService
    session_service = InMemorySessionService()
    logger.info("Session Service初始化完成")
    print("✅ Session Service初始化完成")
    
    # 2. 创建会话并设置初始状态
    logger.info(f"设置初始数据: 材料长度={len(TEST_INITIAL_DATA[INITIAL_MATERIAL_KEY])}, "
               f"要求长度={len(TEST_INITIAL_DATA[INITIAL_REQUIREMENTS_KEY])}, "
               f"标准长度={len(TEST_INITIAL_DATA[INITIAL_SCORING_CRITERIA_KEY])}")
    print("\n初始数据 (将设置在初始会话状态中):")
    pprint(TEST_INITIAL_DATA)
    
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=TEST_INITIAL_DATA
    )
    logger.info(f"Session已创建: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
    print(f"✅ Session已创建: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'，已设置初始状态")
    
    # 3. 创建Runner
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name=APP_NAME
    )
    logger.info(f"已为Agent '{root_agent.name}'创建Runner")
    print(f"✅ 已为Agent '{root_agent.name}'创建Runner")
    
    # 4. 手动执行扁平化架构流程
    
    # 4.1 检查初始数据
    print("\n>>> 第1步: 检查初始数据")
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
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            if any(hasattr(part, 'function_call') for part in event.content.parts):
                function_call_part = next((part for part in event.content.parts if hasattr(part, 'function_call')), None)
                if function_call_part and function_call_part.function_call:
                    function_name = getattr(function_call_part.function_call, 'name', 'unknown')
                    print(f">>> 调用工具: {function_name}")
    
    # 4.2 生成初始文稿
    print("\n>>> 第2步: 生成初始文稿")
    create_draft_message = "请根据要求生成文稿。"
    
    content = types.Content()
    if content.parts is None:
        content.parts = []
    part = types.Part()
    part.text = create_draft_message
    content.parts.append(part)
    
    draft_content = None
    async for event in runner.run_async(
        new_message=content,
        user_id=USER_ID,
        session_id=SESSION_ID
    ):
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            if any(hasattr(part, 'function_call') for part in event.content.parts):
                function_call_part = next((part for part in event.content.parts if hasattr(part, 'function_call')), None)
                if function_call_part and function_call_part.function_call:
                    function_name = getattr(function_call_part.function_call, 'name', 'unknown')
                    print(f">>> 调用工具: {function_name}")
                    
                    # 如果是save_draft_result，直接保存草稿内容
                    if function_name == "save_draft_result" and hasattr(function_call_part.function_call, 'args') and function_call_part.function_call.args:
                        if hasattr(function_call_part.function_call.args, 'content'):
                            draft_content = function_call_part.function_call.args.content
                            
                            # 手动保存草稿内容
                            print(f">>> 手动保存草稿，长度: {len(draft_content)}")
                            session = session_service.get_session(
                                app_name=APP_NAME, 
                                user_id=USER_ID, 
                                session_id=SESSION_ID
                            )
                            session.state['current_draft'] = draft_content
                            session.state['iteration_count'] = 1
            
            # 直接从文本内容中尝试提取草稿
            elif any(hasattr(part, 'text') for part in event.content.parts):
                text_part = next((part for part in event.content.parts if hasattr(part, 'text')), None)
                text_content = getattr(text_part, 'text', '')
                if text_content and len(text_content) > 100:
                    print(f">>> 文本内容: {text_content[:100]}... 检测到长文本")
                    
                    # 如果还没有草稿内容，保存此文本作为草稿
                    if draft_content is None and ('人工智能' in text_content or 'AI写作' in text_content):
                        draft_content = text_content
                        print(f">>> 从LLM响应中提取草稿，长度: {len(draft_content)}")
                        
                        # 手动保存草稿内容
                        session = session_service.get_session(
                            app_name=APP_NAME, 
                            user_id=USER_ID, 
                            session_id=SESSION_ID
                        )
                        session.state['current_draft'] = draft_content
                        session.state['iteration_count'] = 1
                else:
                    print(f">>> 文本内容: {text_content}")
    
    # 4.3 评分文稿
    if draft_content:
        print("\n>>> 第3步: 评分文稿")
        score_message = "请使用score_for_parents工具对当前文稿进行评分，评分时从中等家长受众的视角出发，参考audience_profile字段中的受众画像，按照评分标准全面评估文稿质量。请确保传递文稿内容、受众画像和评分标准三个参数。"
        
        content = types.Content()
        if content.parts is None:
            content.parts = []
        part = types.Part()
        part.text = score_message
        content.parts.append(part)
        
        feedback_content = None
        score_value = None
        
        try:
            async for event in runner.run_async(
                new_message=content,
                user_id=USER_ID,
                session_id=SESSION_ID
            ):
                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                    if any(hasattr(part, 'function_call') for part in event.content.parts):
                        function_call_part = next((part for part in event.content.parts if hasattr(part, 'function_call')), None)
                        if function_call_part and function_call_part.function_call:
                            function_name = getattr(function_call_part.function_call, 'name', 'unknown')
                            print(f">>> 调用工具: {function_name}")
                            
                            # 如果是save_scoring_result，提取评分和反馈
                            if function_name == "save_scoring_result" and hasattr(function_call_part.function_call, 'args'):
                                args = function_call_part.function_call.args
                                if hasattr(args, 'score') and hasattr(args, 'feedback'):
                                    score_value = float(args.score) if args.score else None
                                    feedback_content = args.feedback if args.feedback else None
                                    
                                    # 手动保存评分和反馈
                                    if score_value is not None and feedback_content:
                                        print(f">>> 手动保存评分: {score_value}, 反馈长度: {len(feedback_content)}")
                                        session = session_service.get_session(
                                            app_name=APP_NAME, 
                                            user_id=USER_ID, 
                                            session_id=SESSION_ID
                                        )
                                        session.state['current_score'] = score_value
                                        session.state['current_feedback'] = feedback_content
                                        session.state['is_complete'] = score_value >= 9.0  # 阈值从8分提高到9分（十分制）
                    
                            # 如果是save_parents_scoring_result，提取评分结果
                            elif function_name == "save_parents_scoring_result" and hasattr(function_call_part.function_call, 'args'):
                                args = function_call_part.function_call.args
                                if hasattr(args, 'llm_output'):
                                    llm_output = args.llm_output
                                    
                                    # 从LLM输出中提取分数
                                    score_match = re.search(r'评分：(\d+)', llm_output)
                                    if score_match:
                                        score_value = float(score_match.group(1))
                                        feedback_content = llm_output
                                        
                                        # 手动保存评分和反馈
                                        print(f">>> 手动保存家长评分: {score_value}, 反馈长度: {len(feedback_content)}")
                                        session = session_service.get_session(
                                            app_name=APP_NAME, 
                                            user_id=USER_ID, 
                                            session_id=SESSION_ID
                                        )
                                        session.state['current_score'] = score_value
                                        session.state['current_feedback'] = feedback_content
                                        session.state['is_complete'] = score_value >= 90.0  # 家长评分是0-100分制，阈值从80分提高到90分
                                        
                                        # 记录保存状态
                                        print(f"✅ 已保存家长评分: {score_value}")
                                        print(f"✅ 已保存家长评价反馈 (长度: {len(feedback_content)})")
                                        print(f"✅ 已设置完成状态: {session.state['is_complete']}")
                    
                    # 从文本内容中提取评分和反馈
                    elif any(hasattr(part, 'text') for part in event.content.parts):
                        text_part = next((part for part in event.content.parts if hasattr(part, 'text')), None)
                        text_content = getattr(text_part, 'text', '')
                        
                        if text_content:
                            print(f">>> 文本内容: {text_content[:100]}...")
                            
                            # 如果还没有反馈内容且内容足够长，尝试提取评分和反馈
                            if feedback_content is None and len(text_content) > 50:
                                feedback_content = text_content
                                
                                # 尝试提取分数
                                score_match = re.search(r'(\d+(\.\d+)?)(?:/10)?分?', text_content)
                                if score_match:
                                    score_value = float(score_match.group(1))
                                    
                                    # 手动保存评分和反馈
                                    print(f">>> 从LLM响应中提取评分: {score_value}, 反馈长度: {len(feedback_content)}")
                                    session = session_service.get_session(
                                        app_name=APP_NAME, 
                                        user_id=USER_ID, 
                                        session_id=SESSION_ID
                                    )
                                    session.state['current_score'] = score_value
                                    session.state['current_feedback'] = feedback_content
                                    session.state['is_complete'] = score_value >= 9.0  # 阈值从8分提高到9分（十分制）
                                else:
                                    # 不使用默认分数，而是记录问题
                                    print("⚠️ 警告: 无法从LLM响应中提取评分数据")
                                    print("⚠️ 这可能表明LLM没有按照预期格式生成评分")
        except Exception as e:
            # 这部分原本没有匹配的try块
            logger.error(f"评分文稿过程中发生错误: {e}", exc_info=True)
            print(f"⚠️ 警告: 评分文稿过程中发生错误: {e}")
    
    # 5. 检查最终会话状态
    final_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    logger.info("获取并分析最终会话状态")
    print("\n--- 最终会话状态 (扁平化流程后) --- ")
    if final_session:
        # 打印关键状态字段，避免打印过长的内容
        state_metadata = {}
        for key, value in final_session.state.items():
            if isinstance(value, str) and len(value) > 100:
                state_metadata[key] = f"{value[:100]}... (长度: {len(value)}字符)"
            else:
                state_metadata[key] = value
        
        pprint(state_metadata)
        
        # 检查关键状态字段
        draft = final_session.state.get(CURRENT_DRAFT_KEY)
        draft_info = f"存在 (长度: {len(draft)}字符)" if draft else "缺失"
        
        score = final_session.state.get(CURRENT_SCORE_KEY)
        score_info = f"存在 ({score})" if score is not None else "缺失"
        
        feedback = final_session.state.get(CURRENT_FEEDBACK_KEY)
        feedback_info = f"存在 (长度: {len(feedback)}字符)" if feedback else "缺失"
        
        iteration = final_session.state.get(ITERATION_COUNT_KEY)
        iteration_info = f"存在 ({iteration})" if iteration is not None else "缺失"
        
        is_complete = final_session.state.get(IS_COMPLETE_KEY)
        complete_info = f"存在 ({is_complete})" if is_complete is not None else "缺失"
        
        logger.info(f"状态检查结果: draft={draft_info}, score={score_info}, "
                  f"feedback={feedback_info}, iteration={iteration_info}, "
                  f"is_complete={complete_info}")
        
        print("\n检查扁平化流程生成的键:")
        print(f"  {CURRENT_DRAFT_KEY}: {draft_info}")
        print(f"  {CURRENT_SCORE_KEY}: {score_info}")
        print(f"  {CURRENT_FEEDBACK_KEY}: {feedback_info}")
        print(f"  {ITERATION_COUNT_KEY}: {iteration_info}")
        print(f"  {IS_COMPLETE_KEY}: {complete_info}")
    else:
        logger.error("无法检索最终会话状态")
        print("错误: 无法检索最终会话状态")
    
    logger.info("扁平化架构测试已完成")
    print("\n--- 扁平化架构测试 (ADK Runner) 已完成 ---")


if __name__ == "__main__":
    asyncio.run(async_main()) 