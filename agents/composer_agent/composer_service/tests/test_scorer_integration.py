import pytest
import os
from ..agents.scorer import Scorer
from ..tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)
from .lib import make_adk_context

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scorer_integration_real_llm():
    """
    集成测试：验证 Scorer Agent 与真实 LLM 的交互。
    需要设置 KINGDORA_BASE_URL 和 KINGDORA_API_KEY 环境变量。
    """
    kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
    kingdora_api_key = os.getenv("KINGDORA_API_KEY")
    if not kingdora_base_url or not kingdora_api_key:
        pytest.skip("未设置 KINGDORA_BASE_URL 或 KINGDORA_API_KEY，跳过 Scorer 集成测试")

    # 准备输入状态
    draft_text = "这是一篇关于人工智能的测试稿件，请评估其质量。"
    criteria_text = "评估标准：内容准确性、逻辑连贯性、语言流畅度。分数范围 0-100。"
    state = {
        CURRENT_DRAFT_KEY: draft_text,
        INITIAL_SCORING_CRITERIA_KEY: criteria_text,
        # 初始化预期会改变的状态键，以便观察变化
        CURRENT_SCORE_KEY: -1, # 使用一个明显不可能的值
        CURRENT_FEEDBACK_KEY: "<尚未评分>"
    }

    # 创建 Agent 和 Context
    agent = Scorer()
    session, ctx = make_adk_context(agent, state)

    # 运行 Agent
    events = []
    try:
        async for event in agent.run_async(ctx):
            events.append(event)
    except Exception as e:
        pytest.fail(f"Scorer Agent 在集成测试中抛出异常: {e}")

    # 断言状态更新
    final_score = session.state.get(CURRENT_SCORE_KEY)
    final_feedback = session.state.get(CURRENT_FEEDBACK_KEY)

    assert isinstance(final_score, int), f"预期分数为整数，实际为: {type(final_score)}"
    assert 0 <= final_score <= 100, f"预期分数在 0-100 之间，实际为: {final_score}"
    assert final_score != -1, "分数未被更新 (仍为初始值 -1)"

    assert isinstance(final_feedback, str), f"预期反馈为字符串，实际为: {type(final_feedback)}"
    assert final_feedback is not None and final_feedback != "", "反馈不应为空字符串"
    assert final_feedback != "<尚未评分>", "反馈未被更新 (仍为初始值 '<尚未评分>')"
    # 不对反馈内容做强断言，因为 LLM 输出不稳定
    print(f"\n--- Scorer Integration Test (Real LLM) ---")
    print(f"Draft: {draft_text}")
    print(f"Criteria: {criteria_text}")
    print(f"Score: {final_score}")
    print(f"Feedback: {final_feedback}")
    print(f"-----------------------------------------")

    # 断言事件
    assert len(events) == 1, f"预期只有一个事件，实际收到 {len(events)} 个"
    event = events[0]
    # assert getattr(event, 'event', None) == 'scoring_finished', "事件类型不匹配"
    # assert getattr(event, 'score', None) == final_score, "事件中的分数与状态不匹配"
    # assert getattr(event, 'feedback', None) == final_feedback, "事件中的反馈与状态不匹配"
    # 检查 event.content.text 是否包含了 feedback (更可靠的方式是检查 state)
    assert isinstance(event.content.parts[0].text, str)

    # === 新增的关键断言 ===
    # 检查是否因为 LLM 调用失败而导致测试"假通过"
    assert not (final_score == 0 and final_feedback == "LLM调用失败"), \
           "测试失败：LLM 调用失败，分数和反馈被设置为错误默认值。" 