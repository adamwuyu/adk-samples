"""Sequential Agent to orchestrate writing and scoring."""

from typing import Any, Dict, Type

# 假设 Mock Agents 在父级或同级目录的模块中
# 在实际项目中，你可能需要调整导入路径
from ..writing_scoring_mocks import MockWritingAgent, MockScoringAgent

# 从文档中复制或导入上下文类型定义
PipelineContext = Dict[str, Any]

class SequentialAgent:
    """Orchestrates a sequence of agents (e.g., write then score)."""

    def __init__(self, writing_agent: Type[MockWritingAgent], scoring_agent: Type[MockScoringAgent]):
        """Initializes with instances of the agents to sequence."""
        # 注意：这里传入的是类本身或实例，取决于你的设计
        # 为简单起见，我们假设传入的是实例
        self.writing_agent = writing_agent()
        self.scoring_agent = scoring_agent()
        print("SequentialAgent initialized.")

    def invoke(
        self,
        initial_material: str,
        initial_requirements: str,
        initial_scoring_criteria: str
    ) -> PipelineContext:
        """
        Runs the sequential pipeline: write -> score.

        Args:
            initial_material: The initial material for writing.
            initial_requirements: The writing requirements.
            initial_scoring_criteria: The scoring criteria.

        Returns:
            The final context containing the draft, score, and feedback.
        """
        print("=== SequentialAgent invoked ===")
        # 1. 初始化上下文 (Task 1.3.1: 适配接收初始输入)
        context: PipelineContext = {
            "initial_material": initial_material,
            "initial_requirements": initial_requirements,
            "initial_scoring_criteria": initial_scoring_criteria,
            "current_draft": None,
            "current_score": None,
            "current_feedback": None
        }
        print("Initial context created.")

        # 2. 调用 MockWritingAgent (Task 1.3.2: 串联调用)
        try:
            context = self.writing_agent.invoke(context)
            print("Context after MockWritingAgent.")
        except Exception as e:
            print(f"Error invoking MockWritingAgent: {e}")
            context['current_feedback'] = f"写稿 Agent 执行失败: {e}"
            return context # 提前返回错误

        # 3. 调用 MockScoringAgent (Task 1.3.2: 串联调用)
        try:
            context = self.scoring_agent.invoke(context)
            print("Context after MockScoringAgent.")
        except Exception as e:
            print(f"Error invoking MockScoringAgent: {e}")
            # 保留已生成的文稿，但标记评分失败
            context['current_score'] = None
            context['current_feedback'] = (context.get('current_feedback', '') + f"；评分 Agent 执行失败: {e}").strip('；')
            return context # 提前返回错误

        # 4. 返回最终结果 (Task 1.3.3: 适配输出最终结果)
        print("=== SequentialAgent finished ===")
        return context 