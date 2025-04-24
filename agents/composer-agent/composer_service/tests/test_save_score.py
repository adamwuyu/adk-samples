import pytest
from composer_service.tools.save_score import save_score
from composer_service.tools.constants import CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

@pytest.mark.parametrize("score,feedback,expected_status", [
    (88, "很棒的稿件！", "success"),
    (0, "合格", "success"),
    ("A", "合格", "error"),
    (None, "合格", "error"),
    (88.8, "", "error"),
    (88.8, None, "error"),
    (88.8, 123, "error"),
])
def test_save_score_basic(score, feedback, expected_status):
    ctx = DummyContext()
    if score is not None:
        ctx.state[CURRENT_SCORE_KEY] = score
    if feedback is not None:
        ctx.state[CURRENT_FEEDBACK_KEY] = feedback
    result = save_score(ctx)
    assert getattr(result, "status", result["status"]) == expected_status
    if expected_status == "success":
        assert ctx.state[CURRENT_SCORE_KEY] == score
        assert ctx.state[CURRENT_FEEDBACK_KEY] == feedback
    else:
        v1 = ctx.state.get(CURRENT_SCORE_KEY, None)
        assert not isinstance(v1, int)

def test_save_score_overwrite():
    ctx = DummyContext({CURRENT_SCORE_KEY: 10, CURRENT_FEEDBACK_KEY: "旧反馈"})
    ctx.state[CURRENT_SCORE_KEY] = 99
    ctx.state[CURRENT_FEEDBACK_KEY] = "新反馈"
    result = save_score(ctx)
    assert getattr(result, "status", result["status"]) == "success"
    assert ctx.state[CURRENT_SCORE_KEY] == 99
    assert ctx.state[CURRENT_FEEDBACK_KEY] == "新反馈" 