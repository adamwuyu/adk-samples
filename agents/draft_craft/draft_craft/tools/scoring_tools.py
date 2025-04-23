from google.adk.tools import FunctionTool
from typing import Dict, List, Any, Optional
import logging
import re
from google.adk.tools.tool_context import ToolContext

from .logging_utils import log_generation_event
from .state_manager import (
    StateManager, CURRENT_SCORE_KEY, CURRENT_FEEDBACK_KEY, 
    IS_COMPLETE_KEY, SCORE_THRESHOLD_KEY
)

# 配置日志
logger = logging.getLogger(__name__)

# 评分工具：面向"中等家长"受众

# 评分提示词模板
PARENTS_SCORING_PROMPT_TEMPLATE = """
你现在要扮演一位中等受教育水平、经济中等以上的家长，孩子处于小学高年级至高中一年级阶段。
请严格按照以下要点对下方文章进行评分和反馈：

## 评分标准
{scoring_criteria}

## 待评文章
{draft_content}

【评分要求】
- 分数（0-100之间的整数）：请基于内容相关性、案例丰富度、结构清晰度、语言实用性和家长关注点给出。
- 详细评价（200-300字）：综合分析文章的优缺点，并给出具体可操作的改进建议，涵盖案例、结构、语言等关键方面。
- 关键问题（2-3条，每条以"-"开头）：列出最需要改进的2到3个要点，确保可执行性。

请从目标家长的视角出发，以清晰、简洁的格式输出这三部分内容，不要添加其他多余说明或编号列表。
"""

def score_for_parents(
    draft_content: str,
    audience_profile: str,
    scoring_criteria: str,
    tool_context: Optional[ToolContext] = None
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
    # 日志记录
    logger.info(f"开始对文稿进行评分，文稿长度: {len(draft_content)}")
    logger.warning("[SCORING_DEBUG] 开始对文稿进行评分...")
    
    # 保留特殊情况的快速返回逻辑
    if not draft_content.strip():
        logger.warning("文稿内容为空，直接返回低分结果")
        return {
            "score": 0,
            "feedback": "内容为空，请补充文稿内容。",
            "key_issues": ["内容为空"]
        }
        
    # 构建提示词
    prompt = PARENTS_SCORING_PROMPT_TEMPLATE.format(
        audience_profile=audience_profile,
        scoring_criteria=scoring_criteria,
        draft_content=draft_content
    )
    
    # 如果提供了工具上下文，记录评分事件
    if tool_context:
        log_generation_event("scoring_prompt_generated", {
            "prompt_preview": prompt[:100] + "...",
            "draft_length": len(draft_content)
        }, {
            "audience_type": "parents"
        })
    print("[SCORING_DEBUG] score_for_parents prompt:", prompt[:200])
    # 返回提示词，供Agent处理
    return {
        "status": "llm_prompt_ready",
        "prompt": prompt,
        "audience_type": "parents"
    }

def parse_scoring_result(llm_output: str) -> Dict[str, Any]:
    """
    解析LLM生成的评分结果，提取分数、反馈和关键问题
    
    Args:
        llm_output: LLM生成的评分输出
        
    Returns:
        字典，包含解析后的score、feedback和key_issues
    """
    logger.info("开始解析评分结果...")
    logger.info(f"LLM输出内容摘要: {llm_output[:100]}..., 长度: {len(llm_output)}")
    
    # 默认结果
    result = {
        "score": 60,  # 默认中等分数
        "feedback": llm_output,  # 默认使用全部输出作为反馈
        "key_issues": []  # 默认无关键问题
    }
    
    try:
        # 优先匹配"1. 数字"格式
        score_match = re.search(r'1\.\s*([1-9][0-9]?|100)\b', llm_output)
        if score_match:
            score = int(score_match.group(1))
            if 0 <= score <= 100:
                result["score"] = score
                logger.info(f"解析到分数: {score}")
        else:
            # 兜底：匹配第一个0-100的独立整数
            score_match = re.search(r'\b([1-9][0-9]?|100)\b', llm_output)
            if score_match:
                score = int(score_match.group(1))
                result["score"] = score
                logger.info(f"兜底解析到分数: {score}")
        
        # 提取关键问题 (尝试匹配"-"开头的列表项)
        key_issues = []
        for line in llm_output.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('- '):
                issue = line.lstrip('- ').strip()
                if issue and len(issue) > 5:  # 确保不是空行或过短的内容
                    key_issues.append(issue)
        
        if key_issues:
            result["key_issues"] = key_issues
            logger.info(f"解析到{len(key_issues)}个关键问题")
        
        # 提取反馈 (使用除了明确的分数和关键问题列表外的内容)
        # 这是个简化处理，实际中可能需要更复杂的逻辑
        if score_match:
            feedback_text = llm_output
            # 从反馈中排除可能的分数行
            score_line_match = re.search(r'^.*?\b\d{1,3}\b.*?$', llm_output, re.MULTILINE)
            if score_line_match:
                score_line = score_line_match.group(0)
                feedback_text = feedback_text.replace(score_line, '', 1).strip()
            
            result["feedback"] = feedback_text
            logger.info(f"提取的反馈长度: {len(feedback_text)}")
    
    except Exception as e:
        logger.error(f"解析评分结果出错: {e}", exc_info=True)
        # 出错时保留默认结果
    
    return result

def save_parents_scoring_result(
    llm_output: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    解析并保存LLM生成的评分结果到状态
    
    此工具负责从LLM输出中提取评分、反馈和关键问题，
    并将结果保存到会话状态中
    
    Args:
        llm_output: LLM生成的评分输出
        tool_context: ADK工具上下文，用于访问会话状态
        
    Returns:
        dict: 包含操作状态和评分摘要的字典
    """
    print("[SCORING_DEBUG] llm_output内容:", repr(llm_output))
    logger.warning("[SCORING_DEBUG] 开始保存家长视角评分结果...")
    logger.warning(f"[SCORING_DEBUG] 摘要: {llm_output[:100]}..., 长度: {len(llm_output)}")
    
    try:
        # 解析LLM输出
        parsed_result = parse_scoring_result(llm_output)
        score = parsed_result["score"]
        logger.warning(f"[SCORING_DEBUG] score: {score}")
        feedback = parsed_result["feedback"]
        key_issues = parsed_result["key_issues"]
        
        logger.info(f"解析结果 - 分数: {score}, 反馈长度: {len(feedback)}, 问题数量: {len(key_issues)}")
        
        # 使用状态管理器
        state_manager = StateManager(tool_context)
        
        # 保存评分结果
        state_manager.set(CURRENT_SCORE_KEY, float(score))
        state_manager.set(CURRENT_FEEDBACK_KEY, feedback)
        
        # 获取分数阈值
        score_threshold = state_manager.get(SCORE_THRESHOLD_KEY, 90)
        
        # 确定是否完成
        is_complete = score >= score_threshold
        if is_complete:
            logger.info(f"分数 {score} 已达到或超过阈值 {score_threshold}，标记为完成")
            state_manager.set(IS_COMPLETE_KEY, True)
        
        # 记录评分事件
        log_generation_event("scoring_saved", {
            "score": score,
            "feedback_preview": feedback[:100] + "..." if len(feedback) > 100 else feedback,
        }, {
            "key_issues_count": len(key_issues),
            "is_complete": is_complete,
            "threshold": score_threshold
        })
        
        # 返回摘要信息
        return {
            "status": "success",
            "score": score,
            "feedback_summary": feedback[:100] + "..." if len(feedback) > 100 else feedback,
            "key_issues": key_issues,
            "is_complete": is_complete,
            "threshold": score_threshold
        }
    
    except Exception as e:
        logger.error(f"保存评分结果失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"保存评分结果失败: {str(e)}"
        }

# 注册工具
score_for_parents_tool = FunctionTool(func=score_for_parents)
save_parents_scoring_result_tool = FunctionTool(func=save_parents_scoring_result) 