from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
)
import logging

logger = logging.getLogger(__name__)

def check_initial_data(tool_context) -> dict:
    """
    检查Session State中是否存在必要的初始数据。
    Args:
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"status": "ready"} 或 {"status": "missing_data", "missing_keys": [...]} 
    """
    logger.info("[check_initial_data] 开始检查初始数据...")
    sm = StateManager(tool_context)
    required_keys = [
        INITIAL_MATERIAL_KEY,
        INITIAL_REQUIREMENTS_KEY,
        INITIAL_SCORING_CRITERIA_KEY,
    ]
    missing = [k for k in required_keys if sm.get(k) in (None, "")]
    if not missing:
        logger.info("[check_initial_data] 所有必需的初始数据都存在。")
        return {"status": "ready"}
    else:
        logger.warning(f"[check_initial_data] 缺少初始数据: {missing}")
        return {"status": "missing_data", "missing_keys": missing} 