from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent
from google.adk.tools import FunctionTool
from pydantic import PrivateAttr

from composer_service.agents.draft_writer import DraftWriter
from composer_service.agents.scorer import Scorer

from composer_service.tools.check_initial_data import check_initial_data
from composer_service.tools.save_draft_result import save_draft_result
from composer_service.tools.save_score import save_score
from composer_service.tools.check_progress import check_progress
from composer_service.tools.get_final_draft import get_final_draft

# 通用ToolAgent实现
class ToolAgent(BaseAgent):
    _func: callable = PrivateAttr()

    def __init__(self, name, func, description=None):
        super().__init__(name=name, description=description or func.__doc__)
        self._func = func

    async def _run_async_impl(self, ctx):
        result = self._func(ctx)
        yield result

# 包装所有工具为Agent
check_initial_data_agent = ToolAgent("check_initial_data", check_initial_data)
save_draft_result_agent = ToolAgent("save_draft_result", save_draft_result)
save_score_agent = ToolAgent("save_score", save_score)
check_progress_agent = ToolAgent("check_progress", check_progress)
get_final_draft_agent = ToolAgent("get_final_draft", get_final_draft)

# LlmAgent 实例
draft_writer_agent = DraftWriter()
scorer_agent = Scorer()

# 循环体：严格线性，完全按Mermaid图
loop_agent = LoopAgent(
    name="composer_loop_agent",
    description="循环写稿-保存-评分-保存-进度检查",
    sub_agents=[
        draft_writer_agent,
        save_draft_result_agent,
        scorer_agent,
        save_score_agent,
        check_progress_agent,
    ],
    max_iterations=3,
)

# 主流程：严格线性，完全按Mermaid图
root_agent = SequentialAgent(
    name="composer_service_agent",
    description="主流程：初始检查->循环优化->输出最终稿",
    sub_agents=[
        check_initial_data_agent,
        loop_agent,
        get_final_draft_agent,
    ],
)
