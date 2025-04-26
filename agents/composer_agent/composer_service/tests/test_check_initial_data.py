import pytest
from ..tools.check_initial_data import check_initial_data
from ..tools.constants import (
    INITIAL_MATERIAL_KEY,
    INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY,
)

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

# 这里用pytest的参数化功能，一次性测试多组输入和期望输出
# parametrize的第一个参数是参数名（必须和测试函数参数名一致），第二个参数是参数组列表
# pytest会自动用每组(state, expected)调用一次test_check_initial_data函数
@pytest.mark.parametrize("state,expected", [
    # 全部存在
    ({
        INITIAL_MATERIAL_KEY: "mat",
        INITIAL_REQUIREMENTS_KEY: "req",
        INITIAL_SCORING_CRITERIA_KEY: "cri",
    }, {"status": "ready"}),
    # 缺一项
    ({
        INITIAL_MATERIAL_KEY: "mat",
        INITIAL_REQUIREMENTS_KEY: "req",
    }, {"status": "missing_data", "missing_keys": [INITIAL_SCORING_CRITERIA_KEY]}),
    # 缺两项
    ({
        INITIAL_MATERIAL_KEY: "mat",
    }, {"status": "missing_data", "missing_keys": [INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY]}),
    # 全部缺失
    ({}, {"status": "missing_data", "missing_keys": [INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY]}),
    # 存在但为空字符串
    ({
        INITIAL_MATERIAL_KEY: "",
        INITIAL_REQUIREMENTS_KEY: "",
        INITIAL_SCORING_CRITERIA_KEY: "",
    }, {"status": "missing_data", "missing_keys": [INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY]}),
])
def test_check_initial_data(state, expected):
    # pytest会自动用每组(state, expected)调用本函数，实现批量测试
    ctx = DummyContext(state)
    result = check_initial_data(ctx)
    # 断言状态是否和预期一致
    assert result["status"] == expected["status"]
    # 如果缺数据，断言缺失的key集合是否和预期一致
    if result["status"] == "missing_data":
        assert set(result["missing_keys"]) == set(expected["missing_keys"]) 