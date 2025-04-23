import pytest
from composer_service.tools.save_draft_result import save_draft_result
from composer_service.tools.constants import CURRENT_DRAFT_KEY

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

@pytest.mark.parametrize("content,expected_status", [
    ("一篇稿件内容", "success"),
    ("  有效内容  ", "success"),
    ("", "error"),
    ("   ", "error"),
    (None, "error"),
    (123, "error"),
])
def test_save_draft_result_basic(content, expected_status):
    ctx = DummyContext()
    result = save_draft_result(content, ctx)
    assert result["status"] == expected_status
    if expected_status == "success":
        assert ctx.state[CURRENT_DRAFT_KEY] == content
    else:
        assert CURRENT_DRAFT_KEY not in ctx.state

def test_save_draft_result_overwrite():
    ctx = DummyContext({CURRENT_DRAFT_KEY: "旧稿件"})
    result = save_draft_result("新稿件", ctx)
    assert result["status"] == "success"
    assert ctx.state[CURRENT_DRAFT_KEY] == "新稿件" 