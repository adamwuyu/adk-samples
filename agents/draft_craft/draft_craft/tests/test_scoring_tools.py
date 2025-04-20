import pytest
import os

from draft_craft.tools.scoring_tools import score_for_parents

@pytest.fixture
def default_audience_profile():
    # 动态拼接，保证无论在哪运行都能找到
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audience_path = os.path.join(base_dir, "docs", "受众描述-中等家长.md")
    with open(audience_path, encoding="utf-8") as f:
        return f.read()

@pytest.fixture
def default_scoring_criteria():
    # 可根据实际项目补充更详细的评分标准
    return "请从内容相关性、建议可操作性、语言通俗性、结构清晰度、观点积极性、信息可靠性等维度进行评分。"

def test_score_for_parents_basic(default_audience_profile, default_scoring_criteria):
    draft = "本篇文章介绍了如何帮助孩子顺利度过小升初阶段，建议家长多与孩子沟通，关注孩子心理变化。"
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    assert isinstance(result, dict)
    assert "score" in result and isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert "feedback" in result and isinstance(result["feedback"], str)
    assert "key_issues" in result and isinstance(result["key_issues"], list)

def test_score_for_parents_empty_draft(default_audience_profile, default_scoring_criteria):
    draft = ""
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    assert result["score"] <= 10  # 空文稿应得低分
    assert "内容为空" in result["feedback"] or "无内容" in result["feedback"]

def test_score_for_parents_irrelevant_content(default_audience_profile, default_scoring_criteria):
    draft = "今天的天气真好，适合去公园散步。"
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    assert result["score"] < 50  # 无关内容应得低分
    assert "不相关" in result["feedback"] or "未涉及家长关心内容" in result["feedback"]

def test_score_for_parents_high_quality(default_audience_profile, default_scoring_criteria):
    draft = (
        "作为家长，如何帮助孩子顺利适应初中生活？"
        "本文结合专家建议和真实案例，提出了三点具体做法："
        "1. 主动沟通，关注孩子心理变化；"
        "2. 制定合理作息，培养自主学习能力；"
        "3. 鼓励孩子参与集体活动，提升社交能力。"
        "这些建议简单易行，适合大多数家庭实践。"
    )
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    assert result["score"] > 80
    assert "结构清晰" in result["feedback"] or "建议具体" in result["feedback"]

# 可根据实际需求继续补充更多边界和特殊场景测试 