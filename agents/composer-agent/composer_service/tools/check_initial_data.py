from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
)

def check_initial_data(tool_context) -> dict:
    """
    检查Session State中是否存在必要的初始数据。
    Args:
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"status": "ready"} 或 {"status": "missing_data", "missing_keys": [...]} 
    """
    sm = StateManager(tool_context)
    required_keys = [
        INITIAL_MATERIAL_KEY,
        INITIAL_REQUIREMENTS_KEY,
        INITIAL_SCORING_CRITERIA_KEY,
    ]
    missing = [k for k in required_keys if sm.get(k) in (None, "")]
    if not missing:
        return {"status": "ready"}
    else:
        return {"status": "missing_data", "missing_keys": missing} 