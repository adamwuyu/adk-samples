"""Mock Tools for MVP testing, following ADK patterns and accessing state internally."""

from typing import Any, Dict, Optional
from google.adk.tools.tool_context import ToolContext # Import ToolContext

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
def mock_score_tool(draft: str, tool_context: ToolContext) -> Dict[str, Any]: # 移除了 criteria 参数
    """
    Simulates scoring a given draft. Retrieves scoring criteria from session state
    via tool_context. Returns a dictionary containing the score and feedback.

    Expected State Keys:
        initial_scoring_criteria (str): The scoring criteria.

    Args:
        draft (str): The draft text to be scored (passed from the previous step).
        tool_context (ToolContext): Provides access to session state.

    Returns:
        dict: Contains 'status' ('success' or 'error'), 'score', and 'feedback'.
    """
    agent_name = tool_context.agent_name if tool_context else "Unknown Agent"
    print(f"--- Tool: mock_score_tool invoked by {agent_name} ---")

    # --- 从 State 读取评分标准 ---
    criteria = tool_context.state.get('initial_scoring_criteria', '') # 从 state 获取

    if not criteria:
        print("--- Tool: Error - Missing 'initial_scoring_criteria' in session state. ---")
        return {"status": "error", "score": 0.0, "feedback": "错误：会话状态中缺少评分标准。"}

    print(f"--- Tool: Scoring draft: '{draft[:50]}...'")
    print(f"--- Tool: Read from state - criteria: {criteria[:50]}...")

    if not draft:
        print("--- Tool: Error - No draft provided for scoring. ---")
        return {"status": "error", "score": 0.0, "feedback": "错误：没有提供文稿用于评分。"}

    # Simulate scoring process
    mock_score = 7.0 + len(draft) / 100.0
    mock_score = min(mock_score, 9.5)
    mock_feedback = f"模拟评分反馈：基于标准 '{criteria[:20]}...' (从state读取)，草稿得分尚可。"
    print(f"--- Tool: Assigned score: {mock_score:.1f} ---")
    print(f"--- Tool: Provided feedback: {mock_feedback} ---")

    return {"status": "success", "score": mock_score, "feedback": mock_feedback}

# Example Usage 注释需要更新或移除，因为工具签名已更改

# 移除旧的 Class 定义
# class MockWritingAgent: ...
# class MockScoringAgent: ... 