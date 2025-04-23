"""扁平架构ADK中的LLM工具集实现。"""

import logging
import os
from typing import Any, Dict, Optional
from google.adk.tools.tool_context import ToolContext

from .state_manager import (
    StateManager, INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY, 
    INITIAL_SCORING_CRITERIA_KEY, CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY, ITERATION_COUNT_KEY, SCORE_THRESHOLD_KEY, IS_COMPLETE_KEY
)
from .logging_utils import log_generation_event, reset_llm_log, log_llm_generation

logger = logging.getLogger(__name__)

# 提示词模板
INITIAL_WRITING_PROMPT_TEMPLATE = """
你是一位专业文案写手。现在，请你基于以下素材和要求，撰写一篇高质量的文章：

## 素材
{material}

## 写作要求
{requirements}

## 评分标准
{scoring_criteria}

请确保你的文稿:
1. 符合写作要求的主题和目标
2. 满足评分标准的要求
3. 具有清晰的结构和流畅的逻辑
4. 语言准确、简洁、易于理解

直接输出正文内容，无需添加标题或额外说明。
"""

REVISION_PROMPT_TEMPLATE = """
你是一位专业文案写手。请基于以下反馈，改进现有文稿：

## 当前文稿
{current_draft}

## 评分反馈
{feedback}

## 评分标准
{scoring_criteria}

## 改进指南
1. 认真分析评分反馈，找出需要改进的地方
2. 保留原文稿的优点和核心内容
3. 针对性地修改和补充内容
4. 确保修改后的文稿更符合评分标准

请输出完整的改进后文稿，而不只是修改建议。
"""

SCORING_PROMPT_TEMPLATE = """
你是一位专业文稿评审，需要根据评分标准对以下文稿进行评估。

## 评分标准
{scoring_criteria}

## 待评文稿
{draft}

请按照以下格式进行评估：

1. 首先给出一个0-10分的总体评分，精确到小数点后一位。
2. 然后提供详细的评价和具体建议，着重指出文稿的优点和需要改进的地方。
3. 建议的总字数在150-300字之间，简明扼要。

你的评分应当客观公正，基于评分标准，而不是个人偏好。
请仅输出最终评分和评价，无需重复上述指示或其他说明。
"""

def generate_initial_draft(tool_context: ToolContext) -> Dict[str, Any]:
    """
    生成初始文稿，基于会话状态中的素材、要求和评分标准。
    
    此工具直接在会话状态中读取素材、要求和评分标准，
    生成初始文稿，并将结果保存回会话状态。
    
    Args:
        tool_context: ADK工具上下文，用于访问会话状态
        
    Returns:
        dict: 包含操作状态和文稿摘要的字典
    """
    logger.info("启动初始文稿生成工具...")
    
    # 每次开始初稿生成时，重置LLM调试日志
    reset_llm_log()
    
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 验证必要的输入数据
        validation_result = state_manager.validate_required_keys([
            INITIAL_MATERIAL_KEY,
            INITIAL_REQUIREMENTS_KEY,
            INITIAL_SCORING_CRITERIA_KEY
        ])
        
        if not validation_result["is_valid"]:
            return {
                "status": "error",
                "message": f"缺少必要的输入数据: {validation_result['missing_keys']}"
            }
        
        # 获取必要数据
        material = state_manager.get(INITIAL_MATERIAL_KEY)
        requirements = state_manager.get(INITIAL_REQUIREMENTS_KEY)
        criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY)
        
        logger.info(f"准备文稿生成。素材长度:{len(material)}，要求长度:{len(requirements)}，评分标准长度:{len(criteria)}")
        
        # 构建提示词
        prompt = INITIAL_WRITING_PROMPT_TEMPLATE.format(
            material=material,
            requirements=requirements,
            scoring_criteria=criteria
        )
        
        # 存储并记录LLM提示词
        tool_context.state['LLM_LAST_PROMPT'] = prompt
        log_llm_generation(state_manager.get(ITERATION_COUNT_KEY, 0), prompt, "", tool_name="generate_initial_draft")
        
        # 使用备用文本，以防LLM调用失败
        backup_draft = _get_backup_draft()
        
        # 当前迭代计数
        iteration_count = state_manager.get(ITERATION_COUNT_KEY, 0)
        
        try:
            # ===使用ADK标准方式调用LLM===
            # 注意：不再直接创建LiteLlm实例，而是直接返回提示词，
            # 由Agent自己的LLM机制处理生成
            
            # 直接将提示词作为结果返回，供Agent处理
            return {
                "status": "llm_prompt_ready",
                "prompt": prompt,
                "iteration": iteration_count
            }
            
        except Exception as e:
            logger.error(f"生成文稿提示词时出错: {e}", exc_info=True)
            return {
                "status": "error", 
                "message": f"生成文稿提示词时出错: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"generate_initial_draft工具执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"工具执行失败: {str(e)}"
        }

def save_draft_result(content: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    保存LLM生成的文稿内容到会话状态。
    
    此工具负责将Agent生成的文稿内容持久化到会话状态，
    并更新相关元数据。
    
    Args:
        content: LLM生成的文稿内容
        tool_context: ADK工具上下文，用于访问会话状态
        
    Returns:
        dict: 包含操作状态和文稿摘要的字典
    """
    logger.info("保存LLM生成的文稿内容...")
    logger.info(f"接收到的文稿内容摘要: {content[:100]}..., 长度: {len(content)}")
    logger.info(f"Tool Context 状态对象是否存在: {tool_context.state is not None}")
    logger.info(f"Tool Context 状态类型: {type(tool_context.state)}")
    logger.info(f"Tool Context 状态内容: {str(tool_context.state)[:200]}...")
    
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        logger.info(f"StateManager初始化完成，状态对象: {state_manager.state is not None}")
        
        # 获取当前迭代计数
        iteration_count = state_manager.get(ITERATION_COUNT_KEY, 0)
        
        # 保存文稿内容
        save_result = state_manager.store_draft_efficiently(content)
        logger.info(f"文稿保存结果: {save_result}")
        
        # 每次保存文稿都递增iteration_count
        state_manager.set(ITERATION_COUNT_KEY, iteration_count + 1)
        
        # 再次检查保存是否成功
        current_draft = state_manager.get(CURRENT_DRAFT_KEY)
        if not current_draft:
            # 备用保存方式：直接使用工具上下文保存
            logger.warning("使用StateManager保存失败，尝试备用直接保存方式")
            tool_context.state[CURRENT_DRAFT_KEY] = content
            if CURRENT_DRAFT_KEY in tool_context.state:
                logger.info("备用保存成功")
                save_result = True
                
                # 确保设置迭代计数
                if ITERATION_COUNT_KEY not in tool_context.state:
                    logger.info("设置初始迭代计数")
                    tool_context.state[ITERATION_COUNT_KEY] = 1
                    
                # 更新迭代计数引用
                iteration_count = tool_context.state.get(ITERATION_COUNT_KEY, 1)
        
        if save_result:
            logger.info(f"成功将文稿（{len(content)}字符）保存到状态。")
            
            # 再次检查保存是否成功
            saved_draft = None
            if state_manager.state.get(CURRENT_DRAFT_KEY):
                saved_draft = state_manager.state.get(CURRENT_DRAFT_KEY)
            elif tool_context.state.get(CURRENT_DRAFT_KEY):
                saved_draft = tool_context.state.get(CURRENT_DRAFT_KEY)
                
            logger.info(f"验证保存: 保存后的文稿长度 = {len(saved_draft) if saved_draft else 0}")
            
            # 记录生成事件
            log_generation_event("draft_saved", {
                "preview": content[:100] + "..." if len(content) > 100 else content
            }, {
                "length": len(content),
                "iteration": iteration_count
            })
            
            # 记录LLM生成输出及对应提示词
            last_prompt = tool_context.state.get('LLM_LAST_PROMPT', '')
            log_llm_generation(iteration_count, last_prompt, content, tool_name="save_draft_result")
            
            # 返回摘要信息
            return {
                "status": "success",
                "draft_summary": content[:100] + "..." if len(content) > 100 else content,
                "draft_length": len(content),
                "iteration": iteration_count
            }
        else:
            logger.error("文稿保存失败")
            return {
                "status": "error",
                "message": "文稿保存到状态失败"
            }
    except Exception as e:
        logger.error(f"save_draft_result工具执行失败: {e}", exc_info=True)
        
        # 出现异常时的备用保存机制
        try:
            logger.warning("尝试在异常处理中直接保存文稿")
            tool_context.state[CURRENT_DRAFT_KEY] = content
            tool_context.state[ITERATION_COUNT_KEY] = tool_context.state.get(ITERATION_COUNT_KEY, 0) + 1
            
            if CURRENT_DRAFT_KEY in tool_context.state:
                logger.info("异常处理中的备用保存成功")
                return {
                    "status": "success",
                    "draft_summary": content[:100] + "..." if len(content) > 100 else content,
                    "draft_length": len(content),
                    "iteration": tool_context.state.get(ITERATION_COUNT_KEY, 1),
                    "note": "通过异常处理的备用机制保存"
                }
        except Exception as backup_error:
            logger.error(f"备用保存也失败: {backup_error}")
            
        return {
            "status": "error",
            "message": f"保存文稿失败: {str(e)}"
        }

def generate_draft_scoring(tool_context: ToolContext) -> Dict[str, Any]:
    """
    生成文稿评分提示词，基于当前文稿和评分标准。
    
    此工具从会话状态读取当前文稿和评分标准，
    构建评分提示词供Agent处理。
    
    Args:
        tool_context: ADK工具上下文，用于访问会话状态
        
    Returns:
        dict: 包含操作状态和提示词的字典
    """
    logger.info("启动文稿评分工具...")
    
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 验证必要的输入数据
        draft_metadata = state_manager.get_draft_metadata()
        if not draft_metadata["exists"]:
            return {
                "status": "error",
                "message": "找不到当前文稿，无法生成评分提示词"
            }
        
        # 获取必要数据
        draft = state_manager.get(CURRENT_DRAFT_KEY)
        criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "")
        
        logger.info(f"准备文稿评分。文稿长度:{len(draft)}，评分标准长度:{len(criteria)}")
        
        # 构建提示词
        prompt = SCORING_PROMPT_TEMPLATE.format(
            draft=draft,
            scoring_criteria=criteria
        )
        
        # 直接将提示词作为结果返回，供Agent处理
        return {
            "status": "llm_prompt_ready",
            "prompt": prompt,
            "action": "scoring"
        }
            
    except Exception as e:
        logger.error(f"generate_draft_scoring工具执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"工具执行失败: {str(e)}"
        }

def save_scoring_result(score: float, feedback: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    保存LLM生成的评分结果到会话状态。
    
    此工具负责将Agent生成的评分和反馈持久化到会话状态，
    并更新相关元数据。
    
    Args:
        score: 评分(0-10)
        feedback: 评价反馈
        tool_context: ADK工具上下文，用于访问会话状态
        
    Returns:
        dict: 包含操作状态和评分信息的字典
    """
    logger.info("保存LLM生成的评分结果...")
    logger.info(f"接收到的评分: {score}, 反馈长度: {len(feedback)}")
    logger.info(f"Tool Context 状态对象是否存在: {tool_context.state is not None}")
    
    try:
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 验证评分的合法性
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            return {
                "status": "error",
                "message": f"评分无效: {score}，必须是0-10之间的数字"
            }
        
        # 四舍五入到1位小数
        rounded_score = round(float(score), 1)
        
        # 保存结果
        keys_to_update = {
            CURRENT_SCORE_KEY: rounded_score,
            CURRENT_FEEDBACK_KEY: feedback
        }
        
        # 获取当前分数阈值，如果没有则使用默认值
        score_threshold = state_manager.get(SCORE_THRESHOLD_KEY, 90)
        
        # 判断是否达到完成标准
        is_complete = rounded_score >= score_threshold
        keys_to_update[IS_COMPLETE_KEY] = is_complete
        
        # 批量更新
        update_results = state_manager.update(keys_to_update)
        
        # 检查更新结果
        update_success = all(update_results.values())
        
        # 备用保存：如果状态管理器更新失败，直接使用tool_context.state保存
        if not update_success:
            logger.warning("通过StateManager保存失败，尝试备用保存方式")
            try:
                # 直接保存到state
                tool_context.state[CURRENT_SCORE_KEY] = rounded_score
                tool_context.state[CURRENT_FEEDBACK_KEY] = feedback
                tool_context.state[IS_COMPLETE_KEY] = is_complete
                
                # 验证保存
                if (CURRENT_SCORE_KEY in tool_context.state and 
                    CURRENT_FEEDBACK_KEY in tool_context.state and 
                    IS_COMPLETE_KEY in tool_context.state):
                    logger.info("备用保存成功")
                    update_success = True
            except Exception as backup_error:
                logger.error(f"备用保存失败: {backup_error}")
        
        if update_success:
            # 记录评分结果
            log_generation_event("scoring_saved", {
                "score": rounded_score,
                "feedback": feedback[:100] + "..." if len(feedback) > 100 else feedback
            }, {
                "is_complete": is_complete,
                "threshold": score_threshold
            })
            
            return {
                "status": "success",
                "score": rounded_score,
                "feedback_preview": feedback[:100] + "..." if len(feedback) > 100 else feedback,
                "is_complete": is_complete,
                "score_threshold": score_threshold
            }
        else:
            # 每个失败的键
            failed_keys = [key for key, success in update_results.items() if not success]
            error_msg = f"保存失败的键: {', '.join(failed_keys)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    except Exception as e:
        logger.error(f"save_scoring_result工具执行失败: {e}", exc_info=True)
        
        # 出现异常时的备用保存机制
        try:
            logger.warning("尝试在异常处理中直接保存评分结果")
            # 四舍五入到1位小数
            rounded_score = round(float(score), 1)
            
            # 直接保存到状态
            tool_context.state[CURRENT_SCORE_KEY] = rounded_score
            tool_context.state[CURRENT_FEEDBACK_KEY] = feedback
            
            # 获取当前分数阈值，如果没有则使用默认值
            score_threshold = tool_context.state.get(SCORE_THRESHOLD_KEY, 90)
            
            # 判断是否达到完成标准
            is_complete = rounded_score >= score_threshold
            tool_context.state[IS_COMPLETE_KEY] = is_complete
            
            if (CURRENT_SCORE_KEY in tool_context.state and 
                CURRENT_FEEDBACK_KEY in tool_context.state):
                logger.info("异常处理中的备用保存成功")
                return {
                    "status": "success",
                    "score": rounded_score,
                    "feedback_preview": feedback[:100] + "..." if len(feedback) > 100 else feedback,
                    "is_complete": is_complete,
                    "score_threshold": score_threshold,
                    "note": "通过异常处理的备用机制保存"
                }
        except Exception as backup_error:
            logger.error(f"备用保存也失败: {backup_error}")
        
        return {
            "status": "error",
            "message": f"保存评分结果失败: {str(e)}"
        }

def _get_backup_draft() -> str:
    """
    生成备用草稿内容，用于LLM调用失败的情况。
    
    Returns:
        str: 备用草稿内容
    """
    backup_draft = "AI写作工具的优点包括：\n"
    backup_draft += "1. 提高效率：AI工具可以快速生成内容，节省大量时间\n"
    backup_draft += "2. 辅助创作：可以帮助克服写作障碍，提供创意灵感\n"
    backup_draft += "3. 多语言支持：能够翻译和生成多种语言的内容\n"
    backup_draft += "4. 创意激发：提供不同角度的思考和表达方式\n\n"
    backup_draft += "AI写作工具的缺点包括：\n"
    backup_draft += "1. 缺乏深度：生成内容有时缺乏深度和独特见解\n"
    backup_draft += "2. 格式和风格限制：难以完全掌握特定领域的写作风格\n"
    backup_draft += "3. 事实准确性问题：可能生成不准确或过时的信息\n"
    backup_draft += "4. 缺乏个性化：生成内容可能缺乏作者独特的个人风格\n"
    return backup_draft 