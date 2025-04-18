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
from pprint import pprint

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 将项目根目录添加到sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    print(f"Added project root to sys.path: {PROJECT_ROOT}")

# 导入Agent
from sequential_orchestrator_flat import root_agent
from sequential_orchestrator_flat.tools.state_tools import (
    INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, 
    ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    async for event in runner.run_async(
        new_message=content,
        user_id=user_id,
        session_id=session_id
    ):
        all_events.append(event)
        # 打印事件信息以便调试
        print(f"Event author: {event.author}")
        
        # 检查是否有函数调用
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    print(f">>> Tool Call: {part.function_call.name}")
                elif part.function_response:
                    print(f">>> Tool Response received")
                elif part.text:
                    print(f">>> Text Content: {part.text[:100]}...")

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
    print("\n--- 开始扁平化架构测试 (ADK Runner) ---")
    
    # 1. 初始化SessionService
    session_service = InMemorySessionService()
    print("✅ Session Service初始化完成")
    
    # 2. 创建会话并设置初始状态
    print("\n初始数据 (将设置在初始会话状态中):")
    pprint(TEST_INITIAL_DATA)
    
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=TEST_INITIAL_DATA
    )
    print(f"✅ Session已创建: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'，已设置初始状态")
    
    # 3. 创建Runner
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name=APP_NAME
    )
    print(f"✅ 已为Agent '{root_agent.name}'创建Runner")
    
    # 4. 运行Agent
    trigger_query = "请开始写稿和评分流程。"
    print(f"\n>>> 用户查询 (发送给Runner): {trigger_query}")
    final_response = await run_agent_and_get_final_response(
        query=trigger_query,
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    # 5. 检查最终会话状态
    final_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("\n--- 最终会话状态 (扁平化流程后) --- ")
    if final_session:
        pprint(final_session.state)
        
        # 检查关键状态字段
        print("\n检查扁平化流程生成的键:")
        print(f"  {CURRENT_DRAFT_KEY}: {'存在' if final_session.state.get(CURRENT_DRAFT_KEY) else '缺失'}")
        print(f"  {CURRENT_SCORE_KEY}: {'存在' if final_session.state.get(CURRENT_SCORE_KEY) is not None else '缺失'}")
        print(f"  {CURRENT_FEEDBACK_KEY}: {'存在' if final_session.state.get(CURRENT_FEEDBACK_KEY) else '缺失'}")
        print(f"  {ITERATION_COUNT_KEY}: {'存在 (' + str(final_session.state.get(ITERATION_COUNT_KEY)) + ')' if final_session.state.get(ITERATION_COUNT_KEY) is not None else '缺失'}")
        print(f"  {IS_COMPLETE_KEY}: {'存在 (' + str(final_session.state.get(IS_COMPLETE_KEY)) + ')' if final_session.state.get(IS_COMPLETE_KEY) is not None else '缺失'}")
    else:
        print("错误: 无法检索最终会话状态")
    
    print("\n--- 扁平化架构测试 (ADK Runner) 已完成 ---")


if __name__ == "__main__":
    asyncio.run(async_main()) 