"""Root ADK Agent to orchestrate the MVP writing and scoring pipeline."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# 修改点：从同级目录下的 tools 包导入
from .tools import mock_write_tool, mock_score_tool

# --- 加载环境变量 ---
# 注意：路径需要相对于此文件的新位置调整，向上两级再向上两级
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
# 或者更健壮的方式可能是期望 .env 在项目根目录，并尝试加载
# project_root_dotenv = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# load_dotenv(dotenv_path=os.path.join(project_root_dotenv, '.env'))
load_dotenv(dotenv_path=dotenv_path) # 保持原有逻辑，但注意路径

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
root_agent = None

# 只有在 LLM 实例成功配置后才创建 Agent
if gpt_4o_mini_instance:
    root_agent = Agent(
        name="writing_scoring_pipeline_agent_mvp",
        model=gpt_4o_mini_instance,
        description="Orchestrates the writing and scoring process sequentially. Reads initial data from session state via tools, asking the user if missing.",
        instruction=(
            "You are an orchestrator for a writing and scoring pipeline.\\n"
            "Your goal is to generate a draft based on initial material and requirements, then score it based on criteria.\\n"
            "First, check the session state for 'initial_material', 'initial_requirements', and 'initial_scoring_criteria'.\\n"
            "If any of these are missing, ask the user to provide ALL missing information in one single message. For example: 'Hello! To start the writing and scoring process, I need the initial material, the requirements for the draft, and the scoring criteria. Could you please provide them?' Wait for the user's response containing this information. Assume the user's next message contains the required information and store it in the session state under the keys 'initial_material', 'initial_requirements', and 'initial_scoring_criteria'.\\n"
            "Once you have confirmed 'initial_material', 'initial_requirements', and 'initial_scoring_criteria' are available (either from the initial state or from the user's input you stored), proceed with the following steps:\\n"
            "1. Call the 'mock_write_tool'. It will use the 'initial_material' and 'initial_requirements' from the state.\\n"
            "2. Extract the 'draft' from the result of 'mock_write_tool'. If the tool failed, report the error and stop.\\n"
            "3. Call the 'mock_score_tool', passing the 'draft' from step 2 as the argument. The tool will use the 'initial_scoring_criteria' from the state.\\n"
            "4. Extract the 'score' and 'feedback' from the result of 'mock_score_tool'. If the tool failed, report the error and stop.\\n"
            "5. Present the final 'draft' (from step 2), 'score', and 'feedback' (from step 4) clearly to the user.\\n"
            "Report any tool errors clearly."
        ),
        tools=[mock_write_tool, mock_score_tool],
    )
    print(f"✅ ADK Agent '{root_agent.name}' created.")
else:
    print("❌ ADK Agent creation skipped because LiteLlm instance was not configured.")

# 移除旧的 Class 定义
# class SequentialAgent: ... 