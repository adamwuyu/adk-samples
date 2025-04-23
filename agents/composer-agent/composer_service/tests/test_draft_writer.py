import pytest
from types import SimpleNamespace
from composer_service.agents.draft_writer import DraftWriter
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY,
)

class DummySession:
    def __init__(self, state):
        self.state = state

class DummyContext:
    def __init__(self, state):
        self.session = DummySession(state)

@pytest.mark.asyncio
@pytest.mark.parametrize("state,expected_prefix", [
    ({
        INITIAL_MATERIAL_KEY: "素材内容ABCDEFGH", 
        INITIAL_REQUIREMENTS_KEY: "要求内容12345678", 
        INITIAL_SCORING_CRITERIA_KEY: "评分标准XYZ" 
    }, "MOCK_DRAFT: 素材内容AB | 要求内容12 | 评分标准X"),
    ({
        INITIAL_MATERIAL_KEY: "A", 
        INITIAL_REQUIREMENTS_KEY: "B", 
        INITIAL_SCORING_CRITERIA_KEY: "C" 
    }, "MOCK_DRAFT: A | B | C"),
])
async def test_draft_writer_generates_mock(state, expected_prefix):
    agent = DraftWriter()
    ctx = DummyContext(state)
    events = []
    async for event in agent._run_async_impl(ctx):
        events.append(event)
    assert state[CURRENT_DRAFT_KEY].startswith(expected_prefix)
    assert events[0]["event"] == "draft_generated"
    assert events[0]["draft"].startswith(expected_prefix)

@pytest.mark.asyncio
async def test_draft_writer_missing_inputs():
    agent = DraftWriter()
    state = {}
    ctx = DummyContext(state)
    events = []
    async for event in agent._run_async_impl(ctx):
        events.append(event)
    assert state.get(CURRENT_DRAFT_KEY, "").startswith("MOCK_DRAFT:  |  | ")
    assert events[0]["event"] == "draft_generated" 