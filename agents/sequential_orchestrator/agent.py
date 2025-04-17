"""Root ADK Agent to orchestrate the MVP writing and scoring pipeline."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# 导入我们定义的 Mock Tools (它们现在内部访问 state)
# 假设此文件在 agents/sequential_orchestrator/ 中
from ..writing_scoring_mocks import mock_write_tool, mock_score_tool

# --- 加载环境变量 ---
# 假设 .env 文件在项目根目录，即此文件向上两级
# .env 文件路径可能需要根据实际项目结构调整
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
# 也可以直接加载默认的 .env
# load_dotenv()

# --- 配置 LLM 实例 ---
# 使用 gpt-4o-mini 作为示例，确保 .env 文件中有对应的 ONEAPI 配置
gpt_4o_mini_instance = None
oneapi_base_url = os.getenv("ONEAPI_BASE_URL")
oneapi_api_key = os.getenv("ONEAPI_API_KEY")

if oneapi_base_url and oneapi_api_key:
    try:
        gpt_4o_mini_instance = LiteLlm(
            model="openai/gemini-2.0-pro-exp-02-05", # 使用你之前选择的 Gemini 模型
            api_base=os.getenv("GOOGLE_BASE_URL"),   # 对应修改 Base URL
            api_key=os.getenv("GOOGLE_API_KEY"),    # 对应修改 API Key
            stream=True
        )
        print(f"✅ LiteLlm instance for Gemini Pro configured.") # 更新打印信息
    except Exception as e:
        print(f"❌ Error configuring LiteLlm: {e}")
else:
    print("❌ GOOGLE_BASE_URL or GOOGLE_API_KEY not found in environment variables. Cannot configure LiteLlm.") # 更新打印信息

# --- 定义 Root Agent (简化指令) ---
writing_scoring_pipeline_agent = None

# 只有在 LLM 实例成功配置后才创建 Agent
if gpt_4o_mini_instance:
    writing_scoring_pipeline_agent = Agent(
        name="writing_scoring_pipeline_agent_mvp",
        model=gpt_4o_mini_instance,
        description="Orchestrates the writing and scoring process sequentially. Reads initial data from session state via tools.",
        instruction=(
            "You are an orchestrator for a writing and scoring pipeline.\n"
            "The necessary initial inputs are stored in session state and the tools will access them.\n"
            "Follow these steps strictly:\n"
            "1. Call the 'mock_write_tool'. It will use the material and requirements from the state.\n"
            "2. Extract the 'draft' from the result of 'mock_write_tool'. If the tool failed, report the error and stop.\n"
            "3. Call the 'mock_score_tool', passing the 'draft' from step 2 as the argument. The tool will use the scoring criteria from the state.\n"
            "4. Extract the 'score' and 'feedback' from the result of 'mock_score_tool'. If the tool failed, report the error and stop.\n"
            "5. Present the final 'draft' (from step 2), 'score', and 'feedback' (from step 4) clearly to the user.\n"
            "Report any tool errors clearly. DO NOT ask the user for input data."
        ),
        tools=[mock_write_tool, mock_score_tool],
    )
    print(f"✅ ADK Agent '{writing_scoring_pipeline_agent.name}' created.")
else:
    print("❌ ADK Agent creation skipped because LiteLlm instance was not configured.")

# 移除旧的 Class 定义
# class SequentialAgent: ... 