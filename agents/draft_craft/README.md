# Sequential Orchestrator - 扁平化实现

本项目是Sequential Orchestrator的扁平化架构实现版本，用于解决原版中存在的状态管理问题。

## 架构特点

1. **扁平结构**：单一Root Agent + 完整Tool集，取代多层嵌套的Agent结构
2. **强化工具职责**：每个Tool负责明确的单一功能，并负责状态管理
3. **状态驱动**：使用状态标志（如`iteration_count`、`is_complete`）控制流程，而非依赖复杂的Agent结构
4. **可靠的状态管理**：每个Tool在操作状态后进行验证，确保数据正确保存

## 主要组件

- **Root Agent**：单一入口点，负责整体流程协调
- **核心工具**：
  - `check_initial_data` / `store_initial_data`：初始化数据管理
  - `write_draft`：生成或改进文稿
  - `score_draft`：评估文稿质量
  - `check_progress`：决定是继续迭代还是完成流程
  - `get_final_draft`：获取最终结果

## 运行方式

### 开发环境

```bash
# 安装依赖
cd sequential_orchestrator_flat
pip install -e .

# 通过ADK CLI运行
adk web sequential_orchestrator_flat
```

### 测试

待补充测试脚本。

## 设计原则

此实现遵循以下ADK最佳实践：

1. 将状态访问逻辑封装在Tool中，不在Agent指令中指定具体的状态操作
2. 使用简洁明了的Agent指令，关注"做什么"而非"如何做"
3. 采用类似官方示例（如personalized-shopping）的扁平架构
4. 增强日志和验证，便于调试和追踪 

## 集成测试的定位与架构角色

本项目的集成测试（如 `tests/run_flat_test.py`）在整体ADK架构中的定位如下：

- **入口函数角色**：集成测试脚本扮演 ADK 架构中"入口函数（EntryPoint）"的角色，模拟真实用户与系统的完整交互流程。生产环境下，用户通过 Web UI 交互，Web 服务端的入口函数会初始化 Runner 并驱动 Agent（如 root_agent）；集成测试则以脚本方式模拟用户输入，驱动 Runner 和 Agent，流程本质一致。
- **驱动与观测**：测试脚本负责初始化 Runner、SessionService、root_agent，并通过 Runner 驱动整个业务流程。它模拟用户输入，监听事件流，观测和断言每一步的输出和状态变化。
- **业务流程一致性**：所有业务逻辑（如文稿生成、评分、保存等）都由 root_agent 及其注册的工具（Tool）自动推进，测试流程与生产环境保持高度一致。
- **测试与生产的边界**：测试脚本应避免主动修正或兜底业务状态，防止掩盖底层实现的 bug。最佳实践是只观测和断言，不主动干预业务逻辑。

**结论**：集成测试是验证 root_agent 及其工具集成效果的关键手段，确保端到端流程在真实场景下的正确性和健壮性。其本质是"模拟用户与 root_agent 的交互，测试 root_agent 及其所能调用的所有工具和其它 Agent 的集成效果"。 