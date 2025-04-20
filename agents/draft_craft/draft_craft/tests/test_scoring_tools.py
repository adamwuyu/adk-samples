import pytest
import os
import re
from unittest.mock import MagicMock

from draft_craft.tools.scoring_tools import score_for_parents, parse_scoring_result, save_parents_scoring_result

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

@pytest.fixture
def mock_tool_context():
    """创建模拟的ToolContext"""
    mock_context = MagicMock()
    mock_context.state = {}
    return mock_context

def test_score_for_parents_prompt_generation(default_audience_profile, default_scoring_criteria):
    """测试提示词生成功能"""
    draft = "本篇文章介绍了如何帮助孩子顺利度过小升初阶段，建议家长多与孩子沟通，关注孩子心理变化。"
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    
    # 验证返回结构
    assert isinstance(result, dict)
    assert "status" in result and result["status"] == "llm_prompt_ready"
    assert "prompt" in result and isinstance(result["prompt"], str)
    assert "audience_type" in result and result["audience_type"] == "parents"
    
    # 验证提示词内容包含必要元素
    prompt = result["prompt"]
    assert "受众画像描述" in prompt
    assert "评分标准" in prompt
    assert "待评文稿" in prompt
    assert draft in prompt
    assert default_scoring_criteria in prompt
    assert "0-100分" in prompt

def test_score_for_parents_empty_draft(default_audience_profile, default_scoring_criteria):
    """测试空文稿的处理"""
    draft = ""
    result = score_for_parents(draft, default_audience_profile, default_scoring_criteria)
    
    # 空文稿应直接返回低分结果，不生成提示词
    assert "score" in result and result["score"] == 0
    assert "feedback" in result and "内容为空" in result["feedback"]
    assert "key_issues" in result and "内容为空" in result["key_issues"]

def test_parse_scoring_result_basic():
    """测试基本的评分结果解析"""
    llm_output = """
    85
    
    这篇文章内容非常贴合家长关心的话题，针对小升初阶段的孩子提供了实用建议。文章结构清晰，语言通俗易懂，适合中等教育水平家长阅读。建议具体可行，父母容易落实到实际教育中。
    
    不过，文章可以在以下几方面进一步改进：
    
    - 可以增加一些实际案例，帮助家长更好地理解如何应用这些建议
    - 建议补充一些应对孩子学习压力增大的具体方法
    - 文章结尾可以加强呼应，给读者留下更深刻印象
    """
    
    result = parse_scoring_result(llm_output)
    
    assert result["score"] == 85
    assert "这篇文章内容非常贴合家长关心的话题" in result["feedback"]
    assert len(result["key_issues"]) == 3
    assert "可以增加一些实际案例" in result["key_issues"][0]

def test_parse_scoring_result_without_list():
    """测试没有明确列表的评分结果解析"""
    llm_output = """
    60
    
    文章涉及了家长关心的话题，但内容较为笼统，缺乏具体建议。语言简单直白，但阐述不够深入。结构基本清晰，但逻辑过渡不够自然。建议补充更多实际案例和可操作的方法，增强文章的实用性和针对性。
    """
    
    result = parse_scoring_result(llm_output)
    
    assert result["score"] == 60
    assert "文章涉及了家长关心的话题" in result["feedback"]
    assert len(result["key_issues"]) == 0  # 没有列表项

def test_save_parents_scoring_result(mock_tool_context):
    """测试保存评分结果到状态"""
    llm_output = """
    85
    
    这篇文章内容非常贴合家长关心的话题，针对小升初阶段的孩子提供了实用建议。文章结构清晰，语言通俗易懂，适合中等教育水平家长阅读。建议具体可行，父母容易落实到实际教育中。
    
    不过，文章可以在以下几方面进一步改进：
    
    - 可以增加一些实际案例，帮助家长更好地理解如何应用这些建议
    - 建议补充一些应对孩子学习压力增大的具体方法
    - 文章结尾可以加强呼应，给读者留下更深刻印象
    """
    
    result = save_parents_scoring_result(llm_output, mock_tool_context)
    
    # 验证返回结构
    assert result["status"] == "success"
    assert result["score"] == 85
    assert "这篇文章内容非常贴合家长关心的话题" in result["feedback_summary"]
    assert len(result["key_issues"]) == 3
    
    # 验证状态更新
    assert mock_tool_context.state.get("current_score") == 85.0
    assert "这篇文章内容非常贴合家长关心的话题" in mock_tool_context.state.get("current_feedback")
    
    # 验证是否完成状态（分数85超过默认阈值80）
    assert result["is_complete"] == True
    assert mock_tool_context.state.get("is_complete") == True

# 可根据实际需求继续补充更多边界和特殊场景测试 