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

"""基础状态管理工具，简洁扁平实现。"""

import logging
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# 定义状态键名常量
INITIAL_MATERIAL_KEY = "initial_material"
INITIAL_REQUIREMENTS_KEY = "initial_requirements"
INITIAL_SCORING_CRITERIA_KEY = "initial_scoring_criteria"
CURRENT_DRAFT_KEY = "current_draft"
CURRENT_SCORE_KEY = "current_score"
CURRENT_FEEDBACK_KEY = "current_feedback"
SCORE_THRESHOLD_KEY = "score_threshold"
ITERATION_COUNT_KEY = "iteration_count"
IS_COMPLETE_KEY = "is_complete"


def check_initial_data(tool_context: ToolContext) -> dict:
    """
    检查会话状态中是否存在必要的初始数据。
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问。
    
    Returns:
        dict: 包含状态信息的字典，如果所有必要数据都存在，则'status'为'ready'；
             否则'status'为'missing_data'，并包含缺失的键列表。
    """
    logger.info("检查会话状态中的初始数据...")
    state = tool_context.state
    material = state.get(INITIAL_MATERIAL_KEY)
    requirements = state.get(INITIAL_REQUIREMENTS_KEY)
    criteria = state.get(INITIAL_SCORING_CRITERIA_KEY)
    
    # 记录初始状态内容，便于调试
    logger.info(f"检查状态中的初始数据：material={material is not None}, requirements={requirements is not None}, criteria={criteria is not None}")
    
    if material and requirements and criteria:
        logger.info("在会话状态中找到所有初始数据。")
        return {"status": "ready"}
    else:
        missing_keys = []
        if not material: missing_keys.append(INITIAL_MATERIAL_KEY)
        if not requirements: missing_keys.append(INITIAL_REQUIREMENTS_KEY)
        if not criteria: missing_keys.append(INITIAL_SCORING_CRITERIA_KEY)
        logger.warning(f"会话状态中缺少初始数据。缺失键: {missing_keys}")
        return {"status": "missing_data", "missing_keys": missing_keys}


def store_initial_data(
    initial_material: str,
    initial_requirements: str,
    initial_scoring_criteria: str,
    tool_context: ToolContext,
    score_threshold: float = 8.5
) -> dict:
    """
    将用户提供的初始数据存储到会话状态中。
    
    Args:
        initial_material: 写作的原始素材内容
        initial_requirements: 写作的具体要求
        initial_scoring_criteria: 评分的标准和方法
        tool_context: ADK工具上下文，用于访问会话状态
        score_threshold: 评分阈值，默认为8.5
    
    Returns:
        dict: 包含操作状态信息的字典
    """
    try:
        logger.info(f"存储初始数据: 素材='{initial_material[:50]}...', 要求='{initial_requirements[:50]}...', 标准='{initial_scoring_criteria[:50]}...'")
        # 直接使用state字典API更新多个键值
        tool_context.state.update({
            INITIAL_MATERIAL_KEY: initial_material,
            INITIAL_REQUIREMENTS_KEY: initial_requirements,
            INITIAL_SCORING_CRITERIA_KEY: initial_scoring_criteria,
            SCORE_THRESHOLD_KEY: score_threshold,
            # 初始化迭代计数和完成标志
            ITERATION_COUNT_KEY: 0,
            IS_COMPLETE_KEY: False
        })
        
        # 验证写入内容是否正确保存
        if (tool_context.state.get(INITIAL_MATERIAL_KEY) == initial_material and
            tool_context.state.get(INITIAL_REQUIREMENTS_KEY) == initial_requirements and
            tool_context.state.get(INITIAL_SCORING_CRITERIA_KEY) == initial_scoring_criteria):
            logger.info("成功将初始数据更新到会话状态。")
            return {"status": "success", "message": "初始数据已成功存储到会话状态。"}
        else:
            logger.error("状态验证失败：写入的数据与读取的数据不匹配。")
            return {"status": "error", "message": "数据验证失败，请重试。"}
    except Exception as e:
        logger.error(f"存储初始数据时出错: {e}", exc_info=True)
        return {"status": "error", "message": f"由于错误无法存储初始数据: {e}"}


def get_final_draft(tool_context: ToolContext) -> dict:
    """
    从会话状态获取最终草稿文本。
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问。
    
    Returns:
        dict: 包含检索到的草稿文本以及相关评分和反馈信息的字典。
    """
    try:
        logger.info(f"从状态键'{CURRENT_DRAFT_KEY}'检索最终草稿。")
        # 获取所有相关数据
        draft_content = tool_context.state.get(CURRENT_DRAFT_KEY, "Error: 会话状态中找不到最终草稿。")
        score = tool_context.state.get(CURRENT_SCORE_KEY)
        feedback = tool_context.state.get(CURRENT_FEEDBACK_KEY)
        iterations = tool_context.state.get(ITERATION_COUNT_KEY, 0)
        
        logger.info(f"检索到草稿: '{draft_content[:100]}...'")
        logger.info(f"评分: {score}, 反馈: '{feedback[:50] if feedback else None}...'")
        logger.info(f"总迭代次数: {iterations}")
        
        return {
            "final_draft_text": draft_content,
            "final_score": score,
            "final_feedback": feedback,
            "iterations_completed": iterations
        }
    except Exception as e:
        logger.error(f"从会话状态检索最终草稿时出错: {e}", exc_info=True)
        return {"final_draft_text": f"检索草稿时出错: {e}", "status": "error"} 