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

"""基础状态管理工具，使用优化的状态管理器实现。"""

import logging
from google.adk.tools import ToolContext

from .state_manager import (
    StateManager, INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, 
    INITIAL_SCORING_CRITERIA_KEY, CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY, SCORE_THRESHOLD_KEY, ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)
from .logging_utils import log_generation_event

logger = logging.getLogger(__name__)


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
    state_manager = StateManager(tool_context)
    
    # 使用验证必需键的方法
    validation_result = state_manager.validate_required_keys([
        INITIAL_MATERIAL_KEY,
        INITIAL_REQUIREMENTS_KEY,
        INITIAL_SCORING_CRITERIA_KEY
    ])
    
    if validation_result["is_valid"]:
        logger.info("在会话状态中找到所有初始数据。")
        return {"status": "ready"}
    else:
        logger.warning(f"会话状态中缺少初始数据。缺失键: {validation_result['missing_keys']}")
        return {
            "status": "missing_data", 
            "missing_keys": validation_result["missing_keys"]
        }


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
        logger.info("存储初始数据到会话状态...")
        state_manager = StateManager(tool_context)
        
        # 记录初始数据事件
        log_generation_event("initial_data_stored", {
            "material_preview": initial_material[:100] + "..." if len(initial_material) > 100 else initial_material,
            "requirements_preview": initial_requirements[:100] + "..." if len(initial_requirements) > 100 else initial_requirements,
            "criteria_preview": initial_scoring_criteria[:100] + "..." if len(initial_scoring_criteria) > 100 else initial_scoring_criteria,
        }, {
            "material_length": len(initial_material),
            "requirements_length": len(initial_requirements),
            "criteria_length": len(initial_scoring_criteria),
            "threshold": score_threshold
        })
        
        # 使用状态管理器批量更新
        update_results = state_manager.update({
            INITIAL_MATERIAL_KEY: initial_material,
            INITIAL_REQUIREMENTS_KEY: initial_requirements,
            INITIAL_SCORING_CRITERIA_KEY: initial_scoring_criteria,
            SCORE_THRESHOLD_KEY: score_threshold,
            ITERATION_COUNT_KEY: 0,
            IS_COMPLETE_KEY: False
        })
        
        # 检查更新结果
        if all(update_results.values()):
            logger.info("成功将初始数据更新到会话状态。")
            return {"status": "success", "message": "初始数据已成功存储到会话状态。"}
        else:
            failed_keys = [k for k, v in update_results.items() if not v]
            logger.error(f"状态更新部分失败。失败的键: {failed_keys}")
            return {"status": "partial_error", "message": f"部分数据未能保存。失败的键: {failed_keys}"}
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
        logger.info("获取最终文稿和相关信息...")
        state_manager = StateManager(tool_context)
        
        # 获取所有相关数据
        draft_metadata = state_manager.get_draft_metadata()
        if not draft_metadata["exists"]:
            logger.error("会话状态中找不到最终草稿。")
            return {"final_draft_text": "Error: 会话状态中找不到最终草稿。", "status": "error"}
        
        # 获取完整内容
        draft_content = state_manager.get(CURRENT_DRAFT_KEY)
        score = state_manager.get(CURRENT_SCORE_KEY)
        feedback = state_manager.get(CURRENT_FEEDBACK_KEY)
        iterations = state_manager.get(ITERATION_COUNT_KEY, 0)
        
        # 记录最终结果事件
        log_generation_event("final_result_retrieved", {
            "score": score,
            "feedback_preview": feedback[:100] + "..." if feedback and len(feedback) > 100 else feedback
        }, {
            "iterations_completed": iterations,
            "draft_length": draft_metadata["length"]
        })
        
        return {
            "final_draft_text": draft_content,
            "final_score": score,
            "final_feedback": feedback,
            "iterations_completed": iterations,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"从会话状态检索最终草稿时出错: {e}", exc_info=True)
        return {"final_draft_text": f"检索草稿时出错: {e}", "status": "error"} 