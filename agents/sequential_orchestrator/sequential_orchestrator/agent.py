"""Root ADK Agent to orchestrate the MVP writing and scoring pipeline."""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
# --- V0.5 Imports ---
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool 
# --- End V0.5 Imports ---

# 修改点：从同级目录下的 tools 包导入
from .tools import mock_write_tool, mock_score_tool, store_initial_data, check_initial_data, save_draft
from .tools.state_tools import INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY, \
                               CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY # 假设 state_tools.py 定义了这些

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

# --- V0.5: 定义 Loop 子 Agents ---

# 检查并获取 LLM 实例，如果未配置则后续 Agent 创建会跳过
llm_instance = gpt_4o_mini_instance # 使用之前配置好的实例

# 定义 WritingAgent (修改指令, 移除 output_key, 添加 save_draft tool)
writing_agent = None
if llm_instance:
    # 先定义 save_draft_tool 以便在 WritingAgent 中使用
    save_draft_tool = FunctionTool(func=save_draft)

    writing_agent = LlmAgent(
        name="WritingAgent",
        model=llm_instance,
        instruction="""You are a writing agent focusing solely on document generation or refinement.
Your task is to produce the text for a document draft.
Examine the context provided.
- If the context indicates this is the first attempt (e.g., no previous draft or feedback is mentioned), write an initial draft based on the core material and requirements present in the context.
- If the context includes a previous draft and feedback on it, your task is to *revise* the previous draft strictly according to that feedback.
CRITICAL: After you have generated the initial draft or the revised draft, you MUST call the 'save_draft' tool and pass the complete final draft text as the 'draft' argument to save it. Do not output the draft directly in your response, only call the tool.
""",
        description="Generates an initial document draft or refines an existing one based on feedback, then saves it using the save_draft tool.", # 更新描述
        tools=[save_draft_tool], # 添加 save_draft_tool
        # output_key=CURRENT_DRAFT_KEY # 移除 output_key
    )
    print(f"✅ Sub-Agent '{writing_agent.name}' created.")
else:
    print("❌ WritingAgent creation skipped because LLM instance was not configured.")

# 定义 ScoringTool (现在只用于 ScoringAgent)
scoring_tool = FunctionTool(func=mock_score_tool)
print(f"✅ ScoringTool created (for ScoringAgent), wrapping mock_score_tool.")

# 定义 ScoringAgent (新)
scoring_agent = None
if llm_instance:
    scoring_agent = LlmAgent(
        name="ScoringAgent",
        model=llm_instance,
        instruction="Your only task is to call the 'mock_score_tool'. This tool reads the current draft and scoring criteria from the session state and writes the score and feedback back to the state.",
        description="Calls the scoring tool to evaluate the current draft.",
        tools=[scoring_tool], # <--- ScoringAgent 使用 ScoringTool
        # No output_key needed, tool writes directly to state
    )
    print(f"✅ Sub-Agent '{scoring_agent.name}' created.")
else:
    print("❌ ScoringAgent creation skipped because LLM instance was not configured.")


# 定义 LoopAgent (修改 sub_agents)
loop_agent = None
if writing_agent and scoring_agent: # 确保两个子 Agent 都已创建
    loop_agent = LoopAgent(
        name="WritingImprovementLoop",
        sub_agents=[
            writing_agent, # 第一步：写作或修改
            scoring_agent  # 第二步：调用评分工具
        ],
        max_iterations=3
    )
    print(f"✅ LoopAgent '{loop_agent.name}' created with max_iterations={loop_agent.max_iterations}.")
else:
     print("❌ LoopAgent creation skipped because sub-agents were not configured.")


# --- 定义 Entry Agent (基本不变) ---
entry_agent = None
if llm_instance and loop_agent:
    entry_agent = Agent(
        name="writing_scoring_entry_agent",
        model=llm_instance,
        description="Handles initial user interaction, checks/stores initial data, triggers the writing/scoring loop, and presents the final result.",
        instruction=(
            "You are the main entry point for the writing and scoring pipeline.\\n"
            "Follow these steps precisely:\\n"
            "1. Call the 'check_initial_data' tool to see if the required initial data is already present.\\n"
            "2. Examine the result from 'check_initial_data':\\n"
            "   - If the status is 'missing_data', ask the user to provide ALL missing information (initial_material, initial_requirements, initial_scoring_criteria) in one single message. Wait for the user's response.\\n"
            "   - After receiving the user's response, call the 'store_initial_data' tool with the provided data.\\n"
            "   - If the status was 'ready' or after 'store_initial_data' succeeds, proceed.\\n"
            "3. Announce that you are starting the iterative writing and scoring process.\\n"
            "4. Call the 'WritingImprovementLoop' agent tool. When calling it, provide an argument named 'request' with the string value 'Start the iterative process'. This tool will run the writing and scoring loop multiple times.\\n"
            "5. After the 'WritingImprovementLoop' tool finishes, retrieve the final results from the session state.\\n"
            f"6. Present the final '{CURRENT_DRAFT_KEY}', '{CURRENT_SCORE_KEY}', and '{CURRENT_FEEDBACK_KEY}' clearly to the user.\\n"
            "Report any tool errors clearly."
        ),
        tools=[
            FunctionTool(func=check_initial_data),
            FunctionTool(func=store_initial_data),
            AgentTool(agent=loop_agent)
        ],
    )
    print(f"✅ Entry Agent '{entry_agent.name}' created.")
else:
    print("❌ Entry Agent creation skipped because prerequisites (LLM or LoopAgent) were not met.")

# --- 确保导出正确的 Agent (不变) ---
root_agent = entry_agent

if not root_agent:
     print("❌❌❌ Critical Error: No root agent could be configured for export!")

# 移除旧的 Class 定义
# class SequentialAgent: ... 