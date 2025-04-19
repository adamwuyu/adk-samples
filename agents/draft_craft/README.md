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