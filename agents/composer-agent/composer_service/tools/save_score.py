from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY

def save_score(score, feedback, tool_context) -> dict:
    """
    保存评分和反馈到 session state。
    Args:
        score: 评分分数（int，百分制整数）
        feedback: 评分反馈（str）
        tool_context: ADK工具上下文，需有.state属性
    Returns:
        dict: {"status": "success"} 或 {"status": "error", "message": ...}
    """
    sm = StateManager(tool_context)
    if not isinstance(score, int):
        return {"status": "error", "message": "score必须为百分制整数"}
    if not isinstance(feedback, str) or not feedback.strip():
        return {"status": "error", "message": "feedback必须为非空字符串"}
    ok1 = sm.set(CURRENT_SCORE_KEY, score)
    ok2 = sm.set(CURRENT_FEEDBACK_KEY, feedback)
    if ok1 and ok2:
        return {"status": "success"}
    else:
        return {"status": "error", "message": "保存评分或反馈失败"} 