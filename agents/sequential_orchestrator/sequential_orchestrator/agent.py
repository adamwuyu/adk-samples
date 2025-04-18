"""Root ADK Agent to orchestrate the MVP writing and scoring pipeline."""

import os
from dotenv import load_dotenv
import logging # 添加 logging
from typing import AsyncGenerator # 添加 AsyncGenerator
from google.adk.agents import Agent
from google.adk.agents.base_agent import BaseAgent # 导入 BaseAgent
from google.adk.models.lite_llm import LiteLlm
# --- V0.5 Imports ---
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.events import Event, EventActions # 导入 Event 和 EventActions
from google.adk.agents.invocation_context import InvocationContext # 导入 InvocationContext
# from google.protobuf import struct_pb2 # 不再需要 Struct
# import google.generativeai.types as genai_types # 错误的导入

# 修改点：从同级目录下的 tools 包导入 (移除 save_draft)
from .tools import mock_write_tool, mock_score_tool, store_initial_data, check_initial_data, get_final_draft
# 修改点：导入新的检查工具
from .tools.state_tools import INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY, \
                               CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, SCORE_THRESHOLD_KEY

logger = logging.getLogger(__name__) # 设置 logger

# --- Prompt Templates ---

WRITING_AGENT_INITIAL_PROMPT_TEMPLATE = f"""You are a writing assistant tasked with writing an initial document draft.

Read the initial material from state key '{INITIAL_MATERIAL_KEY}'.
Read the initial requirements from state key '{INITIAL_REQUIREMENTS_KEY}'.

Write a NEW document draft based ONLY on this material and requirements.

Output ONLY the generated draft text.

[MATERIAL]
{{material}}

[REQUIREMENTS]
{{requirements}}

[DRAFT]"""

WRITING_AGENT_REVISION_PROMPT_TEMPLATE = f"""You are a writing assistant revising a document.
Revise the following DRAFT based *strictly* on the provided FEEDBACK.
Output ONLY the revised draft text.

--- Example Revision ---
[DRAFT]
The quick brown fox jumps. It is fast.
[FEEDBACK]
Make the second sentence more descriptive.
[REVISED DRAFT]
The quick brown fox jumps. It moves with remarkable speed.
--- End Example Revision ---

[DRAFT]
{{draft}}

[FEEDBACK]
{{feedback}}

[REVISED DRAFT]"""

SCORING_AGENT_INSTRUCTION = """Your task is to evaluate the current draft.
1. Call the 'mock_score_tool'.
2. After the tool call completes, respond with a simple confirmation message like 'OK, scoring complete.'"""

ENTRY_AGENT_INSTRUCTION = (
    "你是一个写稿和评分流程的主要入口点。\n"
    "严格按照以下步骤执行：\n\n"
    "步骤 1: 调用 'check_initial_data' 工具检查是否已经有必要的初始数据。\n"
    "工具调用示例: ```check_initial_data()```\n\n"
    "步骤 2: 检查 'check_initial_data' 工具返回的结果：\n"
    "  - 如果状态是 'missing_data'，请要求用户在一条消息中提供所有缺失的信息（initial_material、initial_requirements、initial_scoring_criteria）。等待用户回复。\n"
    "  - 收到用户回复后，调用 'store_initial_data' 工具存储提供的数据。\n"
    "  工具调用示例: ```store_initial_data(initial_material=\"用户提供的材料\", initial_requirements=\"用户提供的要求\", initial_scoring_criteria=\"用户提供的评分标准\")```\n"
    "  - 如果状态是 'ready' 或 'store_initial_data' 成功执行后，继续下一步。\n\n"
    "步骤 3: 宣布你正在开始迭代写稿和评分流程。\n\n"
    "步骤 4: 调用 'WritingImprovementLoop' 代理工具。传递名为 'request' 的参数，值为 'Start the iterative process'。\n"
    "工具调用示例: ```WritingImprovementLoop(request=\"Start the iterative process\")```\n"
    "这个工具将多次执行写稿和评分循环。\n\n"
    "步骤 5: 'WritingImprovementLoop' 工具执行完成后，调用 'get_final_draft' 工具获取循环产生的最终草稿文本。\n"
    "工具调用示例: ```get_final_draft()```\n\n"
    "步骤 6: 检查 'get_final_draft' 工具的响应。提取与键 'final_draft_text' 关联的文本值。\n\n"
    "步骤 7: 清晰地展示提取的文本作为最终结果。以 'The final draft after the improvement loop is:' 开始你的回复。\n"
    "如果最终草稿表明发生了错误（例如，以 'Error:' 开头），则报告该错误。\n"
)

# 更专门针对 Gemini 优化的指令版本
GEMINI_ENTRY_AGENT_INSTRUCTION = """
# 写稿和评分流程指南

你是一个负责协调写稿和评分流程的AI助手。请严格按照以下步骤执行任务，使用标准的函数调用格式。

## 可用工具
- check_initial_data()：检查是否有必要的初始数据
- store_initial_data(initial_material, initial_requirements, initial_scoring_criteria)：存储用户提供的数据
- WritingImprovementLoop(request)：执行写稿和评分循环
- get_final_draft()：获取最终草稿

## 工具调用格式示例
正确的函数调用格式示例：
```
check_initial_data()
```
而不是：
```tool_code
print(check_initial_data())
```
或：
```
tool_code.check_initial_data()
```

## 执行步骤

1. 检查初始数据
   ```
   check_initial_data()
   ```

2. 处理初始数据检查结果
   - 如果状态是"missing_data"：请用户提供缺失信息，然后存储数据
     ```
     store_initial_data(initial_material="...", initial_requirements="...", initial_scoring_criteria="...")
     ```
   - 如果状态是"ready"：继续下一步

3. 执行写稿和评分循环
   ```
   WritingImprovementLoop(request="Start the iterative process")
   ```

4. 获取最终草稿
   ```
   get_final_draft()
   ```

5. 展示结果
   以"The final draft after the improvement loop is:"开始你的回复，然后展示草稿内容。

务必准确使用工具调用格式，不要添加print()或其他修饰。
"""

# Reminder comment about future improvement for store_initial_data & threshold setting

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
gpt_4o_instance = None
gemini_20_pro_instance = None
gemini_25_flash_instance = None
oneapi_base_url = os.getenv("ONEAPI_BASE_URL")
oneapi_api_key = os.getenv("ONEAPI_API_KEY")
kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
kingdora_api_key = os.getenv("KINGDORA_API_KEY")

if oneapi_base_url and oneapi_api_key:
    try:
        gpt_4o_mini_instance = LiteLlm(
            model="openai/gpt-4o-mini", # 修改点：使用正确的 OpenAI 模型标识符
            api_base=oneapi_base_url,   # 修改点：使用 oneapi_base_url
            api_key=oneapi_api_key,    # 修改点：使用 oneapi_api_key
            stream=True
        )
        gpt_4o_instance = LiteLlm(
            model="openai/gpt-4o", # 修改点：使用正确的 OpenAI 模型标识符
            api_base=oneapi_base_url,   # 修改点：使用 oneapi_base_url
            api_key=oneapi_api_key,    # 修改点：使用 oneapi_api_key
            stream=True
        )
        gemini_20_pro_instance = LiteLlm(
            model="openai/gemini-2.0-pro-exp-02-05", # 修改点：使用正确的 OpenAI 模型标识符
            api_base=kingdora_base_url,   # 修改点：使用 oneapi_base_url
            api_key=kingdora_api_key,    # 修改点：使用 oneapi_api_key
            stream=True,
        )
        gemini_25_flash_instance = LiteLlm(
            model="openai/gemini-2.5-flash-preview-04-17", # 修改点：使用正确的 OpenAI 模型标识符
            api_base=kingdora_base_url,   # 修改点：使用 oneapi_base_url
            api_key=kingdora_api_key,    # 修改点：使用 oneapi_api_key
            stream=True,
            temperature=0.2,  # 降低温度以减少创造性，提高工具调用准确性
            tool_choice="auto"  # 显式启用工具选择
        )
        print(f"✅ LiteLlm instance for openai/gpt-4o-mini (via OneAPI) configured.") # 修改点：更新日志信息
    except Exception as e:
        print(f"❌ Error configuring LiteLlm via OneAPI: {e}") # 修改点：更新错误日志
else:
    # 修改点：修正 else 块的日志信息，使其检查并报告 OneAPI 变量缺失
    print("❌ ONEAPI_BASE_URL or ONEAPI_API_KEY not found in environment variables. Cannot configure LiteLlm.")

# --- V0.5: 定义 Loop 子 Agents ---

# 检查并获取 LLM 实例，如果未配置则后续 Agent 创建会跳过
llm_instance = gpt_4o_instance  # 使用 Gemini 2.0 Pro 模型

# --- 新增：定义自定义 Writing Agent ---
class CustomWritingAgent(BaseAgent):
    """A custom agent that explicitly fetches state and constructs the prompt for writing/revising."""
    # 不再需要 llm 实例
    # llm: LiteLlm 

    # __init__ 不再需要 model
    # def __init__(self, name: str, model: LiteLlm):
    #     super().__init__(name=name, llm=model)
    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        material = state.get(INITIAL_MATERIAL_KEY, "")
        requirements = state.get(INITIAL_REQUIREMENTS_KEY, "")
        draft = state.get(CURRENT_DRAFT_KEY)
        feedback = state.get(CURRENT_FEEDBACK_KEY)
        prompt_text = ""

        logger.info(f"[{self.name}] Running. Checking for draft/feedback.")

        if draft and feedback:
            logger.info(f"[{self.name}] Found existing draft and feedback. Constructing revision prompt.")
            prompt_text = WRITING_AGENT_REVISION_PROMPT_TEMPLATE.format(draft=draft, feedback=feedback)
        elif material and requirements:
            logger.info(f"[{self.name}] No draft/feedback found. Constructing initial writing prompt.")
            prompt_text = WRITING_AGENT_INITIAL_PROMPT_TEMPLATE.format(material=material, requirements=requirements)
        else:
            logger.error(f"[{self.name}] Cannot construct prompt. Missing initial data or draft/feedback.")
            # 将错误信息也放入 prompt state，以便后续 Agent 知道出错了
            ctx.session.state["current_prompt_text"] = "Error: Cannot construct prompt due to missing data."
            yield Event(author=self.name, content={'parts': [{'text': "Error: Missing data for prompt construction."}]})
            return

        # 将构建好的 prompt 保存到 state
        ctx.session.state["current_prompt_text"] = prompt_text
        logger.info(f"[{self.name}] Prompt constructed and saved to state key 'current_prompt_text'. Prompt: {prompt_text[:100]}...")
        
        # 产生一个简单的完成事件
        yield Event(author=self.name, content={'parts': [{'text': "Prompt constructed successfully."}]})

# --- 新增：ExecutePromptAgent (LlmAgent) --- 
execute_prompt_agent = None
if llm_instance:
    execute_prompt_agent = LlmAgent(
        name="ExecutePromptAgent",
        model=llm_instance,
        # 指令很简单：执行 state 中的 prompt
        instruction="Execute the prompt found in the session state key 'current_prompt_text'. Output only the result.",
        # 输出保存到 current_draft
        output_key=CURRENT_DRAFT_KEY,
        description="Executes the prompt prepared by CustomWritingAgent."
    )
    print(f"✅ Sub-Agent '{execute_prompt_agent.name}' created.")
else:
    print("❌ ExecutePromptAgent creation skipped because LLM instance was not configured.")

# --- 实例化 CustomWritingAgent (移除 model) --- 
writing_agent = CustomWritingAgent(name="WritingAgent") # 不再需要 model
print(f"✅ Custom Agent '{writing_agent.name}' (Prompt Constructor) created.")

# --- Define CustomScoringAgent --- 
class CustomScoringAgent(BaseAgent):
    """A custom agent that deterministically calls the mock_score_tool."""
    tool: FunctionTool

    def __init__(self, name: str, tool_to_call: FunctionTool):
        super().__init__(name=name, tool=tool_to_call)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Attempting to call tool: {self.tool.func.__name__}")
        try:
            # --- 修改：使用 ADK 标准的 Tool 调用方式 ---
            # 创建 ToolContext 实例并正确传递
            tool_ctx = ToolContext(invocation_context=ctx)
            
            # 调用 Tool 函数，传递空的参数字典和 tool_context
            tool_result = await self.tool.run_async(args={}, tool_context=tool_ctx)
            
            # 无需手动更新状态，Tool 函数自己负责更新状态
            # 只需打印日志确认
            if tool_result:
                logger.info(f"[{self.name}] Tool call successful. Result: {tool_result}")
                # 可以检查一下状态是否已更新（仅调试用）
                if ctx.session and ctx.session.state:
                    score = ctx.session.state.get(CURRENT_SCORE_KEY)
                    feedback_len = len(ctx.session.state.get(CURRENT_FEEDBACK_KEY, ""))
                    logger.info(f"[{self.name}] State after tool call: score={score}, feedback_length={feedback_len}")
            else:
                logger.warning(f"[{self.name}] Tool call returned None or empty result")
            
            yield Event(
                author=self.name,
                content={'parts': [{'text': f'Tool {self.tool.func.__name__} executed.'}]}
            )
        except Exception as e:
            logger.error(f"[{self.name}] Error calling tool {self.tool.func.__name__}: {e}", exc_info=True)
            yield Event(
                author=self.name,
                content={'parts': [{'text': f'Error calling tool {self.tool.func.__name__}: {e}'}]}
            )

# --- 实例化 Scoring Tool and CustomScoringAgent --- 
scoring_tool = FunctionTool(func=mock_score_tool)
scoring_agent = None
if llm_instance: # 保持检查以防未来此 Agent 需要 LLM
    scoring_agent = CustomScoringAgent(name="ScoringAgent", tool_to_call=scoring_tool)
    print(f"✅ Custom Agent '{scoring_agent.name}' created, wrapping tool '{scoring_tool.func.__name__}'.")
else:
     print("❌ ScoringAgent (Custom) creation skipped due to missing LLM instance check.")

# --- 新增：定义自定义检查 Agent --- 
class CheckScoreAndEscalateAgent(BaseAgent):
    """A custom agent that checks the score against a threshold and escalates if met."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Checks state and yields an event, escalating if score >= threshold."""
        state = ctx.session.state # Correct access via session
        score = state.get(CURRENT_SCORE_KEY)
        threshold = state.get(SCORE_THRESHOLD_KEY)
        should_escalate = False # Default to not escalate

        logger.info(f"[{self.name}] Checking score threshold: Score={score}, Threshold={threshold}")
        logger.info(f"[{self.name}] Current state keys: {list(state.keys())}")
        logger.info(f"[{self.name}] Current state draft: {state.get(CURRENT_DRAFT_KEY, 'None')[:30]}...")

        # 尝试手动设置 score 和 feedback（用于测试）
        if score is None:
            test_score = 7.5
            logger.info(f"[{self.name}] Manually setting test score: {test_score}")
            state[CURRENT_SCORE_KEY] = test_score
            score = state.get(CURRENT_SCORE_KEY)
            logger.info(f"[{self.name}] After manual set, score={score}")
            
        if not CURRENT_FEEDBACK_KEY in state:
            test_feedback = "测试反馈"
            logger.info(f"[{self.name}] Manually setting test feedback")
            state[CURRENT_FEEDBACK_KEY] = test_feedback
            logger.info(f"[{self.name}] After manual set, feedback exists: {CURRENT_FEEDBACK_KEY in state}")
            
        # 确保更新会保存到最终的会话状态中
        # 这是为了解决可能的状态同步问题
        root_state = ctx.session.state
        if score is not None and not CURRENT_SCORE_KEY in root_state:
            logger.info(f"[{self.name}] Ensuring score is saved to root state: {score}")
            root_state[CURRENT_SCORE_KEY] = score
            
        feedback = state.get(CURRENT_FEEDBACK_KEY)
        if feedback and not CURRENT_FEEDBACK_KEY in root_state:
            logger.info(f"[{self.name}] Ensuring feedback is saved to root state")
            root_state[CURRENT_FEEDBACK_KEY] = feedback

        if score is None or threshold is None:
            logger.warning(
                f"[{self.name}] Cannot check score threshold: Score ('{CURRENT_SCORE_KEY}': {score}) or "
                f"Threshold ('{SCORE_THRESHOLD_KEY}': {threshold}) not found or is None in state. Loop will continue."
            )
        else:
            try:
                score_f = float(score)
                threshold_f = float(threshold)
                if score_f >= threshold_f:
                    logger.info(f"[{self.name}] Score ({score_f}) meets or exceeds threshold ({threshold_f}). Escalating to stop loop.")
                    should_escalate = True
                else:
                    logger.info(f"[{self.name}] Score ({score_f}) is below threshold ({threshold_f}). Loop will continue.")
            except (ValueError, TypeError) as e:
                logger.error(
                    f"[{self.name}] Error converting score/threshold to float: Score={score}, Threshold={threshold}. Error: {e}. Loop will continue."
                )

        # Yield an event, setting escalate=True if the condition was met
        yield Event(author=self.name, actions=EventActions(escalate=should_escalate))

# 实例化自定义 Agent
check_and_escalate_agent = CheckScoreAndEscalateAgent(name="CheckScoreAndEscalateAgent")
print(f"✅ Custom Agent '{check_and_escalate_agent.name}' created.")

# --- LoopAgent - 更新 sub_agents 列表 ---
loop_agent = None
# 修改点：添加 execute_prompt_agent 依赖
if writing_agent and execute_prompt_agent and scoring_agent and check_and_escalate_agent:
    loop_agent = LoopAgent(
        name="WritingImprovementLoop",
        # 修改点：更新步骤顺序
        sub_agents=[
            writing_agent,          # 1. 构建 Prompt (Custom)
            execute_prompt_agent,   # 2. 执行 Prompt (LlmAgent)
            scoring_agent,          # 3. 评分 (Custom)
            check_and_escalate_agent# 4. 检查并升级 (Custom)
        ],
        max_iterations=3
    )
    print(f"✅ LoopAgent '{loop_agent.name}' created with max_iterations={loop_agent.max_iterations}.")
else:
     # 修改点：更新日志
     print("❌ LoopAgent creation skipped because one or more sub-agents were not configured.")

# --- 定义 Entry Agent (检查 loop_agent 存在) ---
entry_agent = None
if llm_instance and loop_agent:
    # 根据模型类型选择合适的指令
    if llm_instance == gemini_25_flash_instance:
        print("✅ 使用针对 Gemini 优化的指令模板")
        instruction = GEMINI_ENTRY_AGENT_INSTRUCTION
    else:
        print("✅ 使用标准指令模板")
        instruction = ENTRY_AGENT_INSTRUCTION
        
    entry_agent = LlmAgent(
        name="entry_agent",
        model=llm_instance,
        description="负责接收初始数据并按顺序编排写稿和审稿流程。",
        instruction=instruction,
        tools=[
            FunctionTool(func=check_initial_data),
            FunctionTool(func=store_initial_data),
            FunctionTool(func=get_final_draft),
            AgentTool(agent=loop_agent)
        ]
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