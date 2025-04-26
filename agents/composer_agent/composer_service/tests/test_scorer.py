import pytest
from unittest import mock
from composer_service.agents.scorer_config import SCORING_PROMPT_TEMPLATE, SCORER_AGENT_INSTRUCTION
from composer_service.agents.scorer import Scorer
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)
from .lib import make_adk_context, create_mock_response_chunk, MockLlmClient, ErrorMockLlmClient

@pytest.mark.asyncio
async def test_scorer_llm_prompt_and_state(monkeypatch):
    """
    测试 Scorer 能正确构建评分 Prompt，调用 LLM 并写入分数和反馈。
    同时检查 Agent instruction 和 Prompt 的精确性。
    """
    draft_text = "一篇好稿件ABCDEFGH"
    criteria_text = "标准XYZ123"
    state = {
        CURRENT_DRAFT_KEY: draft_text,
        INITIAL_SCORING_CRITERIA_KEY: criteria_text
    }
    # 使用新的 Mock 类
    mock_llm = MockLlmClient("""分数: 95
反馈: 结构清晰，表达流畅。""")
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=mock_llm): # 直接返回实例
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)

        # 检查 Agent instruction 是否正确设置
        expected_instruction = SCORER_AGENT_INSTRUCTION.format(
            draft_key=CURRENT_DRAFT_KEY,
            criteria_key=INITIAL_SCORING_CRITERIA_KEY
        )
        assert agent.instruction == expected_instruction

        events = []
        async for event in agent.run_async(ctx):
            events.append(event)

        # 检查 prompt 构建的精确性
        expected_prompt = SCORING_PROMPT_TEMPLATE.format(
            draft=draft_text,
            scoring_criteria=criteria_text
        )
        # 从捕获的 request 中获取 prompt
        assert mock_llm.captured_request is not None, "LLM Client 未被调用"
        captured_prompt_text = mock_llm.captured_request.contents[0].parts[0].text
        assert captured_prompt_text == expected_prompt

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
    # 使用模拟抛出异常的 Mock 类
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=ErrorMockLlmClient()): # 直接返回实例
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        # 检查异常分支
        assert session.state[CURRENT_SCORE_KEY] == 0
        assert session.state[CURRENT_FEEDBACK_KEY].startswith("LLM调用失败")
        assert getattr(events[0], "score", None) == 0
        assert getattr(events[0], "feedback", None).startswith("LLM调用失败")
        assert getattr(events[0], "event", None) == "scoring_finished"

@pytest.mark.asyncio
async def test_scorer_missing_inputs(monkeypatch):
    """
    测试缺少输入时，Prompt 仍能生成，LLM 返回空内容，分数为0，反馈为空字符串。
    """
    state = {}
    # prompts 字典不再需要，因为 prompt 是通过 captured_request 检查的
    # prompts = {}

    # 使用之前的 MockLlmClient，但传入空字符串
    mock_llm = MockLlmClient("")
    with mock.patch("composer_service.agents.scorer.get_llm_client", return_value=mock_llm): # 直接返回实例
        agent = Scorer()
        session, ctx = make_adk_context(agent, state)
        events = []
        async for event in agent.run_async(ctx):
            events.append(event)
        # 检查 prompt 构建 (现在检查捕获的 request)
        expected_prompt = SCORING_PROMPT_TEMPLATE.format(
            draft="", # 缺失输入时 draft 为空
            scoring_criteria="" # 缺失输入时 criteria 为空
        )
        assert mock_llm.captured_request is not None, "LLM Client 未被调用"
        captured_prompt_text = mock_llm.captured_request.contents[0].parts[0].text
        assert captured_prompt_text == expected_prompt

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