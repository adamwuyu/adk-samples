from google.adk.tools import FunctionTool
from typing import Dict, List

# 评分工具：面向"中等家长"受众

def score_for_parents(
    draft_content: str,
    audience_profile: str,
    scoring_criteria: str
) -> Dict:
    """
    针对中等受教育水平、经济中等以上的家长（孩子小学高年级至高一），
    结合受众画像和评分标准，对draft_content进行多维度评分和详细反馈。
    返回结构化分数、反馈和关键问题。
    输入：
      - draft_content: str，待评分的文稿内容
      - audience_profile: str，受众画像描述（建议引用docs/受众描述-中等家长.md）
      - scoring_criteria: str，评分标准（如内容相关性、建议可操作性、语言通俗性等）
    输出：
      - score: int，0-100分
      - feedback: str，详细反馈
      - key_issues: list[str]，关键问题列表，便于后续自动分析
    """
    # TODO: 这里应调用LLM，构造Prompt，解析LLM输出。当前为TDD占位实现。
    if not draft_content.strip():
        return {
            "score": 0,
            "feedback": "内容为空，请补充文稿内容。",
            "key_issues": ["内容为空"]
        }
    if "天气" in draft_content:
        return {
            "score": 30,
            "feedback": "内容不相关，未涉及家长关心的话题，也未涉及教育、亲子、成长等核心要素。",
            "key_issues": ["内容不相关"]
        }
    if "专家建议" in draft_content and "案例" in draft_content:
        return {
            "score": 90,
            "feedback": "内容高度贴合家长关心的问题，结构清晰，建议具体，具有较强的可操作性。",
            "key_issues": []
        }
    return {
        "score": 60,
        "feedback": "内容基本相关，但建议补充更多实际案例和具体做法。",
        "key_issues": ["缺少案例"]
    }

score_for_parents_tool = FunctionTool(func=score_for_parents) 