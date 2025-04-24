import pytest
from google.adk.agents import SequentialAgent, LoopAgent
from composer_service.workflow import (
    root_agent,
    loop_agent,
    ToolAgent,
    check_initial_data_agent,
    save_draft_result_agent,
    save_score_agent,
    check_progress_agent,
    get_final_draft_agent,
)
from composer_service.agents.draft_writer import DraftWriter
from composer_service.agents.scorer import Scorer

def test_tool_agent_type():
    # 所有工具节点都应为ToolAgent
    assert isinstance(check_initial_data_agent, ToolAgent)
    assert isinstance(save_draft_result_agent, ToolAgent)
    assert isinstance(save_score_agent, ToolAgent)
    assert isinstance(check_progress_agent, ToolAgent)
    assert isinstance(get_final_draft_agent, ToolAgent)

def test_loop_agent_structure():
    # 验证LoopAgent严格线性结构
    assert isinstance(loop_agent, LoopAgent)
    assert loop_agent.name == "composer_loop_agent"
    assert getattr(loop_agent, 'max_iterations', None) == 3
    subs = loop_agent.sub_agents
    # 顺序严格：DraftWriter, save_draft_result, Scorer, save_score, check_progress
    assert isinstance(subs[0], DraftWriter)
    assert subs[1] is save_draft_result_agent
    assert isinstance(subs[2], Scorer)
    assert subs[3] is save_score_agent
    assert subs[4] is check_progress_agent

def test_root_agent_structure():
    # 验证SequentialAgent严格线性结构
    assert isinstance(root_agent, SequentialAgent)
    assert root_agent.name == "composer_service_agent"
    subs = root_agent.sub_agents
    # 顺序严格：check_initial_data, loop_agent, get_final_draft
    assert subs[0] is check_initial_data_agent
    assert subs[1] is loop_agent
    assert subs[2] is get_final_draft_agent 