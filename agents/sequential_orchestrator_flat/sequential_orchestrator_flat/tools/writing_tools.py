# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""写作与评分工具，扁平化实现。"""

import logging
from google.adk.tools import ToolContext

from .state_tools import (
    INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, INITIAL_SCORING_CRITERIA_KEY,
    CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, 
    SCORE_THRESHOLD_KEY, ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)

logger = logging.getLogger(__name__)

# 最大迭代次数
MAX_ITERATIONS = 3


def write_draft(tool_context: ToolContext) -> dict:
    """
    生成或改进文稿。
    
    基于会话状态，该工具将：
    1. 如果是首次撰写（无current_draft），基于initial_material和initial_requirements创建新文稿
    2. 如果已有文稿和反馈，则根据反馈改进当前文稿
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含生成的文稿摘要和状态信息的字典
    """
    state = tool_context.state
    
    # 获取当前迭代计数，如果不存在则初始化为0
    iteration_count = state.get(ITERATION_COUNT_KEY, 0)
    state[ITERATION_COUNT_KEY] = iteration_count + 1
    
    # 检查是首次撰写还是改进
    current_draft = state.get(CURRENT_DRAFT_KEY)
    feedback = state.get(CURRENT_FEEDBACK_KEY)
    
    if not current_draft:
        # 首次撰写：基于初始素材和要求
        material = state.get(INITIAL_MATERIAL_KEY, "")
        requirements = state.get(INITIAL_REQUIREMENTS_KEY, "")
        
        logger.info(f"首次撰写文稿。素材: '{material[:50]}...' 要求: '{requirements[:50]}...'")
        
        # 简单模拟文稿生成
        draft = f"这是基于要求'{requirements[:30]}...'生成的初始文稿。\n\n"
        draft += "AI写作工具的优点包括：\n"
        draft += "1. 提高效率：AI工具可以快速生成内容，节省大量时间\n"
        draft += "2. 辅助创作：可以帮助克服写作障碍，提供创意灵感\n"
        draft += "3. 多语言支持：能够翻译和生成多种语言的内容\n\n"
        draft += "AI写作工具的缺点包括：\n"
        draft += "1. 缺乏深度：生成内容有时缺乏深度和独特见解\n"
        draft += "2. 格式和风格限制：难以完全掌握特定领域的写作风格\n"
        draft += "3. 事实准确性问题：可能生成不准确或过时的信息\n"
    else:
        # 基于反馈改进现有文稿
        logger.info(f"正在改进文稿（迭代 {iteration_count + 1}）。反馈: '{feedback[:50]}...'")
        
        # 简单模拟文稿改进
        draft = current_draft
        if feedback and "更多针对AI写作工具优缺点的内容" in feedback:
            # 添加更多关于AI写作工具的内容
            draft += "\n\n额外的AI写作工具优点：\n"
            draft += "4. 个性化内容：可以根据目标受众定制内容\n"
            draft += "5. 内容一致性：保持整个文档的语调和风格一致\n\n"
            draft += "额外的AI写作工具缺点：\n"
            draft += "4. 创造力限制：难以产生真正创新的思想和表达\n"
            draft += "5. 伦理考量：使用AI生成内容可能涉及版权和原创性问题\n"
    
    # 将生成的文稿保存到状态
    state[CURRENT_DRAFT_KEY] = draft
    
    # 校验保存是否成功
    if state.get(CURRENT_DRAFT_KEY) == draft:
        logger.info(f"成功将文稿（{len(draft)}字符）保存到状态。")
        # 返回摘要信息
        return {
            "status": "success",
            "draft_summary": draft[:100] + "..." if len(draft) > 100 else draft,
            "draft_length": len(draft),
            "iteration": iteration_count + 1
        }
    else:
        logger.error("文稿保存验证失败")
        return {
            "status": "error",
            "message": "文稿保存失败，无法验证状态更新"
        }


def score_draft(tool_context: ToolContext) -> dict:
    """
    评估当前文稿，提供分数和反馈。
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含评分、反馈和状态信息的字典
    """
    state = tool_context.state
    
    # 获取必要数据
    draft = state.get(CURRENT_DRAFT_KEY)
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY)
    
    if not draft:
        logger.error(f"无法评分：状态中找不到文稿（键：{CURRENT_DRAFT_KEY}）")
        return {
            "status": "error",
            "message": "找不到要评分的文稿"
        }
    
    if not criteria:
        logger.warning(f"未指定评分标准（键：{INITIAL_SCORING_CRITERIA_KEY}），使用默认标准")
        criteria = "清晰度、流畅性和内容相关性"
    
    logger.info(f"评分文稿（{len(draft)}字符）。标准: '{criteria[:50]}...'")
    
    # 模拟评分逻辑
    # 根据文稿内容和评分标准计算得分
    score = 7.0  # 基础分
    
    # 检查文稿是否包含评分标准中强调的点
    if "清晰度" in criteria and len(draft) > 200:
        score += 0.5  # 较长文稿可能更清晰
    
    if "优缺点" in criteria and "优点" in draft and "缺点" in draft:
        score += 1.0  # 包含优缺点讨论
    
    if "AI写作工具" in draft and len(draft.split("AI写作工具")) > 3:
        score += 0.5  # 多次提及关键主题
    
    # 最终分数限制在0-10范围内，四舍五入到1位小数
    score = round(min(max(score, 0.0), 10.0), 1)
    
    # 生成反馈
    feedback = f"模拟评分反馈: 基于标准 '{criteria}', 草稿得分为 {score}。"
    if score < 8.5:
        feedback += "需要更多针对AI写作工具优缺点的内容。"
    
    # 将评分和反馈保存到状态
    state[CURRENT_SCORE_KEY] = score
    state[CURRENT_FEEDBACK_KEY] = feedback
    
    # 验证保存成功
    saved_score = state.get(CURRENT_SCORE_KEY)
    saved_feedback = state.get(CURRENT_FEEDBACK_KEY)
    
    if saved_score == score and saved_feedback == feedback:
        logger.info(f"成功将评分（{score}）和反馈保存到状态。")
    else:
        logger.error(f"分数/反馈保存验证失败。预期分数：{score}，获取到：{saved_score}")
        return {
            "status": "error",
            "message": "评分结果保存失败，无法验证状态更新"
        }
    
    return {
        "status": "success",
        "score": score,
        "feedback": feedback,
        "meets_threshold": score >= state.get(SCORE_THRESHOLD_KEY, 8.5)
    }


def check_progress(tool_context: ToolContext) -> dict:
    """
    检查写作进度，决定是继续迭代还是完成流程。
    
    该工具会检查：
    1. 当前迭代次数是否已达最大值
    2. 分数是否已超过阈值
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含进度状态和决策信息的字典
    """
    state = tool_context.state
    
    # 获取关键数据
    score = state.get(CURRENT_SCORE_KEY)
    threshold = state.get(SCORE_THRESHOLD_KEY, 8.5)
    iteration = state.get(ITERATION_COUNT_KEY, 0)
    
    logger.info(f"检查进度：迭代={iteration}，分数={score}，阈值={threshold}")
    
    # 根据条件判断是否完成
    should_continue = True
    reason = ""
    
    if iteration >= MAX_ITERATIONS:
        should_continue = False
        reason = f"已达到最大迭代次数（{MAX_ITERATIONS}）"
        logger.info(f"终止迭代：{reason}")
    elif score is not None and score >= threshold:
        should_continue = False
        reason = f"分数（{score}）已达到或超过阈值（{threshold}）"
        logger.info(f"终止迭代：{reason}")
    elif score is None:
        should_continue = False
        reason = "无法找到评分结果，无法继续"
        logger.warning(f"终止迭代：{reason}")
    
    # 更新完成状态
    state[IS_COMPLETE_KEY] = not should_continue
    
    return {
        "status": "success",
        "should_continue": should_continue,
        "is_complete": not should_continue,
        "reason": reason,
        "iteration": iteration,
        "score": score,
        "threshold": threshold
    } 