from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, ITERATION_COUNT_KEY

def get_final_draft(tool_context) -> dict:
    """
    获取最终草稿及相关信息。
    """
    sm = StateManager(tool_context)
    draft = sm.get(CURRENT_DRAFT_KEY, "")
    score = sm.get(CURRENT_SCORE_KEY, None)
    feedback = sm.get(CURRENT_FEEDBACK_KEY, "")
    iterations = sm.get(ITERATION_COUNT_KEY, 0)
    return {
        "final_draft_text": draft,
        "final_score": score,
        "final_feedback": feedback,
        "iterations_completed": iterations,
        "status": "success"
    } 