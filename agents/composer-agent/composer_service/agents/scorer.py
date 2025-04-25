import logging
from types import SimpleNamespace
from google.adk.agents import LlmAgent
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)
from composer_service.llm.client import get_llm_client

logger = logging.getLogger(__name__)

# 评分 Prompt 模板
SCORING_PROMPT_TEMPLATE = """
你是一位专业文稿评审，需要根据评分标准对以下文稿进行评估。

## 评分标准
{scoring_criteria}

## 待评文稿
{draft}

请按照以下格式进行评估：

分数: <0-100的整数>
反馈: <简明扼要的评价和建议>
"""

# 递归包装 dict 为 SimpleNamespace，actions 字段单独处理
def wrap_event(item):
    if isinstance(item, dict):
        actions = item.get("actions", {})
        wrapped = SimpleNamespace(
            actions=SimpleNamespace(**actions),
            **{k: v for k, v in item.items() if k != "actions"}
        )
        return wrapped
    return item

class Scorer(LlmAgent):
    def __init__(self):
        super().__init__(
            name="Scorer",
            instruction=f"请根据 state['{CURRENT_DRAFT_KEY}']、state['{INITIAL_SCORING_CRITERIA_KEY}'] 评分并给出反馈。",
        )

    async def _run_async_impl(self, ctx):
        state = ctx.session.state
        draft = state.get(CURRENT_DRAFT_KEY, "")
        criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, "")
        prompt = SCORING_PROMPT_TEMPLATE.format(
            draft=draft,
            scoring_criteria=criteria
        )
        logger.info(f"[Scorer] 调用 LLM 评分，Prompt 预览: {prompt[:60]}...")
        llm_client = get_llm_client()
        try:
            resp = await llm_client(prompt)
            # 解析分数和反馈
            score, feedback = self._parse_score_and_feedback(resp)
            logger.info(f"[Scorer] LLM 返回分数: {score}, 反馈: {feedback}")
        except Exception as e:
            logger.error(f"[Scorer] LLM 调用异常: {e}", exc_info=True)
            score = 0
            feedback = "LLM调用失败"
        state[CURRENT_SCORE_KEY] = score
        state[CURRENT_FEEDBACK_KEY] = feedback
        result = {
            "event": "scoring_finished",
            "score": score,
            "feedback": feedback,
            "actions": {"escalate": False}
        }
        event = wrap_event(result)
        logger.debug(f"[Scorer] yield type: {type(event)}, value: {event}")
        yield event

    def _parse_score_and_feedback(self, resp):
        """
        解析 LLM 返回的评分和反馈。
        支持格式：
        分数: 95\n反馈: xxx
        或其它常见变体。
        """
        text = resp if isinstance(resp, str) else str(resp)
        import re
        score = 0
        feedback = ""
        # 尝试提取分数
        match = re.search(r"分数[:：]?\s*(\d{1,3})", text)
        if match:
            try:
                score = int(match.group(1))
            except Exception:
                score = 0
        # 尝试提取反馈
        match2 = re.search(r"反馈[:：]?\s*(.+)", text)
        if match2:
            feedback = match2.group(1).strip()
        return score, feedback 