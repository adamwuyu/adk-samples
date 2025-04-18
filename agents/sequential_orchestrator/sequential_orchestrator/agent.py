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
from .tools import mock_write_tool, mock_score_tool, store_initial_data, check_initial_data, save_draft, get_final_draft
# 修改点：导入新的检查工具
from .tools.state_tools import check_score_threshold_tool, LOOP_CONTROL_KEY, INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY, \
                               CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, SCORE_THRESHOLD_KEY

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
        instruction="""Your ONLY task is to generate or revise a document draft based on the context, and then save it.
Examine the context carefully:
- If no previous draft/feedback exists, write a NEW draft based on initial material/requirements.
- If a previous draft and feedback exist, REVISE the previous draft according to the feedback.

CRITICAL ACTION: After generating or revising the draft text, you MUST call the 'save_draft' tool. Pass the complete final draft text as the 'draft' argument to this tool.
ABSOLUTELY DO NOT output the draft text in your response. Your response should ONLY contain the call to the 'save_draft' tool.""",
        description="Generates or refines a draft and saves it using the save_draft tool. MUST NOT output draft text directly.",
        tools=[save_draft_tool], # 添加 save_draft_tool
        # output_key=CURRENT_DRAFT_KEY # 移除 output_key
    )
    print(f"✅ Sub-Agent '{writing_agent.name}' created.")
else:
    print("❌ WritingAgent creation skipped because LLM instance was not configured.")

# --- V0.5: 定义评分和检查 Agent (用于 Loop) ---

# 定义 Scoring Tool (会被 ScoringAgent 调用)
scoring_tool = FunctionTool(func=mock_score_tool)

# 定义 ScoringAgent (简单封装 Scoring Tool)
scoring_agent = None
if llm_instance:
    scoring_agent = LlmAgent(
        name="ScoringAgent",
        model=llm_instance,
        instruction="Your sole task is to call the 'mock_score_tool'. Do nothing else.",
        description="Calls the scoring tool to evaluate the current draft.",
        tools=[scoring_tool],
    )
    print(f"✅ Sub-Agent '{scoring_agent.name}' created.")
else:
    print("❌ ScoringAgent creation skipped because LLM instance was not configured.")

# 定义 Check Score Tool (会被 CheckScoreAgent 调用)
check_score_tool = FunctionTool(func=check_score_threshold_tool)

# 定义 CheckScoreAgent (简单封装 Check Score Tool)
check_score_agent = None
if llm_instance:
    check_score_agent = LlmAgent(
        name="CheckScoreAgent",
        model=llm_instance,
        # 指令让 LLM 调用工具。LlmAgent 会将工具返回的 "STOP" 或 None 作为自己的执行结果
        instruction="Your sole task is to call the 'check_score_threshold_tool'. Relay its exact return value.", 
        description="Calls the check score tool and relays its return value ('STOP' or None).",
        tools=[check_score_tool],
    )
    print(f"✅ Sub-Agent '{check_score_agent.name}' created.")
else:
    print("❌ CheckScoreAgent creation skipped because LLM instance was not configured.")


# 定义 LoopAgent (使用新的 Agent 列表)
loop_agent = None
# 修改点：依赖 writing_agent, scoring_agent, check_score_agent
if writing_agent and scoring_agent and check_score_agent:
    loop_agent = LoopAgent(
        name="WritingImprovementLoop",
        # 修改点：使用 Agent 列表
        sub_agents=[
            writing_agent,      # 步骤 1: 写作
            scoring_agent,     # 步骤 2: 评分
            check_score_agent  # 步骤 3: 检查是否停止
        ],
        max_iterations=3
    )
    print(f"✅ LoopAgent '{loop_agent.name}' created with max_iterations={loop_agent.max_iterations}.")
else:
     # 修改点：更新日志
     print("❌ LoopAgent creation skipped because one or more sub-agents (Writing, Scoring, CheckScore) were not configured.")


# --- 定义 Entry Agent (检查 loop_agent 存在) ---
entry_agent = None
if llm_instance and loop_agent:
    # 修改点：改回 LlmAgent，使用 instruction (string), 使用 model 参数
    entry_agent = LlmAgent(
        name="entry_agent",
        model=llm_instance, # 使用 model 参数
        description="负责接收初始数据并按顺序编排写稿和审稿流程。",
        # 修改点：合并 instructions 列表为单个 instruction 字符串
        instruction=(
            "You are the main entry point for the writing and scoring pipeline.\\n"
            "Follow these steps precisely:\\n"
            "1. Call the 'check_initial_data' tool to see if the required initial data is already present.\\n"
            "2. Examine the result from 'check_initial_data':\\n"
            "   - If the status is 'missing_data', ask the user to provide ALL missing information (initial_material, initial_requirements, initial_scoring_criteria) in one single message. Wait for the user's response.\\n"
            "   - After receiving the user's response, call the 'store_initial_data' tool with the provided data.\\n"
            "   - If the status was 'ready' or after 'store_initial_data' succeeds, proceed.\\n"
            "3. Announce that you are starting the iterative writing and scoring process.\\n"
            "4. Call the 'WritingImprovementLoop' agent tool. Pass an argument named 'request' with the value 'Start the iterative process'. This tool will execute the writing and scoring cycle multiple times.\\n"
            "5. Once the 'WritingImprovementLoop' tool finishes execution, call the `get_final_draft` tool to retrieve the final draft text produced by the loop.\\n"
            "6. Examine the response from the `get_final_draft` tool. Extract the text value associated with the key 'final_draft_text'.\\n"
            "7. Present the extracted text clearly as the final result. Start your response with 'The final draft after the improvement loop is:'."
        ),
        tools=[
            FunctionTool(func=check_initial_data),
            FunctionTool(func=store_initial_data),
            FunctionTool(func=get_final_draft),
            AgentTool(agent=loop_agent)
        ]
        # 移除 llm=... 参数，LlmAgent 使用 model=...
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