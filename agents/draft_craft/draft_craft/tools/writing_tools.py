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

"""写作工具，扁平化实现，负责生成写作/改进提示词。"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext
import os

from .state_manager import (
    StateManager, INITIAL_MATERIAL_KEY, INITIAL_REQUIREMENTS_KEY,
    INITIAL_SCORING_CRITERIA_KEY, CURRENT_DRAFT_KEY, CURRENT_SCORE_KEY,
    CURRENT_FEEDBACK_KEY, ITERATION_COUNT_KEY, IS_COMPLETE_KEY
)
from .logging_utils import log_generation_event, log_llm_generation # Keep log_llm_generation for prompt logging

logger = logging.getLogger(__name__)

# 提示词模板 (Moved from llm_tools.py)
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

def write_draft(tool_context: ToolContext) -> dict:
    """
    生成写作或改进文稿的提示词。

    基于会话状态，该工具将：
    1. 如果是首次撰写（无current_draft），生成基于初始素材和要求的写作提示词。
    2. 如果已有文稿和反馈，则生成基于反馈改进当前文稿的提示词。

    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问

    Returns:
        dict: 包含状态（llm_prompt_ready）和生成提示词的字典。
    """
    try:
        state_manager = StateManager(tool_context)
        iteration_count = state_manager.get(ITERATION_COUNT_KEY, 0) # 获取迭代计数用于日志

        current_draft = state_manager.get(CURRENT_DRAFT_KEY)
        feedback = state_manager.get(CURRENT_FEEDBACK_KEY)

        if not current_draft:
            # 首次撰写：生成初始写作提示词
            logger.info("生成初始文稿的提示词...")
            material = state_manager.get(INITIAL_MATERIAL_KEY)
            requirements = state_manager.get(INITIAL_REQUIREMENTS_KEY)
            criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY)

            if not all([material, requirements, criteria]):
                 missing = [k for k, v in {INITIAL_MATERIAL_KEY: material, INITIAL_REQUIREMENTS_KEY: requirements, INITIAL_SCORING_CRITERIA_KEY: criteria}.items() if not v]
                 logger.error(f"缺少生成初始文稿提示词所需的键: {missing}")
                 return {"status": "error", "message": f"缺少初始数据: {', '.join(missing)}"}

            prompt = INITIAL_WRITING_PROMPT_TEMPLATE.format(
                material=material,
                requirements=requirements,
                scoring_criteria=criteria
            )
            action = "initial_writing"
            log_generation_event("initial_prompt_generated", {"preview": prompt[:100]}, {"length": len(prompt)})

        else:
            # 改进阶段：生成改进提示词
            logger.info(f"生成改进文稿的提示词 (迭代 {iteration_count})...")
            criteria = state_manager.get(INITIAL_SCORING_CRITERIA_KEY, "") # 获取评分标准用于提示词

            prompt = REVISION_PROMPT_TEMPLATE.format(
                current_draft=current_draft,
                feedback=feedback if feedback else "没有具体反馈，请对文稿进行一般性改进，使其更全面、更有深度。",
                scoring_criteria=criteria
            )
            action = "revision_writing"
            log_generation_event("revision_prompt_generated", {"preview": prompt[:100]}, {"length": len(prompt)})

        # 记录将要发送给LLM的提示词
        # 注意：这里记录的是提示词本身，而不是LLM的输出
        log_llm_generation(iteration_count, prompt, "", tool_name="write_draft")
        tool_context.state['LLM_LAST_PROMPT'] = prompt # 保存最后生成的提示词，供save_draft_result记录

        return {
            "status": "llm_prompt_ready",
            "prompt": prompt,
            "action": action # 区分是初始写作还是修订
        }

    except Exception as e:
        logger.error(f"write_draft工具执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"生成写作/改进提示词时发生错误: {str(e)}"
        }

# 移除 _generate_with_llm 和 _generate_mock_content 函数

# score_draft 和 check_progress 函数保持不变 (如果它们存在且需要的话)
# 但根据日志，这两个函数似乎在其他文件中（llm_tools.py, state_tools.py）？
# 如果需要，确认保留或移除

def score_draft(tool_context: ToolContext) -> dict:
    """
    评估当前文稿，提供分数和反馈。(此函数似乎不再需要，因为有专门的评分工具)
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含评分、反馈和状态信息的字典
    """
    logger.warning("score_draft in writing_tools.py is likely deprecated. Use specific scoring tools.")
    # 保留一个基础实现或直接返回错误
    return {
        "status": "error",
        "message": "score_draft in writing_tools.py is deprecated. Use specific scoring tools like score_for_parents."
    }


def check_progress(tool_context: ToolContext) -> dict:
    """
    检查写作进度，决定是继续迭代还是完成流程。(此函数似乎在 state_tools.py 中实现)
    
    Args:
        tool_context: ADK工具上下文，提供对会话状态的访问
    
    Returns:
        dict: 包含进度状态和决策信息的字典
    """
    logger.warning("check_progress in writing_tools.py is likely deprecated. Use the version from state_tools.")
    # 保留一个基础实现或直接返回错误
    return {
        "status": "error",
        "message": "check_progress in writing_tools.py is deprecated. Use the version from state_tools."
    }

# _safely_call_async_api 似乎也不再需要，因为不直接调用LLM
# def _safely_call_async_api(...):
#    ... 