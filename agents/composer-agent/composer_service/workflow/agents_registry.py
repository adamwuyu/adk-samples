import logging
from google.adk.agents import BaseAgent
from pydantic import PrivateAttr
from composer_service.agents.draft_writer import DraftWriter
from composer_service.agents.scorer import Scorer
from google.adk.tools import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from types import SimpleNamespace
import collections.abc
import asyncio

logger = logging.getLogger(__name__)

# 通用ToolAgent实现
def make_tool_agent(name, func, description=None):
    class ToolAgent(BaseAgent):
        _func: callable = PrivateAttr()
        def __init__(self):
            super().__init__(name=name, description=description or func.__doc__)
            self._func = func
        async def _run_async_impl(self, ctx):
            if isinstance(ctx, InvocationContext):
                tool_ctx = ToolContext(invocation_context=ctx)
            else:
                tool_ctx = ctx
            def wrap(item):
                logger.debug(f"[ToolAgent {name}] wrap input type: {type(item)} value: {item}")
                if isinstance(item, dict):
                    actions = item.get("actions", {})
                    wrapped = SimpleNamespace(
                        actions=SimpleNamespace(**actions),
                        **{k: v for k, v in item.items() if k != "actions"}
                    )
                    logger.debug(f"[ToolAgent {name}] wrap output type: {type(wrapped)} value: {wrapped}")
                    return wrapped
                return item
            result = self._func(tool_ctx)
            # 兼容异步生成器
            if isinstance(result, collections.abc.AsyncGenerator):
                async for item in result:
                    wrapped = wrap(item)
                    logger.debug(f"[ToolAgent {name}] yield type: {type(wrapped)} value: {wrapped}")
                    yield wrapped
            # 兼容同步生成器
            elif isinstance(result, collections.abc.Generator):
                for item in result:
                    wrapped = wrap(item)
                    logger.debug(f"[ToolAgent {name}] yield type: {type(wrapped)} value: {wrapped}")
                    yield wrapped
            # 兼容 awaitable
            elif asyncio.iscoroutine(result):
                item = await result
                wrapped = wrap(item)
                logger.debug(f"[ToolAgent {name}] yield type: {type(wrapped)} value: {wrapped}")
                yield wrapped
            # 兼容列表
            elif isinstance(result, list):
                for item in result:
                    wrapped = wrap(item)
                    logger.debug(f"[ToolAgent {name}] yield type: {type(wrapped)} value: {wrapped}")
                    yield wrapped
            else:
                wrapped = wrap(result)
                logger.debug(f"[ToolAgent {name}] yield type: {type(wrapped)} value: {wrapped}")
                yield wrapped
    return ToolAgent()

draft_writer_agent = DraftWriter()
scorer_agent = Scorer() 