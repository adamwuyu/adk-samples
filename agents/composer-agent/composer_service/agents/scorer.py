import logging
from types import SimpleNamespace
from google.adk.agents import LlmAgent
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)

logger = logging.getLogger(__name__)

# 递归包装 dict 为 SimpleNamespace，actions 字段单独处理
def wrap_event(item):
    if isinstance(item, dict):
        actions = item.get("actions", {})
        wrapped = SimpleNamespace(
            actions=SimpleNamespace(**actions),
            **{k: v for k, v in item.items() if k != "actions"}
        )
        return wrapped
    return item

class Scorer(LlmAgent):
    def __init__(self):
        super().__init__(
            name="Scorer",
            instruction=f"请根据 state['{CURRENT_DRAFT_KEY}']、state['{INITIAL_SCORING_CRITERIA_KEY}'] 评分并给出反馈。",
        )

    async def _run_async_impl(self, ctx):
        state = ctx.session.state
        draft = state.get(CURRENT_DRAFT_KEY, "")
        criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, "")
        # 生成MOCK分数和反馈
        score = 88
        feedback = f"MOCK_FEEDBACK: 很棒的稿件！摘要: {draft[:6]} | {criteria[:6]}"
        state[CURRENT_SCORE_KEY] = score
        state[CURRENT_FEEDBACK_KEY] = feedback
        result = {
            "event": "scoring_finished",
            "score": score,
            "feedback": feedback,
            "actions": {"escalate": False}
        }
        event = wrap_event(result)
        logger.debug(f"[Scorer] yield type: {type(event)}, value: {event}")
        yield event 