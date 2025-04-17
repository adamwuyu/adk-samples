"""Root ADK Agent to orchestrate the MVP writing and scoring pipeline."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

# 修改点：从同级目录下的 tools 包导入
from .tools import mock_write_tool, mock_score_tool, store_initial_data, check_initial_data
from .tools.state_tools import INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY

# --- 加载环境变量 ---
# 修改点：确保加载 agents/ 目录下的 .env 文件
# 计算 agent.py 文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 推算 agents 目录的路径 (向上两级)
agents_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
# 拼接 .env 文件路径
dotenv_path = os.path.join(agents_dir, '.env')

# 加载 .env 文件，如果存在
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    # print(f"agent.py: Loaded .env from {dotenv_path}") # 可选：添加日志确认
else:
    print(f"agent.py: Warning - .env file not found at {dotenv_path}. Relying on environment variables or other dotenv loads.")
    # 如果找不到，尝试默认加载，以防变量已在环境中设置
    load_dotenv()

# --- 配置 LLM 实例 ---
# 使用 gpt-4o-mini 作为示例，确保 .env 文件中有对应的 ONEAPI 配置
gpt_4o_mini_instance = None
oneapi_base_url = os.getenv("ONEAPI_BASE_URL")
oneapi_api_key = os.getenv("ONEAPI_API_KEY")

if oneapi_base_url and oneapi_api_key:
    try:
        gpt_4o_mini_instance = LiteLlm(
            model="openai/gpt-4o-mini", # 修改点：使用正确的 OpenAI 模型标识符
            api_base=oneapi_base_url,   # 修改点：使用 oneapi_base_url
            api_key=oneapi_api_key,    # 修改点：使用 oneapi_api_key
            stream=True
        )
        print(f"✅ LiteLlm instance for openai/gpt-4o-mini (via OneAPI) configured.") # 修改点：更新日志信息
    except Exception as e:
        print(f"❌ Error configuring LiteLlm via OneAPI: {e}") # 修改点：更新错误日志
else:
    # 修改点：修正 else 块的日志信息，使其检查并报告 OneAPI 变量缺失
    print("❌ ONEAPI_BASE_URL or ONEAPI_API_KEY not found in environment variables. Cannot configure LiteLlm.")

# --- 定义 Root Agent (使用 check_initial_data Tool) ---
root_agent = None

if gpt_4o_mini_instance:
    root_agent = Agent(
        name="writing_scoring_pipeline_agent_mvp",
        model=gpt_4o_mini_instance,
        description="Orchestrates the writing and scoring process sequentially. Uses tools to check for and store initial data if missing.",
        instruction=(
            "You are an orchestrator for a writing and scoring pipeline.\\n"
            "Your goal is to generate a draft based on initial material and requirements, then score it based on criteria.\\n"
            "Follow these steps precisely:\\n"
            "1. Call the 'check_initial_data' tool to see if the required data (initial_material, initial_requirements, initial_scoring_criteria) is already present in the session state.\\n"
            "2. Examine the result from 'check_initial_data':\\n"
            "   - If the status is 'missing_data', ask the user to provide ALL missing information in one single message. For example: 'Hello! To start the writing and scoring process, I need the initial material, the requirements for the draft, and the scoring criteria. Could you please provide them?' Wait for the user's response.\\n"
            "   - After receiving the user's response containing the data, call the 'store_initial_data' tool, passing the user-provided initial_material, initial_requirements, and initial_scoring_criteria as arguments to the tool.\\n"
            "   - If the status from 'check_initial_data' was 'ready', or after 'store_initial_data' has been successfully called, proceed to the next step.\\n"
            "3. Call the 'mock_write_tool'. It will use the data now guaranteed to be in the state.\\n"
            "4. Extract the 'draft' from the result of 'mock_write_tool'. If the tool failed, report the error and stop.\\n"
            "5. Call the 'mock_score_tool', passing the 'draft' from step 4 as the argument. It will use the state data.\\n"
            "6. Extract the 'score' and 'feedback' from the result of 'mock_score_tool'. If the tool failed, report the error and stop.\\n"
            "7. Present the final 'draft' (from step 4), 'score', and 'feedback' (from step 6) clearly to the user.\\n"
            "Report any tool errors clearly."
        ),
        # 使用 FunctionTool 包装所有 Tools, 添加 check_initial_data
        tools=[
            FunctionTool(func=check_initial_data),
            FunctionTool(func=store_initial_data),
            FunctionTool(func=mock_write_tool),
            FunctionTool(func=mock_score_tool),
        ],
    )
    print(f"✅ ADK Agent '{root_agent.name}' created.")
else:
    print("❌ ADK Agent creation skipped because LiteLlm instance was not configured.")

# 移除旧的 Class 定义
# class SequentialAgent: ... 