import logging
from types import SimpleNamespace
from google.adk.agents import LlmAgent
from google.adk.models.llm_request import LlmRequest
from google.genai.types import Content, Part, GenerateContentConfig
from composer_service.tools.constants import (
    CURRENT_DRAFT_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
)
# 从配置文件导入 Prompt 模板和 Agent 指令
from .scorer_config import SCORING_PROMPT_TEMPLATE, SCORER_AGENT_INSTRUCTION
from composer_service.llm.client import get_llm_client

logger = logging.getLogger(__name__)

# 评分 Prompt 模板 (已移动到 scorer_config.py)
# SCORING_PROMPT_TEMPLATE = ... (代码省略)

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
        # 使用配置文件中的指令，并格式化插入实际的 state keys
        instruction = SCORER_AGENT_INSTRUCTION.format(
            draft_key=CURRENT_DRAFT_KEY,
            criteria_key=INITIAL_SCORING_CRITERIA_KEY
        )
        super().__init__(
            name="Scorer",
            instruction=instruction,
        )

    async def _run_async_impl(self, ctx):
        state = ctx.session.state
        draft = state.get(CURRENT_DRAFT_KEY, "")
        criteria = state.get(INITIAL_SCORING_CRITERIA_KEY, "")
        # 使用导入的 Prompt 模板
        prompt = SCORING_PROMPT_TEMPLATE.format(
            draft=draft,
            scoring_criteria=criteria
        )
        logger.info(f"[Scorer] 调用 LLM 评分，Prompt 预览: {prompt[:60]}...")
        llm_client = get_llm_client()
        try:
            # 构造 LlmRequest，并提供空的 GenerateContentConfig
            config = GenerateContentConfig()
            llm_request = LlmRequest(contents=[Content(parts=[Part(text=prompt)])], config=config) 
            
            # 使用 generate_content_async 并获取第一个响应
            resp_text = "" # 初始化为空字符串
            async for resp_chunk in llm_client.generate_content_async(llm_request):
                # 根据实际返回结构提取文本: resp_chunk.content.parts[0].text
                if (
                    resp_chunk
                    and resp_chunk.content
                    and resp_chunk.content.parts
                    and resp_chunk.content.parts[0].text
                ):
                    resp_text = resp_chunk.content.parts[0].text
                    # 假设我们只需要第一个响应块的文本
                    break 
            
            # # 如果循环结束都没有获取到响应文本 (注释掉这段，允许空响应)
            # if not resp_text:
            #     raise ValueError("LLM did not return any text content.")
            
            # 解析分数和反馈 (即使 resp_text 为空，解析函数也能处理)
            score, feedback = self._parse_score_and_feedback(resp_text)
            logger.info(f"[Scorer] LLM 返回分数: {score}, 反馈: {feedback}")
        except Exception as e:
            logger.error(f"[Scorer] LLM 调用或解析异常: {e}", exc_info=True)
            score = 0
            feedback = f"LLM调用失败: {e}"
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