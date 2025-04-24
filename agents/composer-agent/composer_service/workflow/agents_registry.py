from google.adk.agents import BaseAgent
from pydantic import PrivateAttr
from composer_service.agents.draft_writer import DraftWriter
from composer_service.agents.scorer import Scorer

# 通用ToolAgent实现
def make_tool_agent(name, func, description=None):
    class ToolAgent(BaseAgent):
        _func: callable = PrivateAttr()
        def __init__(self):
            super().__init__(name=name, description=description or func.__doc__)
            self._func = func
        async def _run_async_impl(self, ctx):
            result = self._func(ctx)
            yield result
    return ToolAgent()

draft_writer_agent = DraftWriter()
scorer_agent = Scorer() 