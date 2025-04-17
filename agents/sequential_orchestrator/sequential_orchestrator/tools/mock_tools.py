"""Mock Tools for MVP testing, following ADK patterns and accessing state internally."""

from typing import Any, Dict, Optional
from google.adk.tools.tool_context import ToolContext # Import ToolContext
from .state_tools import CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, INITIAL_SCORING_CRITERIA_KEY # 导入 State Keys

# 定义与 docs/Agent间通信数据结构.md 类似（但不完全相同）的上下文类型别名
PipelineContext = Dict[str, Any]

# 修改 Tool 定义，使其从 ToolContext 获取输入
def mock_write_tool(tool_context: ToolContext) -> Dict[str, Any]: # 主要参数变为 tool_context
    """
    Simulates a writing process. Retrieves material and requirements from session state
    via tool_context. Returns a dictionary containing the generated draft.

    Expected State Keys:
        initial_material (str): The source material for writing.
        initial_requirements (str): The writing requirements.

    Args:
        tool_context (ToolContext): Provides access to session state.

    Returns:
        dict: Contains 'status' ('success' or 'error') and 'draft'.
    """
    agent_name = tool_context.agent_name if tool_context else "Unknown Agent"
    print(f"--- Tool: mock_write_tool invoked by {agent_name} ---")

    # --- 从 State 读取输入 ---
    material = tool_context.state.get('initial_material', '') # 从 state 获取
    requirements = tool_context.state.get('initial_requirements', '') # 从 state 获取

    if not material or not requirements:
        print("--- Tool: Error - Missing 'initial_material' or 'initial_requirements' in session state. ---")
        return {"status": "error", "draft": "Error: Missing initial material or requirements in state."} 

    print(f"--- Tool: Read from state - material: {material[:50]}...")
    print(f"--- Tool: Read from state - requirements: {requirements[:50]}...")

    # Simulate writing process
    mock_draft = f"这是基于要求 '{requirements[:20]}...' (从state读取) 生成的模拟文稿。"
    print(f"--- Tool: Generated draft: {mock_draft} ---")

    # Tools should return results
    return {"status": "success", "draft": mock_draft}

# 修改 Tool 定义，使其从 ToolContext 获取输入 (draft 来自上一步结果，criteria 来自 state)
def mock_score_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Simulates scoring a given draft retrieved from session state.
    Retrieves scoring criteria from session state via tool_context.
    Writes the score and feedback back to session state.
    Returns a dictionary containing the status, score, and feedback for logging/confirmation.

    Expected State Keys (Input):
        CURRENT_DRAFT_KEY (str): The draft text to be scored.
        INITIAL_SCORING_CRITERIA_KEY (str): The scoring criteria.
    State Keys (Output):
        CURRENT_SCORE_KEY (float): The calculated score.
        CURRENT_FEEDBACK_KEY (str): The generated feedback.

    Args:
        tool_context (ToolContext): Provides access to session state.

    Returns:
        dict: Contains 'status', 'score', and 'feedback'.
    """
    agent_name = tool_context.agent_name if tool_context else "Unknown Agent"
    print(f"--- Tool: mock_score_tool invoked by {agent_name} ---")

    # --- 从 State 读取评分标准和文稿 ---
    state = tool_context.state
    draft = state.get(CURRENT_DRAFT_KEY, '') # 修改点：从 state 读取 draft
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, '')

    if not criteria:
        print(f"--- Tool: Error - Missing '{INITIAL_SCORING_CRITERIA_KEY}' in session state. ---")
        # 即使出错，也尝试写入错误状态，避免后续 Agent 拿到旧数据
        state[CURRENT_SCORE_KEY] = 0.0
        state[CURRENT_FEEDBACK_KEY] = "错误：会话状态中缺少评分标准。"
        return {"status": "error", "score": 0.0, "feedback": "错误：会话状态中缺少评分标准。"}

    if not draft:
        print(f"--- Tool: Error - Missing or empty '{CURRENT_DRAFT_KEY}' in session state for scoring. ---")
        state[CURRENT_SCORE_KEY] = 0.0
        state[CURRENT_FEEDBACK_KEY] = "错误：状态中没有文稿用于评分。"
        return {"status": "error", "score": 0.0, "feedback": "错误：状态中没有文稿用于评分。"}

    print(f"--- Tool: Scoring draft from state: '{draft[:50]}...'")
    print(f"--- Tool: Read criteria from state: {criteria[:50]}...")

    # Simulate scoring process
    mock_score = 7.0 + len(draft) / 100.0
    mock_score = round(min(mock_score, 9.5), 2) # 保留两位小数
    mock_feedback = f"模拟评分反馈(Round X): 基于标准 '{criteria[:20]}...', 草稿得分尚可。"
    print(f"--- Tool: Assigned score: {mock_score:.2f} ---")
    print(f"--- Tool: Provided feedback: {mock_feedback} ---")

    # 修改点：将结果写入 Session State
    state[CURRENT_SCORE_KEY] = mock_score
    state[CURRENT_FEEDBACK_KEY] = mock_feedback
    print(f"--- Tool: Wrote score ({CURRENT_SCORE_KEY}) and feedback ({CURRENT_FEEDBACK_KEY}) to state ---")

    # 返回结果字典（可以用于 Agent 确认或日志）
    return {"status": "success", "score": mock_score, "feedback": mock_feedback}

# Example Usage 注释需要更新或移除，因为工具签名已更改

# 移除旧的 Class 定义
# class MockWritingAgent: ...
# class MockScoringAgent: ... 