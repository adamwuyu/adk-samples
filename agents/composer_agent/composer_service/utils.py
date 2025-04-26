import logging
from types import SimpleNamespace # 保留以防万一，但不再用于主要转换
from google.adk.events.event import Event
from google.genai.types import Content, Part
# from google.adk.agents.invocation_context import InvocationContext # 可能需要

logger = logging.getLogger(__name__)

def wrap_event(result: dict, agent_name: str, invocation_id: str) -> Event:
    """将 Agent 或工具返回的 dict 包装成 ADK Event 对象"""

    # 优化 text_content 提取：优先 draft/feedback，其次 status，最后空字符串
    text_content = result.get("draft") or result.get("feedback") or result.get("status") or ""
    if not isinstance(text_content, str):
        text_content = str(text_content) # 确保是字符串

    # 构造 ADK Event 对象
    event = Event(
        author=agent_name,
        invocation_id=invocation_id,
        content=Content(parts=[Part(text=text_content)]),
        # actions 字段需要特殊处理，这里暂时忽略，或根据 EventActions 结构填充
        # actions=EventActions(...)
    )
    logger.debug(f"[wrap_event] created Event for {agent_name}: {event.id}")
    return event

# 注意：调用 wrap_event 的地方 (DraftWriter, Scorer) 需要修改，传递 agent_name 和 invocation_id
# 例如： event = wrap_event(result, self.name, ctx.invocation_id) 