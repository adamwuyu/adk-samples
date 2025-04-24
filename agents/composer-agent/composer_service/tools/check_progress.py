import logging
from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import (
    CURRENT_SCORE_KEY,
    SCORE_THRESHOLD_KEY,
    ITERATION_COUNT_KEY,
)

logger = logging.getLogger(__name__)

def check_progress(tool_context) -> dict:
    """
    检查是否达到终止条件：分数达标或达到最大迭代次数。
    依赖state字段：CURRENT_SCORE_KEY, SCORE_THRESHOLD_KEY, ITERATION_COUNT_KEY
    评分采用百分制整数，默认及格线为60分。
    返回actions.escalate信号，供LoopAgent终止。
    Args:
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"status": "continue"/"done", "actions": {"escalate": bool}, ...}
    """
    sm = StateManager(tool_context)
    score = sm.get(CURRENT_SCORE_KEY)
    threshold = sm.get(SCORE_THRESHOLD_KEY, 60)  # 默认60分及格
    iteration = sm.get(ITERATION_COUNT_KEY, 0)
    max_iterations = tool_context.state.get("max_iterations", 5)  # 支持动态最大轮数

    # 终止条件1：分数达标
    if isinstance(score, int) and score >= threshold:
        result = {
            "status": "done",
            "reason": "score_passed",
            "actions": {"escalate": True}
        }
        logger.info(f"[check_progress] 达到分数阈值: {score} >= {threshold}")
        return result
    # 终止条件2：达到最大轮数
    if iteration >= max_iterations:
        result = {
            "status": "done",
            "reason": "max_iterations",
            "actions": {"escalate": True}
        }
        logger.info(f"[check_progress] 达到最大轮数: {iteration} >= {max_iterations}")
        return result
    # 否则继续
    result = {
        "status": "continue",
        "actions": {"escalate": False}
    }
    logger.debug(f"[check_progress] 继续迭代: iteration={iteration}, score={score}")
    return result 