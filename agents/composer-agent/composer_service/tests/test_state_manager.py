import pytest

from composer_service.tools.state_manager import StateManager
from composer_service.tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY,
    CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY,
    SCORE_THRESHOLD_KEY,
    ITERATION_COUNT_KEY,
    IS_COMPLETE_KEY,
)


class DummyContext:
    """
    简易上下文，包含 .state 属性用于测试 StateManager。
    """
    def __init__(self):
        self.state = {}


@pytest.fixture
def tool_context():
    return DummyContext()


def test_get_default(tool_context):
    sm = StateManager(tool_context)
    # 默认值应返回
    assert sm.get("nonexistent_key", "default") == "default"


def test_set_and_get_valid(tool_context):
    sm = StateManager(tool_context)
    # 设置并读取
    assert sm.set(INITIAL_MATERIAL_KEY, "initial content")
    assert sm.get(INITIAL_MATERIAL_KEY) == "initial content"


def test_set_invalid_type(tool_context):
    sm = StateManager(tool_context)
    # 将 float 类型值设置为 str键应失败
    assert not sm.set(CURRENT_SCORE_KEY, "not a number")


def test_update_all_success(tool_context):
    sm = StateManager(tool_context)
    results = sm.update({
        INITIAL_REQUIREMENTS_KEY: "req",
        CURRENT_SCORE_KEY: 9.5,
    })
    assert results[INITIAL_REQUIREMENTS_KEY] is True
    assert results[CURRENT_SCORE_KEY] is True
    assert sm.get(INITIAL_REQUIREMENTS_KEY) == "req"
    assert sm.get(CURRENT_SCORE_KEY) == 9.5


def test_update_partial_failure(tool_context):
    sm = StateManager(tool_context)
    results = sm.update({
        SCORE_THRESHOLD_KEY: "threshold",
        IS_COMPLETE_KEY: False,
    })
    assert results[SCORE_THRESHOLD_KEY] is False
    assert results[IS_COMPLETE_KEY] is True
    # 失败的 key 不应写入
    assert sm.get(SCORE_THRESHOLD_KEY) is None
    # 成功写入的 key 应存在
    assert sm.get(IS_COMPLETE_KEY) is False 

@pytest.fixture
def tool_context_with_initial_score(tool_context):
    # 假设 tool_context 是已有的 fixture
    tool_context.state[SCORE_THRESHOLD_KEY] = 0.8
    return tool_context

def test_update_partial_failure_preserves_existing(tool_context_with_initial_score):
    sm = StateManager(tool_context_with_initial_score)
    results = sm.update({
        SCORE_THRESHOLD_KEY: "threshold",  # 错误类型
        IS_COMPLETE_KEY: False,            # 正确类型
    })
    assert results[SCORE_THRESHOLD_KEY] is False
    assert results[IS_COMPLETE_KEY] is True
    # 失败的 key 应保留原值
    assert sm.get(SCORE_THRESHOLD_KEY) == 0.8
    # 成功写入的 key 应存在
    assert sm.get(IS_COMPLETE_KEY) is False