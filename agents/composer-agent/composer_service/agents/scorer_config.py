# 评分 Prompt 模板
SCORING_PROMPT_TEMPLATE = """
你是一位专业文稿评审，需要根据评分标准对以下文稿进行评估。

## 评分标准
{scoring_criteria}

## 待评文稿
{draft}

请按照以下格式进行评估：

分数: <0-100的整数>
反馈: <简明扼要的评价和建议>
"""

# Scorer Agent 指令
# 使用占位符 {draft_key} 和 {criteria_key}，Agent 初始化时会替换为实际的 state key
SCORER_AGENT_INSTRUCTION = "请根据 state['{criteria_key}'] 中的评分标准对 state['{draft_key}'] 中的文稿进行评分并给出反馈。" 