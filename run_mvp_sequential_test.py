"""Integration test script for the MVP SequentialAgent flow."""

import sys
import os
from pprint import pprint

# 确保 agents 目录在 Python 路径中
# 这是一种常见做法，但可能需要根据你的项目结构调整
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 从我们创建的模块中导入 Agents
# 注意：这里的导入路径假设此脚本在项目根目录运行
from agents.writing_scoring_mocks import MockWritingAgent, MockScoringAgent
from agents.sequential_orchestrator import SequentialAgent

def main():
    """Runs the MVP sequential workflow test."""
    print("--- Starting MVP Sequential Workflow Test ---")

    # 1. 准备输入数据 (MVP 阶段使用简单字符串)
    material = "关于人工智能在创意写作中的应用的几篇文章摘要。"
    requirements = "写一篇面向普通读者的博客文章，介绍 AI 写作工具的优缺点。"
    scoring_criteria = "重点评估文章的清晰度、流畅性以及对 AI 优缺点的平衡论述。"

    print("\nInput Data:")
    print(f"  Material: {material}")
    print(f"  Requirements: {requirements}")
    print(f"  Scoring Criteria: {scoring_criteria}\n")

    # 2. 初始化 SequentialAgent，传入 Mock Agent 的 *类*
    # SequentialAgent 的 __init__ 会创建实例
    try:
        sequential_agent = SequentialAgent(
            writing_agent=MockWritingAgent,
            scoring_agent=MockScoringAgent
        )
    except ImportError as e:
        print(f"Error initializing SequentialAgent. Check import paths: {e}")
        print("Ensure this script is run from the project root directory ('/Users/adam/adk/adk-samples') or adjust sys.path.")
        return
    except Exception as e:
        print(f"Error initializing SequentialAgent: {e}")
        return

    # 3. 调用 SequentialAgent 的 invoke 方法
    print("\nInvoking SequentialAgent...")
    final_context = sequential_agent.invoke(
        initial_material=material,
        initial_requirements=requirements,
        initial_scoring_criteria=scoring_criteria
    )

    # 4. 打印最终结果
    print("\n--- Final Output Context --- ")
    pprint(final_context)
    print("--- MVP Sequential Workflow Test Finished ---")

if __name__ == "__main__":
    main() 