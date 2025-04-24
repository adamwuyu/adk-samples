from google.adk.agents import SequentialAgent, LoopAgent
from .agents_registry import draft_writer_agent, scorer_agent
from .tools_registry import (
    check_initial_data_agent,
    save_draft_result_agent,
    save_score_agent,
    check_progress_agent,
    get_final_draft_agent,
)

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

root_agent = SequentialAgent(
    name="composer_service_agent",
    description="主流程：初始检查->循环优化->输出最终稿",
    sub_agents=[
        check_initial_data_agent,
        loop_agent,
        get_final_draft_agent,
    ],
) 