"""日志工具，用于增强系统可观察性。"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

# 配置根日志记录器
logger = logging.getLogger(__name__)

def setup_logging(level=logging.INFO):
    """
    设置日志配置
    
    Args:
        level: 日志级别，默认为INFO
    """
    # 配置根日志记录器
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_state_operation(
    operation: str, 
    key: str, 
    value: Any = None, 
    metadata: Optional[Dict[str, Any]] = None,
    truncate_length: int = 200
):
    """
    记录状态操作的结构化日志
    
    Args:
        operation: 操作类型，如'read', 'write', 'delete'
        key: 状态键名
        value: 操作的值（可选）
        metadata: 额外元数据（可选）
        truncate_length: 值截断长度，避免过长日志
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "key": key,
    }
    
    # 处理值的日志记录，截断过长内容
    if value is not None:
        if isinstance(value, str):
            log_value = (value[:truncate_length] + "...") if len(value) > truncate_length else value
            log_data["value_length"] = len(value)
        else:
            try:
                # 尝试将值转换为字符串
                log_value = str(value)
                if len(log_value) > truncate_length:
                    log_value = log_value[:truncate_length] + "..."
                log_data["value_length"] = len(log_value)
            except:
                log_value = f"<不可序列化的值，类型: {type(value).__name__}>"
        
        log_data["value_preview"] = log_value
    
    # 添加元数据
    if metadata:
        log_data["metadata"] = metadata
    
    # 记录结构化日志
    logger.info(f"状态操作: {json.dumps(log_data, ensure_ascii=False)}")
    
    return log_data

def log_generation_event(
    event_type: str,
    content: Union[str, Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    truncate_length: int = 300
):
    """
    记录内容生成事件的结构化日志
    
    Args:
        event_type: 事件类型，如'draft_generated', 'score_calculated'
        content: 生成的内容或结构化数据
        metadata: 额外元数据（可选）
        truncate_length: 内容截断长度，避免过长日志
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
    }
    
    # 处理内容
    if isinstance(content, str):
        log_content = (content[:truncate_length] + "...") if len(content) > truncate_length else content
        log_data["content_length"] = len(content)
        log_data["content_preview"] = log_content
    elif isinstance(content, dict):
        # 对字典内容进行处理，截断长字符串
        processed_content = {}
        for k, v in content.items():
            if isinstance(v, str) and len(v) > truncate_length:
                processed_content[k] = v[:truncate_length] + "..."
                processed_content[f"{k}_length"] = len(v)
            else:
                processed_content[k] = v
        log_data["content"] = processed_content
    else:
        log_data["content"] = str(content)
    
    # 添加元数据
    if metadata:
        log_data["metadata"] = metadata
    
    # 记录结构化日志
    logger.info(f"生成事件: {json.dumps(log_data, ensure_ascii=False)}")
    
    return log_data 