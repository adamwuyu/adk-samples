"""状态管理工具，优化变量传递和数据验证。"""

import logging
from typing import Any, Dict, List, Optional, Union
from google.adk.tools.tool_context import ToolContext

from .logging_utils import log_state_operation

logger = logging.getLogger(__name__)

# 定义状态键名常量
INITIAL_MATERIAL_KEY = "initial_material"
INITIAL_REQUIREMENTS_KEY = "initial_requirements"
INITIAL_SCORING_CRITERIA_KEY = "initial_scoring_criteria"
CURRENT_DRAFT_KEY = "current_draft"
CURRENT_SCORE_KEY = "current_score"
CURRENT_FEEDBACK_KEY = "current_feedback"
SCORE_THRESHOLD_KEY = "score_threshold"
ITERATION_COUNT_KEY = "iteration_count"
IS_COMPLETE_KEY = "is_complete"

# 定义数据类型验证映射
TYPE_VALIDATORS = {
    INITIAL_MATERIAL_KEY: str,
    INITIAL_REQUIREMENTS_KEY: str,
    INITIAL_SCORING_CRITERIA_KEY: str,
    CURRENT_DRAFT_KEY: str,
    CURRENT_SCORE_KEY: float,
    CURRENT_FEEDBACK_KEY: str,
    SCORE_THRESHOLD_KEY: float,
    ITERATION_COUNT_KEY: int,
    IS_COMPLETE_KEY: bool
}

class StateManager:
    """状态管理器，提供安全的状态访问和验证。"""
    
    def __init__(self, tool_context: ToolContext):
        """
        初始化状态管理器
        
        Args:
            tool_context: ADK工具上下文
        """
        self.tool_context = tool_context
        self.state = tool_context.state
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        从状态获取值，附带日志记录
        
        Args:
            key: 状态键名
            default: 如果键不存在时的默认值
            
        Returns:
            存储的值或默认值
        """
        value = self.state.get(key, default)
        log_state_operation("read", key, value, 
                           {"exists": key in self.state, "type": type(value).__name__})
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置状态值，带类型验证和日志记录
        
        Args:
            key: 状态键名
            value: 要存储的值
            
        Returns:
            bool: 操作是否成功
        """
        # 输出更详细的日志
        logger.info(f"设置状态值: 键='{key}', 值类型={type(value).__name__}, 值长度={len(value) if hasattr(value, '__len__') else '不可计算'}")
        logger.info(f"状态对象类型: {type(self.state)}, 状态对象ID: {id(self.state)}")
        
        # 类型验证
        expected_type = TYPE_VALIDATORS.get(key)
        if expected_type and not isinstance(value, expected_type):
            logger.error(f"类型验证失败：键'{key}'预期类型{expected_type.__name__}，实际为{type(value).__name__}")
            return False
        
        # 写入前状态
        had_key = key in self.state
        logger.info(f"写入前状态: 键'{key}'存在={had_key}")
        
        # 写入状态
        self.state[key] = value
        
        # 验证写入
        if self.state.get(key) == value:
            log_state_operation("write", key, value, {"type": type(value).__name__})
            logger.info(f"键'{key}'写入成功，验证通过")
            return True
        else:
            logger.error(f"状态验证失败：键'{key}'的写入验证不匹配")
            return False
    
    def update(self, values: Dict[str, Any]) -> Dict[str, bool]:
        """
        批量更新多个状态值，带验证
        
        Args:
            values: 键值对字典
            
        Returns:
            Dict[str, bool]: 每个键的更新结果
        """
        results = {}
        for key, value in values.items():
            results[key] = self.set(key, value)
        
        return results
    
    def delete(self, key: str) -> bool:
        """
        删除状态中的键
        
        Args:
            key: 要删除的键名
            
        Returns:
            bool: 操作是否成功
        """
        if key in self.state:
            log_state_operation("delete", key, metadata={"exists": True})
            del self.state[key]
            return key not in self.state
        else:
            log_state_operation("delete", key, metadata={"exists": False})
            return True
    
    def validate_required_keys(self, required_keys: List[str]) -> Dict[str, Any]:
        """
        验证必需的键是否存在
        
        Args:
            required_keys: 必需键列表
            
        Returns:
            Dict: 包含验证结果的字典
        """
        missing_keys = []
        values = {}
        
        for key in required_keys:
            value = self.get(key)
            if value is None:
                missing_keys.append(key)
            else:
                values[key] = value
        
        return {
            "is_valid": len(missing_keys) == 0,
            "missing_keys": missing_keys,
            "values": values
        }

    def store_draft_efficiently(self, draft: str) -> bool:
        """
        高效存储文稿内容，避免重复
        
        可以在这里添加压缩或引用优化等功能
        
        Args:
            draft: 文稿内容
            
        Returns:
            bool: 操作是否成功
        """
        logger.info(f"开始存储文稿，长度: {len(draft)}")
        
        # 检查当前是否已有文稿
        current_draft = self.get(CURRENT_DRAFT_KEY)
        if current_draft:
            logger.info(f"当前已存在文稿，长度: {len(current_draft)}")
            # 比较是否相同
            if current_draft == draft:
                logger.info("新文稿与现有文稿相同，不需要重复存储")
                return True
        
        # 存储文稿
        result = self.set(CURRENT_DRAFT_KEY, draft)
        
        # 确保迭代计数也被正确设置
        iteration = self.get(ITERATION_COUNT_KEY, 0)
        if iteration == 0:
            logger.info("首次存储文稿，设置迭代计数为1")
            self.set(ITERATION_COUNT_KEY, 1)
        
        # 再次验证是否存储成功
        if result:
            logger.info(f"文稿存储成功，验证状态: 键'{CURRENT_DRAFT_KEY}'存在={CURRENT_DRAFT_KEY in self.state}")
            saved_draft = self.get(CURRENT_DRAFT_KEY)
            logger.info(f"保存后的文稿长度: {len(saved_draft) if saved_draft else 0}")
        
        return result
    
    def get_draft_metadata(self) -> Dict[str, Any]:
        """
        获取当前文稿的元数据，而不返回完整内容
        
        Returns:
            Dict: 包含文稿元数据的字典
        """
        draft = self.get(CURRENT_DRAFT_KEY)
        return {
            "exists": draft is not None,
            "length": len(draft) if draft else 0,
            "preview": draft[:100] + "..." if draft and len(draft) > 100 else draft
        } 