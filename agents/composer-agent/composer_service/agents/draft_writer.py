from google.adk.agents import LlmAgent
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY,
)

class DraftWriter(LlmAgent):
    def __init__(self):
        super().__init__(
            name="DraftWriter",
            instruction=f"请根据 state['{INITIAL_MATERIAL_KEY}']、state['{INITIAL_REQUIREMENTS_KEY}']、state['{INITIAL_SCORING_CRITERIA_KEY}'] 生成初稿。",
            output_key=CURRENT_DRAFT_KEY
        )

    async def _run_async_impl(self, ctx):
        # 读取state
        state = ctx.session.state
        material = state.get(INITIAL_MATERIAL_KEY, "")
        requirements = state.get(INITIAL_REQUIREMENTS_KEY, "")
        criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, "")
        # 生成MOCK内容，取前6字符作为摘要
        draft = f"MOCK_DRAFT: {material[:6]} | {requirements[:6]} | {criteria[:6]}"
        state[CURRENT_DRAFT_KEY] = draft
        # LlmAgent通常yield事件，这里直接yield结果
        yield {
            "event": "draft_generated",
            "draft": draft
        } 