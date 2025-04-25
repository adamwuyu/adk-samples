import pytest
from unittest import mock
from composer_service.agents.scorer import Scorer
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)
from .lib import make_adk_context

@pytest.mark.asyncio
async def test_scorer_llm_prompt_and_state(monkeypatch):
    """
    测试 Scorer 能正确构建评分 Prompt，调用 LLM 并写入分数和反馈。
    """
    state = {
        CURRENT_DRAFT_KEY: "一篇好稿件ABCDEFGH",
        INITIAL_SCORING_CRITERIA_KEY: "标准XYZ123"
    }
    prompts = {}
    class DummyLlm:
        async def __call__(self, prompt):
            prompts['content'] = prompt
            return "分数: 95\n反馈: 结构清晰，表达流畅。"
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=DummyLlm()):
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        # 检查 prompt 构建
        assert "一篇好稿件ABCDEFGH" in prompts['content']
        assert "标准XYZ123" in prompts['content']
        # 检查状态写入
        assert session.state[CURRENT_SCORE_KEY] == 95
        assert session.state[CURRENT_FEEDBACK_KEY] == "结构清晰，表达流畅。"
        # 检查事件内容
        assert getattr(events[0], "score", None) == 95
        assert getattr(events[0], "feedback", None) == "结构清晰，表达流畅。"
        assert getattr(events[0], "event", None) == "scoring_finished"

@pytest.mark.asyncio
async def test_scorer_llm_exception(monkeypatch):
    """
    测试 LLM 调用异常时，Scorer 能捕获并记录异常，且写入错误提示。
    """
    state = {
        CURRENT_DRAFT_KEY: "A",
        INITIAL_SCORING_CRITERIA_KEY: "B"
    }
    class DummyLlm:
        async def __call__(self, prompt):
            raise RuntimeError("LLM API Error")
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=DummyLlm()):
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        # 检查异常分支
        assert session.state[CURRENT_SCORE_KEY] == 0
        assert session.state[CURRENT_FEEDBACK_KEY] == "LLM调用失败"
        assert getattr(events[0], "score", None) == 0
        assert getattr(events[0], "feedback", None) == "LLM调用失败"
        assert getattr(events[0], "event", None) == "scoring_finished"

@pytest.mark.asyncio
async def test_scorer_missing_inputs(monkeypatch):
    """
    测试缺少输入时，Prompt 仍能生成，LLM 返回空内容，分数为0，反馈为空字符串。
    """
    state = {}
    prompts = {}
    class DummyLlm:
        async def __call__(self, prompt):
            prompts['content'] = prompt
            return ""
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=DummyLlm()):
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        # 检查 prompt 构建
        assert "" in prompts['content']
        # 检查状态写入
        assert session.state[CURRENT_SCORE_KEY] == 0
        assert session.state[CURRENT_FEEDBACK_KEY] == ""
        assert getattr(events[0], "score", None) == 0
        assert getattr(events[0], "feedback", None) == ""
        assert getattr(events[0], "event", None) == "scoring_finished"

@pytest.mark.parametrize("llm_resp, expected_score, expected_feedback", [
    ("分数: 95\n反馈: 结构清晰，表达流畅。", 95, "结构清晰，表达流畅。"), # 正常格式
    ("分数: 70\n反馈：内容尚可", 70, "内容尚可"), # 中文冒号
    ("分数: 100\n反馈:完美", 100, "完美"), # 无空格
    ("分数: 88", 88, ""), # 只有分数
    ("反馈: 内容需要补充", 0, "内容需要补充"), # 只有反馈 (默认分数0)
    ("这是一篇很好的稿件，分数：90\n反馈：可以再深入一些。", 90, "可以再深入一些。"), # 分数不在行首
    ("乱七八糟的回复", 0, ""), # 格式异常
    ("", 0, ""), # 空字符串
    (None, 0, ""), # None 值 (转换为字符串测试)
    (123, 0, ""), # 非字符串类型 (转换为字符串测试)
])
def test_parse_score_and_feedback(llm_resp, expected_score, expected_feedback):
    """
    测试 _parse_score_and_feedback 方法能正确解析不同格式的 LLM 返回。
    """
    scorer = Scorer()
    score, feedback = scorer._parse_score_and_feedback(llm_resp)
    assert score == expected_score
    assert feedback == expected_feedback 