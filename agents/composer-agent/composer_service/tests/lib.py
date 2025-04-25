from google.adk.sessions import InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext

def make_adk_context(agent, state, invocation_id="test_case"):
    """
    构造标准 ADK Session 和 InvocationContext，便于 run_async 测试。
    """
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="composer-service",
        user_id="test_user",
    )
    session.state.update(state)
    invoc_context = InvocationContext(
        session_service=session_service,
        invocation_id=invocation_id,
        agent=agent,
        session=session,
    )
    return session, invoc_context 