import pytest

try:
    import google.adk
except ImportError:
    pytest.skip("Skipping real context test due to google.adk not installed", allow_module_level=True)

# 以下使用真实 InMemorySessionService + ToolContext 测试 StateManager
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents import BaseAgent

from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    CURRENT_SCORE_KEY,
    SCORE_THRESHOLD_KEY,
)

@ pytest.fixture(scope="function")
def tool_context_real():

    class DummyAgent(BaseAgent):
      name: str = "dummy"
      instruction: str = "dummy agent for test"

    # 使用真实 ADK 上下文
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="composer-service",
        user_id="test_real_user",
    )
    session.state[SCORE_THRESHOLD_KEY] = 0.99

    dummy_agent = DummyAgent()
    invoc_context = InvocationContext(
        session_service=session_service,
        invocation_id="test_real",
        agent=dummy_agent,
        session=session,
    )
    return ToolContext(invocation_context=invoc_context)


def test_real_set_and_get(tool_context_real):
    sm = StateManager(tool_context_real)
    # 测试读取初始值
    assert sm.get(SCORE_THRESHOLD_KEY) == 0.99
    # 测试字符串写入与读取
    assert sm.set(INITIAL_MATERIAL_KEY, "real material")
    assert sm.get(INITIAL_MATERIAL_KEY) == "real material"
    # 测试数值写入与读取
    assert sm.set(CURRENT_SCORE_KEY, 8.8)
    assert sm.get(CURRENT_SCORE_KEY) == 8.8 