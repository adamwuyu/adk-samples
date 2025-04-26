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
    logger.info("[check_progress] 开始检查进度...")
    sm = StateManager(tool_context)
    try:
        score = sm.get(CURRENT_SCORE_KEY)
        threshold = sm.get(SCORE_THRESHOLD_KEY, 60)  # 默认60分及格
        iteration = sm.get(ITERATION_COUNT_KEY, 0)
        max_iterations = tool_context.state.get("max_iterations", 5)  # 支持动态最大轮数

        logger.debug(f"[check_progress] 当前状态: score={score}, threshold={threshold}, iteration={iteration}, max_iterations={max_iterations}")

        # 校验阈值和最大轮数类型
        if not isinstance(threshold, (int, float)):
            logger.warning(f"[check_progress] 分数阈值类型无效 ({type(threshold)})，使用默认值 60。")
            threshold = 60
        if not isinstance(max_iterations, int) or max_iterations <= 0:
            logger.warning(f"[check_progress] 最大迭代次数无效 ({type(max_iterations)})，使用默认值 5。")
            max_iterations = 5

        # 终止条件1：分数达标
        score_passed = False
        if isinstance(score, (int, float)):
            if score >= threshold:
                score_passed = True
        else:
            logger.warning(f"[check_progress] 当前分数类型无效: {score} ({type(score)})，无法判断是否达标。")
        
        if score_passed:
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
        logger.info(f"[check_progress] 继续迭代: iteration={iteration}, score={score}")
        return result
    except Exception as e:
        logger.exception(f"[check_progress] 检查进度时发生异常: {e}")
        # 异常情况下，保守起见，选择继续执行，避免流程卡死
        return {
            "status": "continue", 
            "actions": {"escalate": False}, 
            "error": f"检查进度时发生异常: {e}"
        } 