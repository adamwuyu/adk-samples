import pytest
from composer_service.workflow import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext

@pytest.mark.asyncio
async def test_full_workflow_integration():
    # 构造真实 ADK Session
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="composer-service",
        user_id="test_user",
    )
    # 初始化 session state
    session.state.update({
        "initial_material": "材料A",
        "initial_requirements": "要求B",
        "initial_scoring_criteria": "标准C",
    })
    # 构造 InvocationContext
    invoc_context = InvocationContext(
        session_service=session_service,
        invocation_id="test_integration",
        agent=root_agent,
        session=session,
    )
    events = []
    # 用 run_async 驱动
    async for event in root_agent.run_async(invoc_context):
        events.append(event)
    assert "current_draft" in session.state
    assert "current_score" in session.state or "current_feedback" in session.state
    assert any(getattr(e, "event", None) == "draft_generated" for e in events) 