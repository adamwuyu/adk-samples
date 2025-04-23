from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import CURRENT_DRAFT_KEY

def save_draft_result(content: str, tool_context) -> dict:
    """
    保存稿件内容到 session state。
    Args:
        content: 要保存的稿件内容
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"status": "success"} 或 {"status": "error", "message": ...}
    """
    sm = StateManager(tool_context)
    if not isinstance(content, str) or not content.strip():
        return {"status": "error", "message": "content必须为非空字符串"}
    ok = sm.set(CURRENT_DRAFT_KEY, content)
    if ok:
        return {"status": "success"}
    else:
        return {"status": "error", "message": "保存稿件失败"} 