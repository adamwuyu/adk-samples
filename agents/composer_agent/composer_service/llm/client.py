import os
from dotenv import load_dotenv
from typing import Optional

# 假设 LiteLlm 已在项目依赖中，若无需自定义实现则直接导入
from google.adk.models.lite_llm import LiteLlm
import logging

load_dotenv()

def get_llm_client() -> 'LiteLlm':
    """
    获取配置好的 LiteLlm 实例。
    环境变量：KINGDORA_BASE_URL, KINGDORA_API_KEY
    固定模型：openai/gpt-4.1-mini
    """
    kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
    kingdora_api_key = os.getenv("KINGDORA_API_KEY")
    if not kingdora_base_url or not kingdora_api_key:
        logging.error("KINGDORA_BASE_URL 或 KINGDORA_API_KEY 环境变量未设置")
        raise EnvironmentError("KINGDORA_BASE_URL 或 KINGDORA_API_KEY 环境变量未设置")
    if LiteLlm is None:
        raise ImportError("LiteLlm 包未安装，请先安装依赖")
    return LiteLlm(
        model="openai/gpt-4.1-mini",
        api_base=kingdora_base_url,
        api_key=kingdora_api_key,
        stream=False,
        temperature=0.2
    ) 