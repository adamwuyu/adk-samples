import pytest
from composer_service.agents.scorer import Scorer
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)

class DummySession:
    def __init__(self, state):
        self.state = state

class DummyContext:
    def __init__(self, state):
        self.session = DummySession(state)

@pytest.mark.asyncio
@pytest.mark.parametrize("state,expected_score,expected_feedback_prefix", [
    ({
        CURRENT_DRAFT_KEY: "一篇好稿件ABCDEFGH",
        INITIAL_SCORING_CRITERIA_KEY: "标准XYZ123"
    }, 88, "MOCK_FEEDBACK: 很棒的稿件！摘要: 一篇好稿件A | 标准XYZ1"),
    ({
        CURRENT_DRAFT_KEY: "A",
        INITIAL_SCORING_CRITERIA_KEY: "B"
    }, 88, "MOCK_FEEDBACK: 很棒的稿件！摘要: A | B"),
])
async def test_scorer_generates_mock(state, expected_score, expected_feedback_prefix):
    agent = Scorer()
    ctx = DummyContext(state)
    events = []
    async for event in agent._run_async_impl(ctx):
        events.append(event)
    assert state[CURRENT_SCORE_KEY] == expected_score
    assert state[CURRENT_FEEDBACK_KEY].startswith(expected_feedback_prefix)
    assert events[0]["event"] == "scoring_finished"
    assert events[0]["score"] == expected_score
    assert events[0]["feedback"].startswith(expected_feedback_prefix)

@pytest.mark.asyncio
async def test_scorer_missing_inputs():
    agent = Scorer()
    state = {}
    ctx = DummyContext(state)
    events = []
    async for event in agent._run_async_impl(ctx):
        events.append(event)
    # 依然会生成MOCK分数和反馈，但内容为空
    assert state[CURRENT_SCORE_KEY] == 88
    assert state[CURRENT_FEEDBACK_KEY].startswith("MOCK_FEEDBACK: 很棒的稿件！摘要:  | ")
    assert events[0]["event"] == "scoring_finished" 