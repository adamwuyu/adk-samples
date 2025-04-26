import logging
from google.adk.agents import BaseAgent, LlmAgent
from pydantic import PrivateAttr
from ..agents.draft_writer import DraftWriter
from ..agents.scorer import Scorer
from ..tools.check_initial_data import check_initial_data
from ..tools.check_progress import check_progress
from ..tools.save_draft_result import save_draft_result
from ..tools.save_score import save_score
from google.adk.tools import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from types import SimpleNamespace
import collections.abc
import asyncio
from ..utils import wrap_event
from google.adk.events.event import Event

logger = logging.getLogger(__name__)

# 通用ToolAgent实现
def make_tool_agent(name, func, description=None):
    class ToolAgent(BaseAgent):
        _func: callable = PrivateAttr()
        def __init__(self):
            super().__init__(name=name, description=description or func.__doc__)
            self._func = func
        async def _run_async_impl(self, ctx):
            invocation_id = getattr(ctx, 'invocation_id', '') # 安全获取 invocation_id
            if isinstance(ctx, InvocationContext):
                tool_ctx = ToolContext(invocation_context=ctx)
            else:
                tool_ctx = ctx
            result = self._func(tool_ctx)
            # 如果是 awaitable，等待其完成
            if asyncio.iscoroutine(result):
                await result
            # Yield 一个空的 Event 对象，包含 author 和 invocation_id
            yield Event(author=self.name, invocation_id=invocation_id)
    return ToolAgent()

draft_writer_agent = DraftWriter()
scorer_agent = Scorer() 