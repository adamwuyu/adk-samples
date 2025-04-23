import pytest
from composer_service.tools.save_score import save_score
from composer_service.tools.constants import CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

@pytest.mark.parametrize("score,feedback,expected_status", [
    (8.8, "很棒的稿件！", "success"),
    (0, "合格", "success"),
    ("A", "合格", "error"),
    (None, "合格", "error"),
    (8.8, "", "error"),
    (8.8, None, "error"),
    (8.8, 123, "error"),
])
def test_save_score_basic(score, feedback, expected_status):
    ctx = DummyContext()
    result = save_score(score, feedback, ctx)
    assert result["status"] == expected_status
    if expected_status == "success":
        assert ctx.state[CURRENT_SCORE_KEY] == score
        assert ctx.state[CURRENT_FEEDBACK_KEY] == feedback
    else:
        assert CURRENT_SCORE_KEY not in ctx.state or ctx.state[CURRENT_SCORE_KEY] != score
        assert CURRENT_FEEDBACK_KEY not in ctx.state or ctx.state[CURRENT_FEEDBACK_KEY] != feedback

def test_save_score_overwrite():
    ctx = DummyContext({CURRENT_SCORE_KEY: 1.0, CURRENT_FEEDBACK_KEY: "旧反馈"})
    result = save_score(9.9, "新反馈", ctx)
    assert result["status"] == "success"
    assert ctx.state[CURRENT_SCORE_KEY] == 9.9
    assert ctx.state[CURRENT_FEEDBACK_KEY] == "新反馈" 