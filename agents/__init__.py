# agents/__init__.py

# 从子模块导入你的 Agent 实例
# 修改点：导入 root_agent
from .sequential_orchestrator import root_agent as sequential_orchestrator_agent

# 添加对sequential_orchestrator_flat的导入（使用符合ADK Web的路径）
try:
    from .sequential_orchestrator_flat.agent import root_agent as sequential_orchestrator_flat_agent
    print("Successfully imported sequential_orchestrator_flat agent")
except ImportError as e:
    print(f"Warning: Could not import sequential_orchestrator_flat agent: {e}")
    sequential_orchestrator_flat_agent = None

# 创建一个字典来存储所有需要暴露的 Agent
# 使用 Agent 实例的 .name 属性作为 key 是个好习惯
agents = {}
# 修改点：使用 root_agent 变量
if sequential_orchestrator_agent: # 确保 Agent 实例已成功创建
    # 使用 root_agent.name 作为 key (其值为 "writing_scoring_pipeline_agent_mvp")
    agents[sequential_orchestrator_agent.name] = sequential_orchestrator_agent
else:
    print("Warning: sequential_orchestrator.root_agent not found or initialized, cannot expose via agents/__init__.py")

# 添加sequential_orchestrator_flat的agent
if sequential_orchestrator_flat_agent:
    agents[sequential_orchestrator_flat_agent.name] = sequential_orchestrator_flat_agent
    print(f"Added sequential_orchestrator_flat agent with name: {sequential_orchestrator_flat_agent.name}")

# (可选) 如果将来有其他 Agent，也像这样导入并添加到字典中
# 尝试导入其他示例 Agent (如果它们遵循 root_agent 约定)
try:
    from .fomc_research.fomc_research import root_agent as fomc_agent
    if fomc_agent:
        agents[fomc_agent.name] = fomc_agent
except ImportError:
    print("Could not import fomc_research agent.")
# ... 添加其他需要暴露的 agent

# 确保 __all__ 包含 agents 字典，或者 ADK 会自动查找名为 'agents' 的变量
__all__ = ["agents"]

print(f"Agents discovered in agents/__init__.py: {list(agents.keys())}") 