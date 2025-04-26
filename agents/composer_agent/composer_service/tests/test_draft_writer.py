import pytest
from unittest import mock
from ..agents.draft_writer import DraftWriter
from ..tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY,
)
from .lib import make_adk_context, create_mock_response_chunk, MockLlmClient, ErrorMockLlmClient

class DummySession:
    def __init__(self, state):
        self.state = state

class DummyContext:
    def __init__(self, state):
        self.session = DummySession(state)

# 定义一个通用的模拟响应结构
def create_mock_response_chunk(text):
    return SimpleNamespace(
        content=SimpleNamespace(
            parts=[SimpleNamespace(text=text)]
        )
    )

@pytest.mark.asyncio
async def test_draft_writer_llm_prompt_and_state(monkeypatch):
    """
    用例说明：
    - 测试 DraftWriter 在输入完整时，能正确构建 Prompt，调用 LLM，并将 LLM 返回内容写入状态和事件。
    - 通过 mock LLM client，捕获传入的 prompt 内容，确保 prompt 构建符合预期。
    - 断言状态和事件内容等于 mock LLM 返回值。
    """
    state = {
        INITIAL_MATERIAL_KEY: "素材内容ABCDEFGH",
        INITIAL_REQUIREMENTS_KEY: "要求内容12345678",
        INITIAL_SCORING_CRITERIA_KEY: "评分标准XYZ"
    }
    ctx = DummyContext(state)
    prompts = {}
    # mock 的 LLM client，记录 prompt 并返回固定内容
    mock_llm = MockLlmClient("LLM生成的稿件内容")
    with mock.patch("composer_agent.composer_service.agents.draft_writer.get_llm_client", return_value=mock_llm):
        agent = DraftWriter()
        session, invoc_context = make_adk_context(agent, state, invocation_id="test_case_1")
        events = []
        async for event in agent.run_async(invoc_context):
            events.append(event)
        # 检查 prompt 构建
        assert "素材内容ABCDEFGH" in mock_llm.captured_request.contents[0].parts[0].text
        assert "要求内容12345678" in mock_llm.captured_request.contents[0].parts[0].text
        assert "评分标准XYZ" in mock_llm.captured_request.contents[0].parts[0].text
        # 检查状态写入
        assert session.state[CURRENT_DRAFT_KEY] == "LLM生成的稿件内容"
        # 检查事件内容
        assert events[0].content.parts[0].text == "LLM生成的稿件内容"

@pytest.mark.asyncio
async def test_draft_writer_llm_exception(monkeypatch):
    """
    用例说明：
    - 测试 DraftWriter 在 LLM 调用抛出异常时，能捕获异常并写入错误提示。
    - mock 的 LLM client 直接抛出异常，模拟 LLM API 错误。
    - 断言状态和事件内容为 "LLM调用失败"。
    """
    state = {
        INITIAL_MATERIAL_KEY: "素材",
        INITIAL_REQUIREMENTS_KEY: "要求",
        INITIAL_SCORING_CRITERIA_KEY: "标准"
    }
    ctx = DummyContext(state)
    # mock 的 LLM client，抛出异常
    with mock.patch("composer_agent.composer_service.agents.draft_writer.get_llm_client", return_value=ErrorMockLlmClient()):
        agent = DraftWriter()
        session, invoc_context = make_adk_context(agent, state, invocation_id="test_case_2")
        events = []
        async for event in agent.run_async(invoc_context):
            events.append(event)
        # 检查异常分支
        assert session.state[CURRENT_DRAFT_KEY].startswith("LLM调用失败")
        assert events[0].content.parts[0].text.startswith("LLM调用失败")
        # 检查状态写入为空字符串 - 错误！异常时状态应为错误信息
        # assert session.state[CURRENT_DRAFT_KEY] == ""
        assert session.state[CURRENT_DRAFT_KEY].startswith("LLM调用失败")

@pytest.mark.asyncio
async def test_draft_writer_missing_inputs(monkeypatch):
    """
    用例说明：
    - 测试 DraftWriter 在输入缺失时，Prompt 仍能生成，LLM 返回空内容，状态和事件内容也为空字符串。
    - mock 的 LLM client 返回空字符串，模拟 LLM 正常响应但无内容。
    - 断言状态和事件内容均为空字符串。
    """
    state = {}
    ctx = DummyContext(state)
    prompts = {}
    # mock 的 LLM client，返回空字符串
    mock_llm = MockLlmClient("")
    with mock.patch("composer_agent.composer_service.agents.draft_writer.get_llm_client", return_value=mock_llm):
        agent = DraftWriter()
        session, invoc_context = make_adk_context(agent, state, invocation_id="test_case_3")
        events = []
        async for event in agent.run_async(invoc_context):
            events.append(event)
        # 检查 prompt 构建（即使输入缺失也能生成）
        assert "素材" in mock_llm.captured_request.contents[0].parts[0].text or "" == mock_llm.captured_request.contents[0].parts[0].text
        # 检查状态写入为空字符串
        assert session.state[CURRENT_DRAFT_KEY] == ""
        assert events[0].content.parts[0].text == ""
 