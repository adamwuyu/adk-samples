import os
import pytest
from ..agents.draft_writer import DraftWriter
from ..tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY,
)
from .lib import make_adk_context

class DummySession:
    def __init__(self, state):
        self.state = state

class DummyContext:
    def __init__(self, state):
        self.session = DummySession(state)

@pytest.mark.integration
@pytest.mark.asyncio
def test_draft_writer_real_llm():
    """
    集成测试：验证 DraftWriter 能实际调用真实 LLM，CURRENT_DRAFT_KEY 被写入为非空字符串。
    运行前需确保已设置 KINGDORA_BASE_URL 和 KINGDORA_API_KEY 环境变量。
    """
    # 检查环境变量
    kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
    kingdora_api_key = os.getenv("KINGDORA_API_KEY")
    if not kingdora_base_url or not kingdora_api_key:
        pytest.skip("未设置 KINGDORA_BASE_URL 或 KINGDORA_API_KEY，跳过集成测试")

    # 构造输入
    state = {
        INITIAL_MATERIAL_KEY: "请用一句话介绍你自己。",
        INITIAL_REQUIREMENTS_KEY: "要求内容简洁、真实。",
        INITIAL_SCORING_CRITERIA_KEY: "内容相关性、表达清晰度。"
    }
    agent = DraftWriter()
    session, invoc_context = make_adk_context(agent, state, invocation_id="integration_draft_writer")
    events = []
    import asyncio
    async def run_agent():
        async for event in agent.run_async(invoc_context):
            events.append(event)
    asyncio.get_event_loop().run_until_complete(run_agent())
    # 断言 CURRENT_DRAFT_KEY 被写入且为非空字符串
    draft = session.state.get(CURRENT_DRAFT_KEY, "")
    assert isinstance(draft, str) and draft.strip() != ""
    # 事件内容也应为非空字符串
    assert events[0].content.parts[0].text and isinstance(events[0].content.parts[0].text, str) 