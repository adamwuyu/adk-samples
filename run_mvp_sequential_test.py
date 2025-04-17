"""Integration test script for the MVP SequentialAgent flow using ADK Runner."""

import sys
import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv

# --- ADK Imports (模仿教程) ---
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
# 确保 agents 目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# --- 从我们创建的模块中导入 Agent ---
# agent.py 中定义了 writing_scoring_pipeline_agent 实例
from agents.sequential_orchestrator import writing_scoring_pipeline_agent

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
    """Sets up ADK components and runs the MVP sequential workflow."""
    print("--- Starting MVP Sequential Workflow Test (ADK Runner) ---")

    # 检查 Agent 是否已成功创建 (在 sequential_orchestrator/agent.py 中)
    if not writing_scoring_pipeline_agent:
        print("❌ Error: writing_scoring_pipeline_agent is not defined or failed to initialize.")
        print("   Please check agents/sequential_orchestrator/agent.py and ensure LLM is configured.")
        return

    # 1. 初始化 Session Service (模仿教程)
    session_service = InMemorySessionService()
    print(f"✅ Session Service initialized.")

    # 2. 准备初始 State 数据 (对应 Agent 指令中的要求)
    initial_state = {
        "initial_material": "关于人工智能在创意写作中的应用的几篇文章摘要。",
        "initial_requirements": "写一篇面向普通读者的博客文章，介绍 AI 写作工具的优缺点。",
        "initial_scoring_criteria": "重点评估文章的清晰度、流畅性以及对 AI 优缺点的平衡论述。"
    }
    print("\nInput Data (to be set in initial session state):")
    pprint(initial_state)

    # 3. 创建 Session 并设置初始 State (模仿教程)
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initial_state # <<< 设置初始状态
    )
    print(f"\n✅ Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}' with initial state.")

    # 4. 初始化 Runner (模仿教程)
    runner = Runner(
        agent=writing_scoring_pipeline_agent, # 使用我们导入的 Agent 实例
        app_name=APP_NAME,
        session_service=session_service
    )
    print(f"✅ Runner created for agent '{runner.agent.name}'.")

    # 5. 运行 Agent (发送一个简单的触发消息)
    # Agent 的指令要求它从 state 中提取数据并执行流程
    trigger_query = "请开始写稿和评分流程。"
    final_response = await run_agent_and_get_final_response(
        query=trigger_query,
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # 6. (可选) 检查最终 Session State
    final_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("\n--- Final Session State --- ")
    if final_session:
        pprint(final_session.state)
    else:
        print("Error: Could not retrieve final session state.")

    print("\n--- MVP Sequential Workflow Test (ADK Runner) Finished ---")

# --- 脚本入口 (模仿教程) ---
if __name__ == "__main__":
    # 确保 .env 文件已加载 (agent.py 中应该已经加载，但这里再次确保)
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
      load_dotenv(dotenv_path=dotenv_path)
    else:
      # 尝试加载默认的 .env 文件
      load_dotenv()
      print("Loaded default .env, ensure necessary variables (e.g., ONEAPI_...) are present.")

    # 运行主异步函数
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"\n❌ An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

# 移除旧的同步 main 函数
# def main(): ... 