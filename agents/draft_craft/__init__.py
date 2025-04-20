# sequential_orchestrator_flat/__init__.py

# 导入内层包
from . import draft_craft

# 从内层包导入核心组件
from .draft_craft import root_agent

# 将内层的tools子包暴露给外部
# 创建一个系统级别的模块引用，让Python导入系统能正确找到draft_craft.tools
import sys as _sys
_sys.modules['draft_craft.tools'] = draft_craft.tools

# 同时将tools作为当前包的属性，方便直接访问
tools = draft_craft.tools

# 创建符合run_agent.py等文件使用习惯的命名空间
import types
agent = types.SimpleNamespace(root_agent=draft_craft.root_agent)

# 定义公开的API
__all__ = ["root_agent", "tools"]
