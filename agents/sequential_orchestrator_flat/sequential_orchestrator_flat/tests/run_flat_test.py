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
from sequential_orchestrator_flat import root_agent
from sequential_orchestrator_flat.tools.state_manager import (
    INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, 
    ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)
from sequential_orchestrator_flat.tools.logging_utils import setup_logging

# 配置日志
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("测试脚本启动，已配置日志系统")

# 应用和会话标识
APP_NAME = "writing_scoring_flat_app"
USER_ID = "flat_test_user"
SESSION_ID = "flat_test_session_001"

# 初始测试数据
TEST_INITIAL_DATA = {
    INITIAL_MATERIAL_KEY: "关于人工智能在创意写作中的应用的几篇文章摘要。",
    INITIAL_REQUIREMENTS_KEY: "写一篇面向普通读者的博客文章，介绍AI写作工具的优缺点。",
    INITIAL_SCORING_CRITERIA_KEY: "重点评估文章的清晰度、流畅性以及对AI优缺点的平衡论述。"
}


async def run_agent_and_get_final_response(query, runner, user_id, session_id):
    """运行Agent并获取最终响应。"""
    content = types.Content()
    if content.parts is None:
        content.parts = []
    part = types.Part()
    part.text = query
    content.parts.append(part)
    
    # 运行Agent并收集所有事件
    all_events = []
    try:
        # 逐步跟踪调用过程，并捕获事件
        tool_call_ids = set()  # 用于记录已发起的工具调用ID
        tool_response_ids = set()  # 用于记录已接收到响应的工具调用ID
        
        async for event in runner.run_async(
            new_message=content,
            user_id=user_id,
            session_id=session_id
        ):
            all_events.append(event)
            # 打印更详细的事件信息
            print(f"\n>>> 事件 #{len(all_events)}")
            print(f"事件作者: {event.author}")
            
            # 更详细地检查事件内容
            if event.content and event.content.parts:
                for part_index, part in enumerate(event.content.parts):
                    print(f"  部分 #{part_index+1}:")
                    if part.function_call:
                        tool_id = getattr(part.function_call, 'id', None)
                        if tool_id:
                            tool_call_ids.add(tool_id)
                        print(f"    工具调用: {part.function_call.name} (ID: {tool_id})")
                        print(f"    参数: {getattr(part.function_call, 'args', {})}")
                    elif part.function_response:
                        tool_id = getattr(part.function_response, 'id', None)
                        if tool_id:
                            tool_response_ids.add(tool_id)
                        resp_str = str(getattr(part.function_response, 'response', ''))
                        if len(resp_str) > 50:
                            resp_str = resp_str[:50] + "..."
                        print(f"    工具响应 (ID: {tool_id}): {resp_str}")
                    elif part.text:
                        text_preview = part.text[:100] + "..." if len(part.text) > 100 else part.text
                        print(f"    文本内容: {text_preview}")
                        print(f"    文本长度: {len(part.text)}字符")
            else:
                print("  [事件没有内容]")
        
        # 比较工具调用和响应ID，检测是否所有调用都有对应的响应
        missing_responses = tool_call_ids - tool_response_ids
        if missing_responses:
            print(f"警告: 以下工具调用ID没有收到响应: {missing_responses}")
    except Exception as e:
        print(f"运行Agent时出错: {str(e)}")
        logger.error(f"运行Agent时出错", exc_info=True)

    # 提取最后一个事件的文本响应（如果有）
    final_text_response = ""
    for event in reversed(all_events):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text_response = part.text
                    break
            if final_text_response:
                break
    
    return final_text_response


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
    
    # 4. 运行Agent
    trigger_query = "请开始写稿和评分流程。"
    logger.info(f"发送查询到Runner: '{trigger_query}'")
    print(f"\n>>> 用户查询 (发送给Runner): {trigger_query}")
    final_response = await run_agent_and_get_final_response(
        query=trigger_query,
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
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