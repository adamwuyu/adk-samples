import pytest
from ..workflow import root_agent
from .lib import make_adk_context

@pytest.mark.asyncio
async def test_full_workflow_integration():
    # 构造真实 ADK Session
    state = {
        "initial_material": "材料A",
        "initial_requirements": "要求B",
        "initial_scoring_criteria": "标准C",
    }
    session, invoc_context = make_adk_context(root_agent, state, invocation_id="test_integration")
    events = []
    # 用 run_async 驱动
    async for event in root_agent.run_async(invoc_context):
        events.append(event)
    assert "current_draft" in session.state
    assert "current_score" in session.state or "current_feedback" in session.state
    # assert any(getattr(e, "event", None) == "draft_generated" for e in events) 