import pytest
from types import SimpleNamespace
from unittest import mock
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
    class DummyLlm:
        async def __call__(self, prompt):
            prompts['content'] = prompt
            return "LLM生成的稿件内容"
    # 用 mock.patch 替换 get_llm_client，确保 DraftWriter 不会调用真实 LLM
    with mock.patch("composer_service.agents.draft_writer.get_llm_client", return_value=DummyLlm()):
        agent = DraftWriter()
        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)
        # 检查 prompt 构建
        assert "素材内容ABCDEFGH" in prompts['content']
        assert "要求内容12345678" in prompts['content']
        assert "评分标准XYZ" in prompts['content']
        # 检查状态写入
        assert state[CURRENT_DRAFT_KEY] == "LLM生成的稿件内容"
        # 检查事件内容
        assert getattr(events[0], "draft", None) == "LLM生成的稿件内容"
        assert getattr(events[0], "event", None) == "draft_generated"

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
    class DummyLlm:
        async def __call__(self, prompt):
            raise RuntimeError("LLM API Error")
    with mock.patch("composer_service.agents.draft_writer.get_llm_client", return_value=DummyLlm()):
        agent = DraftWriter()
        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)
        # 检查异常分支
        assert state[CURRENT_DRAFT_KEY] == "LLM调用失败"
        assert getattr(events[0], "draft", None) == "LLM调用失败"
        assert getattr(events[0], "event", None) == "draft_generated"

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
    class DummyLlm:
        async def __call__(self, prompt):
            prompts['content'] = prompt
            return ""
    with mock.patch("composer_service.agents.draft_writer.get_llm_client", return_value=DummyLlm()):
        agent = DraftWriter()
        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)
        # 检查 prompt 构建（即使输入缺失也能生成）
        assert "素材" in prompts['content'] or "" == prompts['content']
        # 检查状态写入为空字符串
        assert state[CURRENT_DRAFT_KEY] == ""
        assert getattr(events[0], "draft", None) == ""
        assert getattr(events[0], "event", None) == "draft_generated" 