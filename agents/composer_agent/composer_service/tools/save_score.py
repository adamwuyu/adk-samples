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
    logger.info("[save_score] 开始保存评分和反馈...")
    sm = StateManager(tool_context)
    score = tool_context.state.get(CURRENT_SCORE_KEY, None)
    feedback = tool_context.state.get(CURRENT_FEEDBACK_KEY, "")
    if not isinstance(score, int):
        logger.warning(f"[save_score] 状态中的分数不是有效的整数: {score} ({type(score)})。")
        return {"actions": {"escalate": False}, "status": "error", "message": "score必须为百分制整数"}
    if not isinstance(feedback, str) or not feedback.strip():
        logger.warning("[save_score] 状态中的反馈不是有效的非空字符串。")
        return {"actions": {"escalate": False}, "status": "error", "message": "feedback必须为非空字符串"}
    try:
        ok1 = sm.set(CURRENT_SCORE_KEY, score)
        ok2 = sm.set(CURRENT_FEEDBACK_KEY, feedback)
        if ok1 and ok2:
            logger.info(f"[save_score] 评分 ({score}) 和反馈成功保存到状态。")
            return {"actions": {"escalate": False}, "status": "success"}
        else:
            logger.error(f"[save_score] StateManager 返回保存失败信号 (score: {ok1}, feedback: {ok2})。")
            return {"actions": {"escalate": False}, "status": "error", "message": "保存评分或反馈失败"}
    except Exception as e:
        logger.exception(f"[save_score] 保存评分或反馈时发生异常: {e}")
        return {"actions": {"escalate": False}, "status": "error", "message": f"保存评分或反馈时发生异常: {e}"} 