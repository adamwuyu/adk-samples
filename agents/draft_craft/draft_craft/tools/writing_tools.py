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
import asyncio
from typing import Dict, Any, List, Optional
from google.adk.tools.tool_context import ToolContext
import os

from .state_manager import (
    StateManager, INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, 
    INITIAL_SCORING_CRITERIA_KEY, CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY, SCORE_THRESHOLD_KEY, ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)
from .logging_utils import log_generation_event
from .llm_generator import get_content_generator
from .fix_llm import safely_run_async  # 重新添加，以便在需要时处理异步调用

logger = logging.getLogger(__name__)

# 最大迭代次数
MAX_ITERATIONS = 3

# 控制是否使用LLM生成器的环境变量
USE_LLM_GENERATOR = os.environ.get("USE_LLM_GENERATOR", "false").lower() == "true"


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
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 获取当前迭代计数，如果不存在则初始化为0
        iteration_count = state_manager.get(ITERATION_COUNT_KEY, 0)
        state_manager.set(ITERATION_COUNT_KEY, iteration_count + 1)
        
        # 检查是首次撰写还是改进
        current_draft = state_manager.get(CURRENT_DRAFT_KEY)
        feedback = state_manager.get(CURRENT_FEEDBACK_KEY)
        
        # 根据环境变量决定使用LLM生成还是模拟生成
        if USE_LLM_GENERATOR:
            logger.info("使用LLM生成器创建内容")
            draft = _generate_with_llm(state_manager, current_draft, feedback, iteration_count)
        else:
            logger.info("使用模拟内容生成器创建内容")
            draft = _generate_mock_content(state_manager, current_draft, feedback, iteration_count)
        
        # 高效存储文稿
        if state_manager.store_draft_efficiently(draft):
            logger.info(f"成功将文稿（{len(draft)}字符）保存到状态。")
            # 返回摘要信息，避免重复传递完整内容
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
    except Exception as e:
        logger.error(f"write_draft工具执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"生成文稿时发生错误: {str(e)}"
        }


def _generate_with_llm(
    state_manager: StateManager,
    current_draft: str = None,
    feedback: str = None,
    iteration_count: int = 0
) -> str:
    """
    使用LLM生成文稿内容
    
    Args:
        state_manager: 状态管理器
        current_draft: 当前文稿，如果为None则表示需要生成初始文稿
        feedback: 当前反馈，用于改进文稿
        iteration_count: 当前迭代次数
        
    Returns:
        生成的文稿内容
    """
    try:
        # 获取LLM生成器
        generator = get_content_generator(temperature=0.7)
        
        if not current_draft:
            # 首次撰写：基于初始素材和要求
            material = state_manager.get(INITIAL_MATERIAL_KEY, "")
            requirements = state_manager.get(INITIAL_REQUIREMENTS_KEY, "")
            criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "")
            
            logger.info(f"使用LLM撰写初始文稿。素材长度:{len(material)}，要求长度:{len(requirements)}，评分标准长度:{len(criteria)}")
            
            # 创建提示词
            prompt = f"""
你是一位专业文案写手。请基于以下素材和要求，撰写一篇高质量文章：

## 素材
{material}

## 写作要求
{requirements}

## 评分标准
{criteria}

请直接输出文章内容，不要添加额外说明。
"""
            
            # 生成备用内容
            backup_draft = f"[使用备用内容]\n\n"
            backup_draft += "AI写作工具的优点包括：\n"
            backup_draft += "1. 提高效率：AI工具可以快速生成内容，节省大量时间\n"
            backup_draft += "2. 辅助创作：可以帮助克服写作障碍，提供创意灵感\n"
            backup_draft += "3. 多语言支持：能够翻译和生成多种语言的内容\n"
            backup_draft += "4. 创意激发：提供不同角度的思考和表达方式\n\n"
            backup_draft += "AI写作工具的缺点包括：\n"
            backup_draft += "1. 缺乏深度：生成内容有时缺乏深度和独特见解\n"
            backup_draft += "2. 格式和风格限制：难以完全掌握特定领域的写作风格\n"
            backup_draft += "3. 事实准确性问题：可能生成不准确或过时的信息\n"
            backup_draft += "4. 缺乏个性化：生成内容可能缺乏作者独特的个人风格\n"
            
            # 使用同步方法，避免异步生成器问题
            def generate_content():
                material = state_manager.get(INITIAL_MATERIAL_KEY, "")
                requirements = state_manager.get(INITIAL_REQUIREMENTS_KEY, "")
                criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "")
                try:
                    return generator.generate_initial_draft_sync(material, requirements, criteria)
                except Exception as e:
                    logger.error(f"同步生成初始文稿出错: {e}", exc_info=True)
                    return None
            
            # 在同步上下文中执行，如果失败则使用备用内容
            try:
                logger.info("开始LLM生成初始文稿...")
                
                # 如果是实际的LLM客户端实例
                if not isinstance(generator.model, str):
                    result = generate_content()
                    if result and not result.startswith("生成文稿失败") and not "error" in result.lower():
                        draft = result
                        logger.info(f"LLM生成成功，得到{len(draft)}字符的内容")
                    else:
                        logger.warning("LLM生成失败或返回错误信息，使用备用内容")
                        draft = backup_draft
                else:
                    # 使用模拟内容作为LLM字符串模型的备用方案
                    logger.warning(f"使用的是字符串模型名称({generator.model})，实际生成中会通过API调用，这里使用模拟内容")
                    draft = f"[使用备用内容 - 实际部署时将调用{generator.model}]\n\n" + backup_draft[15:]
            except Exception as e:
                logger.error(f"生成文稿时发生错误: {e}", exc_info=True)
                draft = f"[生成出错 - {str(e)}]\n\n" + backup_draft[15:]
            
            # 记录生成事件
            log_generation_event("llm_draft_created", draft, {
                "iteration": iteration_count,
                "type": "initial_draft",
                "material_length": len(material),
                "requirements_length": len(requirements)
            })
        else:
            # 基于反馈改进现有文稿
            logger.info(f"使用LLM改进文稿（迭代 {iteration_count}）。")
            
            # 获取文稿元数据，避免多次记录完整内容
            draft_metadata = state_manager.get_draft_metadata()
            criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "")
            
            # 创建改进提示词
            prompt = f"""
你是一位专业文案写手。请基于以下反馈，改进现有文稿：

## 当前文稿
{current_draft}

## 评分反馈
{feedback if feedback else "没有具体反馈，请对文稿进行一般性改进，使其更全面、更有深度。"}

## 评分标准
{criteria}

请输出完整的改进后文稿，不要添加额外说明。
"""
            
            # 生成备用改进内容
            backup_improvement = "\n\n[添加备用改进内容]\n\n"
            backup_improvement += "基于反馈进行的改进：\n"
            backup_improvement += "- 更深入分析：增加了对AI写作工具实际应用场景的分析\n"
            backup_improvement += "- 平衡观点：加强了对优缺点的平衡论述\n"
            backup_improvement += "- 提高清晰度：优化了段落结构和表达方式\n"
                
            # 使用同步方法，避免异步生成器问题
            def improve_content():
                criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "")
                try:
                    return generator.improve_draft_sync(current_draft, feedback if feedback else "", criteria)
                except Exception as e:
                    logger.error(f"同步改进文稿出错: {e}", exc_info=True)
                    return None
            
            # 在同步上下文中执行，如果失败则使用备用内容
            try:
                logger.info("开始LLM改进文稿...")
                
                # 如果是实际的LLM客户端实例
                if not isinstance(generator.model, str):
                    result = improve_content()
                    if result and not (result.startswith(current_draft + "\n\n[文稿同步改进失败") or "error" in result.lower()):
                        draft = result
                        logger.info(f"LLM改进成功，得到{len(draft)}字符的内容")
                    else:
                        logger.warning("LLM改进失败或返回错误信息，使用备用内容")
                        draft = current_draft + backup_improvement
                else:
                    # 使用模拟内容作为LLM字符串模型的备用方案
                    logger.warning(f"使用的是字符串模型名称({generator.model})，实际生成中会通过API调用，这里使用模拟内容")
                    draft = current_draft + f"\n\n[使用备用改进内容 - 实际部署时将调用{generator.model}]\n\n"
                    draft += "基于反馈进行的改进：\n"
                    draft += "- 更深入分析：增加了对AI写作工具实际应用场景的分析\n"
                    draft += "- 平衡观点：加强了对优缺点的平衡论述\n"
                    draft += "- 提高清晰度：优化了段落结构和表达方式\n"
            except Exception as e:
                logger.error(f"改进文稿时发生错误: {e}", exc_info=True)
                draft = current_draft + backup_improvement
            
            # 记录生成事件
            log_generation_event("llm_draft_improved", draft, {
                "iteration": iteration_count,
                "previous_length": draft_metadata.get("length", 0),
                "new_length": len(draft),
                "feedback_applied": feedback is not None
            })
        
        return draft
    except Exception as e:
        logger.error(f"LLM生成文稿失败: {e}", exc_info=True)
        # 如果LLM生成失败，回退到模拟生成
        logger.warning("回退到模拟生成内容")
        return _generate_mock_content(state_manager, current_draft, feedback, iteration_count)


def _generate_mock_content(
    state_manager: StateManager,
    current_draft: str = None,
    feedback: str = None,
    iteration_count: int = 0
) -> str:
    """
    生成模拟文稿内容 (旧的实现，作为后备方案)
    
    Args:
        state_manager: 状态管理器
        current_draft: 当前文稿，如果为None则表示需要生成初始文稿
        feedback: 当前反馈，用于改进文稿
        iteration_count: 当前迭代次数
        
    Returns:
        生成的文稿内容
    """
    if not current_draft:
        # 首次撰写：基于初始素材和要求
        material = state_manager.get(INITIAL_MATERIAL_KEY, "")
        requirements = state_manager.get(INITIAL_REQUIREMENTS_KEY, "")
        
        logger.info(f"模拟撰写初始文稿。素材和要求已加载。")
        
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
        
        # 记录生成事件
        log_generation_event("mock_draft_created", draft, {
            "iteration": iteration_count,
            "type": "initial_draft",
            "material_length": len(material),
            "requirements_length": len(requirements)
        })
    else:
        # 基于反馈改进现有文稿
        logger.info(f"模拟改进文稿（迭代 {iteration_count}）。")
        
        # 获取文稿元数据，避免多次记录完整内容
        draft_metadata = state_manager.get_draft_metadata()
        
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
        
        # 记录生成事件
        log_generation_event("mock_draft_improved", draft, {
            "iteration": iteration_count,
            "previous_length": draft_metadata.get("length", 0),
            "new_length": len(draft),
            "feedback_applied": feedback is not None
        })
    
    return draft


def score_draft(tool_context: ToolContext) -> dict:
    """
    评估当前文稿，提供分数和反馈。
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含评分、反馈和状态信息的字典
    """
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 获取必要数据
        draft_metadata = state_manager.get_draft_metadata()
        if not draft_metadata["exists"]:
            logger.error(f"无法评分：状态中找不到文稿")
            return {
                "status": "error",
                "message": "找不到要评分的文稿"
            }
        
        # 获取完整文稿和评分标准
        draft = state_manager.get(CURRENT_DRAFT_KEY)
        criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "清晰度、流畅性和内容相关性")
        
        logger.info(f"评分文稿（{len(draft)}字符）。使用评分标准。")
        
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
        
        # 记录评分事件
        log_generation_event("score_calculated", {
            "score": score,
            "feedback": feedback
        }, {
            "draft_length": len(draft),
            "criteria_used": criteria
        })
        
        # 将评分和反馈保存到状态
        update_results = state_manager.update({
            CURRENT_SCORE_KEY: score,
            CURRENT_FEEDBACK_KEY: feedback
        })
        
        if all(update_results.values()):
            logger.info(f"成功将评分（{score}）和反馈保存到状态。")
        else:
            failed_keys = [k for k, v in update_results.items() if not v]
            logger.error(f"评分/反馈保存失败。失败的键: {failed_keys}")
            return {
                "status": "error",
                "message": f"评分结果保存失败，以下键无法更新: {failed_keys}"
            }
        
        threshold = state_manager.get(SCORE_THRESHOLD_KEY, 90)
        return {
            "status": "success",
            "score": score,
            "feedback": feedback,
            "meets_threshold": score >= threshold
        }
    except Exception as e:
        logger.error(f"score_draft工具执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"评分文稿时发生错误: {str(e)}"
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
    # 使用状态管理器
    state_manager = StateManager(tool_context)
    
    # 获取关键数据
    score = state_manager.get(CURRENT_SCORE_KEY)
    threshold = state_manager.get(SCORE_THRESHOLD_KEY, 90)
    iteration = state_manager.get(ITERATION_COUNT_KEY, 0)
    
    logger.info(f"检查进度：迭代={iteration}，分数={score}，阈值={threshold}")
    
    # 根据条件判断是否完成
    should_continue = True
    reason = ""
    
    logger.warning(f"[SCORING_DEBUG] iteration: {iteration}, MAX_ITERATIONS: {MAX_ITERATIONS}, score: {score}, threshold: {threshold}")
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
    
    # 记录进度检查事件
    log_generation_event("progress_checked", {
        "should_continue": should_continue,
        "reason": reason
    }, {
        "iteration": iteration,
        "score": score,
        "threshold": threshold
    })
    
    # 更新完成状态
    state_manager.set(IS_COMPLETE_KEY, not should_continue)
    
    return {
        "status": "success",
        "should_continue": should_continue,
        "is_complete": not should_continue,
        "reason": reason,
        "iteration": iteration,
        "score": score,
        "threshold": threshold
    }


def _safely_call_async_api(async_func, fallback_value, *args, **kwargs):
    """
    安全地调用异步API，如果可能的话使用safely_run_async
    
    Args:
        async_func: 要调用的异步函数
        fallback_value: 失败时返回的值
        *args, **kwargs: 传递给异步函数的参数
        
    Returns:
        异步函数的结果，或失败时的备用值
    """
    try:
        return safely_run_async(async_func, fallback_value, *args, **kwargs)
    except Exception as e:
        logger.error(f"异步调用失败: {e}", exc_info=True)
        return fallback_value 