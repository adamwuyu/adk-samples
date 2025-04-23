from google.adk.agents import LlmAgent
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)

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
        score = 8.8
        feedback = f"MOCK_FEEDBACK: 很棒的稿件！摘要: {draft[:6]} | {criteria[:6]}"
        state[CURRENT_SCORE_KEY] = score
        state[CURRENT_FEEDBACK_KEY] = feedback
        yield {
            "event": "scoring_finished",
            "score": score,
            "feedback": feedback
        } 