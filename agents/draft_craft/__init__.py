# sequential_orchestrator_flat/__init__.py

# Expose the agent from the inner package
from .draft_craft import root_agent
import types
from . import draft_craft
agent = types.SimpleNamespace(root_agent=draft_craft.root_agent)

__all__ = ["root_agent"]
