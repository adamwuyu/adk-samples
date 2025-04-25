from google.adk.sessions import InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from types import SimpleNamespace

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

# 公用 mock LLM 工具

def create_mock_response_chunk(text):
    return SimpleNamespace(
        content=SimpleNamespace(
            parts=[SimpleNamespace(text=text)]
        )
    )

class MockLlmClient:
    def __init__(self, response_text):
        self.response_text = response_text
        self.captured_request = None
    async def generate_content_async(self, request):
        self.captured_request = request
        yield create_mock_response_chunk(self.response_text)

class ErrorMockLlmClient:
    async def generate_content_async(self, request):
        raise RuntimeError("LLM API Error")
        yield  # 语法上需要，但不会执行

# # 公用事件包装函数 (移至 utils.py)
# def wrap_event(item):
#     if isinstance(item, dict):
#         actions = item.get("actions", {})
#         wrapped = SimpleNamespace(
#             actions=SimpleNamespace(**actions),
#             **{k: v for k, v in item.items() if k != "actions"}
#         )
#         return wrapped
#     return item 