"""Mock Agents for MVP testing."""

from typing import Any, Dict, Optional

# 定义与 docs/Agent间通信数据结构.md 一致的上下文类型别名
PipelineContext = Dict[str, Any]

class MockWritingAgent:
    """A mock agent that 'writes' a fixed draft."""

    def invoke(self, context: PipelineContext) -> PipelineContext:
        """
        Simulates writing a draft based on initial inputs.
        Updates the context with the generated draft.
        """
        print("--- MockWritingAgent invoked ---")
        print(f"Received material: {context.get('initial_material', 'N/A')}")
        print(f"Received requirements: {context.get('initial_requirements', 'N/A')}")

        # Simulate writing process
        mock_draft = "这是由 MockWritingAgent 生成的固定文稿内容。"
        context["current_draft"] = mock_draft
        print(f"Generated draft: {mock_draft}")
        print("--- MockWritingAgent finished ---")
        return context

class MockScoringAgent:
    """A mock agent that 'scores' a draft."""

    def invoke(self, context: PipelineContext) -> PipelineContext:
        """
        Simulates scoring the draft in the context.
        Updates the context with a fixed score and feedback.
        """
        print("--- MockScoringAgent invoked ---")
        draft_to_score = context.get("current_draft")
        scoring_criteria = context.get("initial_scoring_criteria", "N/A")

        if not draft_to_score:
            print("Error: No draft found in context to score.")
            context["current_score"] = 0.0
            context["current_feedback"] = "错误：上下文中没有找到可评分的文稿。"
            return context

        print(f"Scoring draft: '{draft_to_score}'")
        print(f"Using criteria: {scoring_criteria}")

        # Simulate scoring process
        mock_score = 7.5
        mock_feedback = "这是来自 MockScoringAgent 的固定评分反馈：分数尚可，结构需优化。"
        context["current_score"] = mock_score
        context["current_feedback"] = mock_feedback
        print(f"Assigned score: {mock_score}")
        print(f"Provided feedback: {mock_feedback}")
        print("--- MockScoringAgent finished ---")
        return context 