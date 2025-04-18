"""Tools for managing session state in the sequential orchestrator."""

import typing
from google.adk.tools import ToolContext
import logging

logger = logging.getLogger(__name__)

# 定义常量以便复用
INITIAL_MATERIAL_KEY = "initial_material"
INITIAL_REQUIREMENTS_KEY = "initial_requirements"
INITIAL_SCORING_CRITERIA_KEY = "initial_scoring_criteria"
# --- V0.5 State Keys ---
CURRENT_DRAFT_KEY = "current_draft"
CURRENT_SCORE_KEY = "current_score"
CURRENT_FEEDBACK_KEY = "current_feedback"
# --- End V0.5 State Keys ---

# V0.5 - 新增阈值 Key
SCORE_THRESHOLD_KEY = "score_threshold" # 用于判断是否提前终止循环

def check_initial_data(tool_context: ToolContext) -> dict[str, str]:
    """
    检查会话状态中是否存在必要的初始数据。
    
    此工具会检查以下三个关键的状态数据是否存在且不为空：
    1. initial_material - 原始素材内容
    2. initial_requirements - 写作要求
    3. initial_scoring_criteria - 评分标准
    
    Returns:
        dict: 返回包含状态信息的字典，如果所有必要数据都存在，则 'status' 为 'ready'；
             否则 'status' 为 'missing_data'。
    """
    logger.info("Checking for initial data in session state...")
    state = tool_context.state
    material = state.get(INITIAL_MATERIAL_KEY)
    requirements = state.get(INITIAL_REQUIREMENTS_KEY)
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY)

    if material and requirements and criteria:
        logger.info("Initial data found in session state.")
        return {"status": "ready"}
    else:
        missing_keys = []
        if not material: missing_keys.append(INITIAL_MATERIAL_KEY)
        if not requirements: missing_keys.append(INITIAL_REQUIREMENTS_KEY)
        if not criteria: missing_keys.append(INITIAL_SCORING_CRITERIA_KEY)
        logger.warning(f"Initial data missing in session state. Missing keys: {missing_keys}")
        return {"status": "missing_data"}

def store_initial_data(
    initial_material: str,
    initial_requirements: str,
    initial_scoring_criteria: str,
    tool_context: ToolContext
) -> dict[str, str]:
    """
    将用户提供的初始数据存储到会话状态中。
    
    Args:
        initial_material: 写作的原始素材内容
        initial_requirements: 写作的具体要求
        initial_scoring_criteria: 评分的标准和方法
        tool_context: ADK 工具上下文，用于访问会话状态
    
    Returns:
        dict: 返回包含操作状态信息的字典，'status' 字段表示存储操作的结果
    """
    try:
        logger.info(f"Storing initial data into session state: Material='{initial_material[:50]}...', Requirements='{initial_requirements[:50]}...', Criteria='{initial_scoring_criteria[:50]}...'" )
        tool_context.state.update({
            INITIAL_MATERIAL_KEY: initial_material,
            INITIAL_REQUIREMENTS_KEY: initial_requirements,
            INITIAL_SCORING_CRITERIA_KEY: initial_scoring_criteria,
        })
        logger.info("Successfully updated session state with initial data.")
        return {"status": "Initial data successfully stored in session state."}
    except Exception as e:
        logger.error(f"Error storing initial data in session state: {e}", exc_info=True)
        return {"status": f"Failed to store initial data due to an error: {e}"}

# --- 新增：获取最终草稿的 Tool ---
def get_final_draft(tool_context: ToolContext) -> dict[str, str]:
    """Retrieves the final draft text stored in the session state under the 'current_draft' key.

    Args:
        tool_context: The ADK tool context providing access to session state.

    Returns:
        A dict containing the retrieved draft text, e.g., {'final_draft_text': '...'}.
        If the draft is not found, returns a default message in the text field.
    """
    try:
        logger.info(f"Retrieving final draft from state key '{CURRENT_DRAFT_KEY}'.")
        draft_content = tool_context.state.get(CURRENT_DRAFT_KEY, "Error: Final draft not found in session state.")
        logger.info(f"Retrieved draft: '{draft_content[:100]}...'" )
        return {"final_draft_text": draft_content}
    except Exception as e:
        logger.error(f"Error retrieving final draft from session state: {e}", exc_info=True)
        return {"final_draft_text": f"Error retrieving draft: {e}"} 