"""解决LLM生成和ADK同步/异步调用冲突的修复脚本"""

import asyncio
import concurrent.futures
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

def run_async_in_thread(async_func, *args, **kwargs):
    """
    在单独的线程中运行异步函数并同步等待结果
    
    Args:
        async_func: 异步函数
        *args, **kwargs: 传递给异步函数的参数
        
    Returns:
        异步函数的执行结果
        
    Raises:
        如果发生错误，则传递原始异常
    """
    result = [None]
    error = [None]
    
    # 在线程中运行事件循环
    def run_in_thread():
        try:
            # 创建一个新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步函数并获取结果
            result[0] = loop.run_until_complete(async_func(*args, **kwargs))
            
            # 关闭循环
            loop.close()
        except Exception as e:
            error[0] = e
    
    # 创建并启动线程
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        try:
            # 等待最多30秒
            future.result(timeout=30)
        except concurrent.futures.TimeoutError:
            raise TimeoutError("异步函数执行超时")
    
    # 如果有错误，重新抛出
    if error[0]:
        raise error[0]
    
    # 返回执行结果
    return result[0]

def safely_run_async(async_func: Callable[..., Awaitable[Any]], fallback_value: Any, *args, **kwargs) -> Any:
    """
    安全地在同步上下文中运行异步函数，如果发生错误则返回后备值
    
    Args:
        async_func: 要运行的异步函数
        fallback_value: 如果异步函数失败时返回的后备值
        *args, **kwargs: 传递给异步函数的参数
        
    Returns:
        成功时返回异步函数的结果，失败时返回后备值
    """
    try:
        return run_async_in_thread(async_func, *args, **kwargs)
    except Exception as e:
        logger.error(f"异步函数执行失败: {e}", exc_info=True)
        return fallback_value 