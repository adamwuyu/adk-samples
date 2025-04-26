import pytest
from ..tools.check_progress import check_progress
from ..tools.constants import (
    CURRENT_SCORE_KEY,
    SCORE_THRESHOLD_KEY,
    ITERATION_COUNT_KEY,
)

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

@pytest.mark.parametrize("state,expected", [
    # 分数达标，立即终止
    ({CURRENT_SCORE_KEY: 90, SCORE_THRESHOLD_KEY: 80, ITERATION_COUNT_KEY: 2, "max_iterations": 5},
     {"status": "done", "reason": "score_passed", "actions": {"escalate": True}}),
    # 达到最大轮数，终止
    ({CURRENT_SCORE_KEY: 70, SCORE_THRESHOLD_KEY: 80, ITERATION_COUNT_KEY: 5, "max_iterations": 5},
     {"status": "done", "reason": "max_iterations", "actions": {"escalate": True}}),
    # 未达分数且未超轮数，继续
    ({CURRENT_SCORE_KEY: 70, SCORE_THRESHOLD_KEY: 80, ITERATION_COUNT_KEY: 2, "max_iterations": 5},
     {"status": "continue", "actions": {"escalate": False}}),
])
def test_check_progress(state, expected):
    ctx = DummyContext(state)
    result = check_progress(ctx)
    assert result["status"] == expected["status"]
    assert result["actions"]["escalate"] == expected["actions"]["escalate"]
    if result["status"] == "done":
        assert result["reason"] == expected["reason"] 