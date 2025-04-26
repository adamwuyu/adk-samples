import logging
from typing import Any, Dict, Union
from .constants import (
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

logger = logging.getLogger(__name__)

# 按键名定义类型验证
TYPE_VALIDATORS: Dict[str, Union[type, tuple]] = {
    INITIAL_MATERIAL_KEY: str,
    INITIAL_REQUIREMENTS_KEY: str,
    INITIAL_SCORING_CRITERIA_KEY: str,
    CURRENT_DRAFT_KEY: str,
    CURRENT_SCORE_KEY: int,
    CURRENT_FEEDBACK_KEY: str,
    SCORE_THRESHOLD_KEY: int,
    ITERATION_COUNT_KEY: int,
    IS_COMPLETE_KEY: bool,
}


class StateManager:
    """
    状态管理器，封装对 context.state 的读写与类型验证。
    """

    def __init__(self, context):
        """
        初始化状态管理器，context 只需有 .state 属性。
        """
        self.state = context.state

    def get(self, key: str, default: Any = None) -> Any:
        """
        读取状态值，返回 default 如果键不存在。
        """
        value = self.state.get(key, default)
        logger.debug(f"Get state: {key}={value}")
        return value

    def set(self, key: str, value: Any) -> bool:
        """
        设置状态值，带类型验证，返回是否写入成功。
        """
        expected = TYPE_VALIDATORS.get(key)
        if expected and not isinstance(value, expected):
            logger.error(f"Type validation failed for key={key}, expected={expected}, got={type(value)}")
            return False
        self.state[key] = value
        logger.debug(f"Set state: {key}={value}")
        return True

    def update(self, values: Dict[str, Any]) -> Dict[str, bool]:
        """
        批量更新状态值，返回每个键的更新结果。
        """
        results: Dict[str, bool] = {}
        for k, v in values.items():
            results[k] = self.set(k, v)
        return results 