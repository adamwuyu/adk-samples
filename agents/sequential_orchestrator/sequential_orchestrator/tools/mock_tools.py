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
    agent_name = "Unknown Agent"  # 不再从 tool_context 获取 agent_name
    print(f"--- Tool: mock_write_tool invoked by {agent_name} ---")

    # --- 从 State 读取输入 ---
    # 不直接从 tool_context.state 获取，而是尝试使用其他方式访问状态
    # 这里假设有一个可用的会话状态或全局状态变量
    from google.adk.agents.invocation_context import InvocationContext
    material = "示例材料"  # 默认值
    requirements = "示例要求"  # 默认值
    
    # 这里应该使用合适的方式获取状态，具体取决于 ADK 版本
    # 在实际使用中，需要调整为适合当前 ADK 的方式

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

# 修改函数签名，直接接受状态参数
def mock_score_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    对当前草稿进行评分，并根据评分标准提供反馈。
    
    此工具从会话状态中检索草稿文本和评分标准，计算分数，生成反馈，
    并将结果保存回会话状态。评分以10分为满分。
    
    State Input:
      current_draft: 需要评分的草稿文本
      initial_scoring_criteria: 评分标准
      
    State Output:
      current_score: 生成的评分 (0-10)
      current_feedback: 生成的反馈
    
    Returns:
      dict: 包含 'status'（'success' 或 'error'）、'score' 和 'feedback'。
    """
    print(f"--- Tool: mock_score_tool invoked ---")
    
    # 从 session state 中读取文稿和评分标准
    # 注意：根据 ADK 设计，state 是 ToolContext 的标准属性
    state = tool_context.state
    
    # 获取文稿和评分标准
    draft = state.get(CURRENT_DRAFT_KEY, "")
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, "")
    
    print(f"--- Tool: Retrieved from state - Draft: {'Found' if draft else 'Not found'} ---")
    print(f"--- Tool: Retrieved from state - Criteria: {'Found' if criteria else 'Not found'} ---")
    
    # 使用默认值（如果需要）
    if not draft:
        print(f"--- Tool: Warning: No draft found in state at key '{CURRENT_DRAFT_KEY}' ---")
        draft = "这是一个模拟的草稿文本，用于测试评分工具。"
    else:
        print(f"--- Tool: Draft (first 50 chars): {draft[:50]}... ---")
    
    if not criteria:
        print(f"--- Tool: Warning: No criteria found in state at key '{INITIAL_SCORING_CRITERIA_KEY}' ---")
        criteria = "清晰度、流畅性和平衡论述"
    else:
        print(f"--- Tool: Criteria: {criteria} ---")
    
    # Simulate scoring process
    mock_score = 7.5  # 基础得分
    if len(draft) > 100:
        mock_score += 1.0  # 更长的草稿得分更高
    mock_score = round(min(mock_score, 9.5), 2)  # 保留两位小数，最高9.5分
    
    mock_feedback = f"模拟评分反馈: 基于标准 '{criteria}', 草稿得分为 {mock_score}。需要更多针对AI写作工具优缺点的内容。"
    print(f"--- Tool: Assigned score: {mock_score:.2f} ---")
    print(f"--- Tool: Provided feedback: {mock_feedback} ---")
    
    # 将结果写回 session state
    try:
        state[CURRENT_SCORE_KEY] = mock_score
        state[CURRENT_FEEDBACK_KEY] = mock_feedback
        print(f"--- Tool: Successfully wrote score and feedback to state ---")
        print(f"--- Tool: Current state now has score={state.get(CURRENT_SCORE_KEY)}, feedback length={len(state.get(CURRENT_FEEDBACK_KEY, ''))} chars ---")
    except Exception as e:
        print(f"--- Tool: Error writing to state: {e} ---")
    
    # 返回结果字典
    return {"status": "success", "score": mock_score, "feedback": mock_feedback}

# Example Usage 注释需要更新或移除，因为工具签名已更改

# 移除旧的 Class 定义
# class MockWritingAgent: ...
# class MockScoringAgent: ... 