# expose agent for top-level discovery
from .workflow.assembler import root_agent as agent

# expose tools for top-level discovery (if needed by __init__.py)
from . import tools

__all__ = ['agent', 'tools']
