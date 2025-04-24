import logging
from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY

logger = logging.getLogger(__name__)

def save_score(tool_context) -> dict:
    """
    保存评分和反馈到 session state。
    依赖state字段：CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY
    Args:
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"actions": {"escalate": False}, ...}
    """
    sm = StateManager(tool_context)
    score = tool_context.state.get(CURRENT_SCORE_KEY, None)
    feedback = tool_context.state.get(CURRENT_FEEDBACK_KEY, "")
    if not isinstance(score, int):
        logger.info("[save_score] score必须为百分制整数")
        return {"actions": {"escalate": False}, "status": "error", "message": "score必须为百分制整数"}
    if not isinstance(feedback, str) or not feedback.strip():
        logger.info("[save_score] feedback必须为非空字符串")
        return {"actions": {"escalate": False}, "status": "error", "message": "feedback必须为非空字符串"}
    ok1 = sm.set(CURRENT_SCORE_KEY, score)
    ok2 = sm.set(CURRENT_FEEDBACK_KEY, feedback)
    if ok1 and ok2:
        return {"actions": {"escalate": False}, "status": "success"}
    else:
        logger.error("[save_score] 保存评分或反馈失败")
        return {"actions": {"escalate": False}, "status": "error", "message": "保存评分或反馈失败"} 