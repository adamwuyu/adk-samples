import logging
from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import CURRENT_DRAFT_KEY

logger = logging.getLogger(__name__)

def save_draft_result(tool_context) -> dict:
    """
    保存稿件内容到 session state。
    依赖state字段：CURRENT_DRAFT_KEY
    Args:
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"actions": {"escalate": False}, ...}
    """
    logger.info("[save_draft_result] 开始保存稿件...")
    sm = StateManager(tool_context)
    content = tool_context.state.get(CURRENT_DRAFT_KEY, "")
    if not isinstance(content, str) or not content.strip():
        logger.warning("[save_draft_result] 状态中的稿件内容不是有效的非空字符串。")
        return {"actions": {"escalate": False}, "status": "error", "message": "content必须为非空字符串"}
    try:
        ok = sm.set(CURRENT_DRAFT_KEY, content)
        if ok:
            logger.info(f"[save_draft_result] 稿件成功保存到状态 {CURRENT_DRAFT_KEY}。")
            return {"actions": {"escalate": False}, "status": "success"}
        else:
            logger.error("[save_draft_result] StateManager 返回保存失败信号。")
            return {"actions": {"escalate": False}, "status": "error", "message": "保存稿件失败"}
    except Exception as e:
        logger.exception(f"[save_draft_result] 保存稿件时发生异常: {e}")
        return {"actions": {"escalate": False}, "status": "error", "message": f"保存稿件时发生异常: {e}"} 