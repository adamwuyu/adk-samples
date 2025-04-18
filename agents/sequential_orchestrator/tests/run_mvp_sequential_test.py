"""Integration test script for the Looping Writing/Scoring flow using ADK Runner."""

import sys
import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
import json
import logging

# --- ADK Imports (模仿教程) ---
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts

# 修改点：确保 agents 目录在 Python 路径中
# 获取脚本当前目录 agents/sequential_orchestrator/tests/
current_dir_for_path = os.path.dirname(os.path.abspath(__file__))
# 计算项目根目录 (向上三级)
project_root_for_path = os.path.abspath(os.path.join(current_dir_for_path, '..', '..', '..'))
# 将项目根目录添加到 sys.path，以便能找到顶层的 'agents' 包
sys.path.insert(0, project_root_for_path)
print(f"Added project root to sys.path: {project_root_for_path}") # 确认路径

# --- 从我们创建的模块中导入 Agent ---
# root_agent 现在指向 entry_agent，这是正确的入口点
from agents.sequential_orchestrator import root_agent
from agents.sequential_orchestrator.sequential_orchestrator.tools.state_tools import SCORE_THRESHOLD_KEY


# --- 定义 App 常量 (模仿教程) ---
APP_NAME = "writing_scoring_mvp_app"
USER_ID = "mvp_user_1"
SESSION_ID = "mvp_session_001"

# --- 定义入口函数 (模仿教程的 call_agent_async) ---
async def run_agent_and_get_final_response(query: str, runner: Runner, user_id: str, session_id: str) -> str:
    """Sends a query to the agent via the runner and returns the final text response."""
    print(f"\n>>> User Query (sent to runner): {query}")

    # 准备用户消息 (即使主要输入在 state 中，也需要一个触发消息)
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final text response." # Default
    full_final_event = None # Store the full final event for inspection

    # Key Concept: run_async executes the agent logic and yields Events.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # 打印所有事件以进行调试
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}")
        # print(f"  Content: {event.content}")
        # print(f"  Actions: {event.actions}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            full_final_event = event # Save the event
            if event.content and event.content.parts:
                # 假设文本响应在第一个 part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break # Stop processing events once the final response is found

    print(f"<<< Agent Final Text Response: {final_response_text}")
    # print("\n--- Full Final Event ---")
    # pprint(full_final_event)
    # print("------------------------")
    return final_response_text

# --- 主异步函数 (模仿教程的 async_main) ---
async def async_main():
    """Sets up ADK components and runs the Looping workflow via entry_agent."""
    print("--- Starting Looping Workflow Test (ADK Runner) ---")

    # 检查 Agent 是否已成功创建 (现在是 entry_agent)
    if not root_agent:
        print("❌ Error: root_agent (entry_agent) is not defined or failed to initialize.")
        print("   Please check agents/sequential_orchestrator/sequential_orchestrator/agent.py and ensure LLM and LoopAgent are configured.")
        return

    # 1. 初始化 Session Service (不变)
    session_service = InMemorySessionService()
    print(f"✅ Session Service initialized.")

    # 2. 准备初始 State 数据 (不变)
    initial_state = {
        "initial_material": "关于人工智能在创意写作中的应用的几篇文章摘要。",
        "initial_requirements": "写一篇面向普通读者的博客文章，介绍 AI 写作工具的优缺点。",
        "initial_scoring_criteria": "重点评估文章的清晰度、流畅性以及对 AI 优缺点的平衡论述。",
        SCORE_THRESHOLD_KEY: 8.5
        # V0.5: 不需要预设 current_draft 等，因为 entry_agent 会处理
    }
    print("\nInput Data (to be set in initial session state):")
    pprint(initial_state)

    # 3. 创建 Session 并设置初始 State (不变)
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initial_state # <<< 设置初始状态
    )
    print(f"\n✅ Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}' with initial state.")

    # 4. 初始化 Runner (使用 entry_agent, 不变)
    runner = Runner(
        agent=root_agent, # 使用导入的入口 Agent 实例
        app_name=APP_NAME,
        session_service=session_service
    )
    print(f"✅ Runner created for agent '{runner.agent.name}'.")

    # 5. 运行 Agent (发送一个简单的触发消息, 不变)
    # entry_agent 内部会调用 check_initial_data, 发现数据存在，然后调用 LoopAgent
    trigger_query = "请开始写稿和评分流程。"
    final_response = await run_agent_and_get_final_response(
        query=trigger_query,
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # 6. 检查最终 Session State (关键验证点)
    final_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("\n--- Final Session State (After Loop) --- ")
    if final_session:
        pprint(final_session.state)
        # 检查循环后产生的 key 是否存在
        print("\nChecking keys generated by the loop:")
        from agents.sequential_orchestrator.sequential_orchestrator.tools.state_tools import CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY
        draft_final = final_session.state.get(CURRENT_DRAFT_KEY)
        score_final = final_session.state.get(CURRENT_SCORE_KEY)
        feedback_final = final_session.state.get(CURRENT_FEEDBACK_KEY)
        print(f"  {CURRENT_DRAFT_KEY}: {'Present' if draft_final else 'Missing'}")
        print(f"  {CURRENT_SCORE_KEY}: {'Present' if score_final is not None else 'Missing'}") # Score可以是0
        print(f"  {CURRENT_FEEDBACK_KEY}: {'Present' if feedback_final else 'Missing'}")
    else:
        print("Error: Could not retrieve final session state.")

    print("\n--- Looping Workflow Test (ADK Runner) Finished ---")

# --- 脚本入口 (模仿教程) ---
if __name__ == "__main__":
    # 修改点：确保 .env 文件已加载
    # 获取脚本当前目录 agents/sequential_orchestrator/tests/
    current_dir_for_dotenv = os.path.dirname(os.path.abspath(__file__))
    # 计算 .env 文件路径 (向上两级到 agents/ 目录)
    dotenv_path = os.path.abspath(os.path.join(current_dir_for_dotenv, '..', '..', '.env'))

    if os.path.exists(dotenv_path):
      load_dotenv(dotenv_path=dotenv_path)
      print(f"Loaded .env file from: {dotenv_path}") # 添加日志确认
    else:
      # 如果 agents/.env 不存在，尝试加载默认的
      print(f"Warning: Did not find .env file at {dotenv_path}. Trying default load_dotenv().")
      load_dotenv()

    # 运行主异步函数
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"\n❌ An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

# 移除旧的同步 main 函数
# def main(): ... 