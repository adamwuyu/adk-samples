"""LLM内容生成器，提供LLM文本生成功能。"""

import logging
import os
from typing import Any, Dict, List, Optional, Union
from google.adk.models.lite_llm import LiteLlm

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


class LlmContentGenerator:
    """使用LLM生成文本内容的生成器类"""
    
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.7):
        """
        初始化LLM生成器
        
        Args:
            model_name: 要使用的模型名称，如果不指定则使用环境配置
            temperature: 生成温度，控制创造性，默认0.7
        """
        self.model = self._setup_model(model_name, temperature)
        self.temperature = temperature  # 保存温度参数作为类的属性
        logger.info(f"LLM内容生成器初始化完成，使用模型: {self.model}")
    
    def _setup_model(self, model_name: Optional[str], temperature: float) -> LiteLlm:
        """
        配置LLM模型，优先使用gpt-4.1-mini（kingdora优先），否则gpt-4o，否则抛出异常。
        """
        kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
        kingdora_api_key = os.getenv("KINGDORA_API_KEY")
        oneapi_base_url = os.getenv("ONEAPI_BASE_URL")
        oneapi_api_key = os.getenv("ONEAPI_API_KEY")

        if kingdora_base_url and kingdora_api_key:
            try:
                return LiteLlm(
                    model="openai/gpt-4.1-mini",
                    api_base=kingdora_base_url,
                    api_key=kingdora_api_key,
                )
            except Exception as e:
                logger.error(f"配置gpt-4.1-mini模型时出错: {e}")
                raise
        elif oneapi_base_url and oneapi_api_key:
            try:
                return LiteLlm(
                    model="openai/gpt-4o",
                    api_base=oneapi_base_url,
                    api_key=oneapi_api_key,
                )
            except Exception as e:
                logger.error(f"配置gpt-4o模型时出错: {e}")
                raise
        else:
            logger.error("未找到有效的LLM服务配置，无法初始化LLM实例。请设置KINGDORA或ONEAPI相关环境变量。")
            raise RuntimeError("未找到有效的LLM服务配置，无法初始化LLM实例。请设置KINGDORA或ONEAPI相关环境变量。")
    
    async def generate_initial_draft(
        self, 
        material: str, 
        requirements: str, 
        scoring_criteria: str
    ) -> str:
        """
        生成初始文稿
        
        Args:
            material: 写作素材
            requirements: 写作要求
            scoring_criteria: 评分标准
            
        Returns:
            生成的文稿内容
        """
        prompt = INITIAL_WRITING_PROMPT_TEMPLATE.format(
            material=material,
            requirements=requirements,
            scoring_criteria=scoring_criteria
        )
        
        logger.info("请求LLM生成初始文稿")
        try:
            # 调用LLM生成内容
            if isinstance(self.model, str):
                # 使用ADK自身的LLM处理机制 - 这部分需要根据ADK的具体API调整
                response = "由于当前使用字符串模型配置，无法进行异步调用。请在实际使用时提供完整的LLM实例。"
                logger.warning("使用了字符串模型名称，无法执行实际生成。这是一个占位实现。")
            else:
                # 使用配置好的LiteLlm实例 - 使用litellm.completion方法
                try:
                    # 创建消息格式
                    messages = [{"role": "user", "content": prompt}]
                    
                    # 使用litellm的completion方法(异步版)
                    response = await self.model.completion_async(
                        model=self.model.model,
                        messages=messages,
                        temperature=self.temperature  # 使用类属性而不是从model获取
                    )
                except AttributeError:
                    # 如果不存在异步方法，退回到使用同步方法
                    logger.warning("LiteLLM对象未提供异步方法，回退到同步调用")
                    import litellm
                    response = litellm.completion(
                        model=self.model.model,
                        messages=messages,
                        temperature=self.temperature  # 使用类属性而不是从model获取
                    )
                
                # 从标准格式中提取文本内容
                response_text = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
                response = response_text
            
            logger.info(f"成功生成初始文稿，长度: {len(response)}字符")
            return response
        except Exception as e:
            logger.error(f"生成初始文稿时出错: {e}", exc_info=True)
            return f"生成文稿失败: {e}。请重试或检查LLM配置。"
    
    def generate_initial_draft_sync(
        self, 
        material: str, 
        requirements: str, 
        scoring_criteria: str
    ) -> str:
        """
        同步版本的初始文稿生成器
        
        Args:
            material: 写作素材
            requirements: 写作要求
            scoring_criteria: 评分标准
            
        Returns:
            生成的文稿内容
        """
        prompt = INITIAL_WRITING_PROMPT_TEMPLATE.format(
            material=material,
            requirements=requirements,
            scoring_criteria=scoring_criteria
        )
        
        logger.info("请求LLM同步生成初始文稿")
        try:
            # 调用LLM生成内容
            if isinstance(self.model, str):
                # 使用ADK自身的LLM处理机制 - 这部分需要根据ADK的具体API调整
                response = f"由于当前使用字符串模型配置({self.model})，无法进行同步调用。请在实际使用时提供完整的LLM实例。"
                logger.warning(f"使用了字符串模型名称({self.model})，无法执行实际生成。这是一个占位实现。")
            else:
                # 使用配置好的LiteLlm实例，使用litellm.completion方法
                import litellm
                # 创建消息格式
                messages = [{"role": "user", "content": prompt}]
                
                response = litellm.completion(
                    model=self.model.model,
                    messages=messages,
                    temperature=self.temperature  # 使用类属性而不是从model获取
                )
                
                # 从标准格式中提取文本内容
                response_text = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
                response = response_text
            
            logger.info(f"成功生成初始文稿，长度: {len(response)}字符")
            return response
        except Exception as e:
            logger.error(f"同步生成初始文稿时出错: {e}", exc_info=True)
            return f"生成文稿失败: {e}。请重试或检查LLM配置。"
    
    async def improve_draft(
        self, 
        current_draft: str, 
        feedback: str, 
        scoring_criteria: str
    ) -> str:
        """
        基于反馈改进现有文稿
        
        Args:
            current_draft: 当前文稿
            feedback: 评分反馈
            scoring_criteria: 评分标准
            
        Returns:
            改进后的文稿
        """
        prompt = REVISION_PROMPT_TEMPLATE.format(
            current_draft=current_draft,
            feedback=feedback,
            scoring_criteria=scoring_criteria
        )
        
        logger.info("请求LLM改进文稿")
        try:
            # 调用LLM生成内容
            if isinstance(self.model, str):
                # 使用ADK自身的LLM处理机制 - 占位实现
                response = current_draft + "\n\n[此处为改进内容的占位符 - 实际使用时会替换为真实生成内容]"
                logger.warning("使用了字符串模型名称，无法执行实际生成。返回占位内容。")
            else:
                # 使用配置好的LiteLlm实例 - 使用litellm.completion方法
                try:
                    # 创建消息格式
                    messages = [{"role": "user", "content": prompt}]
                    
                    # 使用litellm的completion方法(异步版)
                    response = await self.model.completion_async(
                        model=self.model.model,
                        messages=messages,
                        temperature=self.temperature  # 使用类属性而不是从model获取
                    )
                except AttributeError:
                    # 如果不存在异步方法，退回到使用同步方法
                    logger.warning("LiteLLM对象未提供异步方法，回退到同步调用")
                    import litellm
                    response = litellm.completion(
                        model=self.model.model,
                        messages=messages,
                        temperature=self.temperature  # 使用类属性而不是从model获取
                    )
                
                # 从标准格式中提取文本内容
                response_text = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
                response = response_text
            
            logger.info(f"成功改进文稿，新长度: {len(response)}字符")
            return response
        except Exception as e:
            logger.error(f"改进文稿时出错: {e}", exc_info=True)
            return current_draft + f"\n\n[文稿改进失败: {e}]"
            
    def improve_draft_sync(
        self, 
        current_draft: str, 
        feedback: str, 
        scoring_criteria: str
    ) -> str:
        """
        同步版本的基于反馈改进现有文稿
        
        Args:
            current_draft: 当前文稿
            feedback: 评分反馈
            scoring_criteria: 评分标准
            
        Returns:
            改进后的文稿
        """
        prompt = REVISION_PROMPT_TEMPLATE.format(
            current_draft=current_draft,
            feedback=feedback,
            scoring_criteria=scoring_criteria
        )
        
        logger.info("请求LLM同步改进文稿")
        try:
            # 调用LLM生成内容
            if isinstance(self.model, str):
                # 使用ADK自身的LLM处理机制 - 占位实现
                response = current_draft + f"\n\n[此处为改进内容的占位符 - 实际使用时会通过{self.model}替换为真实生成内容]"
                logger.warning(f"使用了字符串模型名称({self.model})，无法执行实际生成。返回占位内容。")
            else:
                # 使用配置好的LiteLlm实例，使用litellm.completion方法
                import litellm
                # 创建消息格式
                messages = [{"role": "user", "content": prompt}]
                
                response = litellm.completion(
                    model=self.model.model,
                    messages=messages,
                    temperature=self.temperature  # 使用类属性而不是从model获取
                )
                
                # 从标准格式中提取文本内容
                response_text = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
                response = response_text
            
            logger.info(f"成功改进文稿，新长度: {len(response)}字符")
            return response
        except Exception as e:
            logger.error(f"同步改进文稿时出错: {e}", exc_info=True)
            return current_draft + f"\n\n[文稿同步改进失败: {e}]"

# 创建全局实例以便重用
content_generator = None

def get_content_generator(temperature: float = 0.7) -> LlmContentGenerator:
    """
    获取或创建LLM内容生成器实例
    
    Args:
        temperature: 生成温度
        
    Returns:
        LlmContentGenerator实例
    """
    global content_generator
    if content_generator is None:
        content_generator = LlmContentGenerator(temperature=temperature)
    return content_generator 