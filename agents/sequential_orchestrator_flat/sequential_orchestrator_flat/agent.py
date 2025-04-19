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

"""扁平化实现的Sequential Orchestrator主Agent。"""

import os
import logging
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

from .prompt import ROOT_AGENT_INSTRUCTION
from .tools import (
    check_initial_data,
    store_initial_data,
    check_progress,
    get_final_draft
)
from .tools.llm_tools import (
    generate_initial_draft,
    save_draft_result,
    generate_draft_improvement,
    generate_draft_scoring,
    save_scoring_result
)

logger = logging.getLogger(__name__)

# --- 加载环境变量 ---
# 计算agent.py文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 推算agents目录的路径(向上两级)
agents_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
# 拼接.env文件路径
dotenv_path = os.path.join(agents_dir, '.env')

# 加载.env文件，如果存在
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"已从{dotenv_path}加载.env")
else:
    logger.warning(f"警告 - 在{dotenv_path}找不到.env文件，依赖环境变量或其他dotenv加载。")
    # 如果找不到，尝试默认加载，以防变量已在环境中设置
    load_dotenv()

# --- 配置LLM实例 ---
model_instance = None
oneapi_base_url = os.getenv("ONEAPI_BASE_URL")
oneapi_api_key = os.getenv("ONEAPI_API_KEY")
kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
kingdora_api_key = os.getenv("KINGDORA_API_KEY")

# 优先尝试配置GPT-4o模型
if oneapi_base_url and oneapi_api_key:
    try:
        model_instance = LiteLlm(
            model="openai/gpt-4o", 
            api_base=oneapi_base_url,
            api_key=oneapi_api_key,
            stream=True
        )
        logger.info("✅ 成功配置GPT-4o模型")
    except Exception as e:
        logger.error(f"❌ 配置GPT模型时出错: {e}")

# 如果GPT-4o配置失败，尝试配置Gemini模型
if not model_instance and kingdora_base_url and kingdora_api_key:
    try:
        model_instance = LiteLlm(
            model="openai/gemini-2.5-flash-preview-04-17",
            api_base=kingdora_base_url,
            api_key=kingdora_api_key,
            stream=True,
            temperature=0.2
        )
        logger.info("✅ 成功配置Gemini模型")
    except Exception as e:
        logger.error(f"❌ 配置Gemini模型时出错: {e}")

# 如果无法配置任何模型，使用默认模型
if not model_instance:
    logger.warning("⚠️ 未找到模型配置，使用默认GPT模型")
    model_instance = "openai/gpt-4o-mini"

# --- 定义Root Agent ---
# 扁平化设计：单一Agent + 完整Tool集，不使用循环或嵌套Agent
root_agent = Agent(
    model=model_instance,
    name="writing_scoring_agent",
    description="帮助用户撰写并评估文稿，通过迭代流程优化内容直至达到要求。",
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[
        # 初始化工具
        FunctionTool(func=check_initial_data),
        FunctionTool(func=store_initial_data),
        
        # V0.9: 新版LLM工具 - 符合ADK标准架构
        FunctionTool(func=generate_initial_draft),
        FunctionTool(func=save_draft_result),
        FunctionTool(func=generate_draft_improvement),
        
        # V0.9: 新版LLM评分工具 - 符合ADK标准架构
        FunctionTool(func=generate_draft_scoring),
        FunctionTool(func=save_scoring_result),
        
        # 流程控制工具
        FunctionTool(func=check_progress),
        
        # 结果获取工具
        FunctionTool(func=get_final_draft)
    ]
)

logger.info(f"✅ 成功创建Root Agent '{root_agent.name}'，配置了{len(root_agent.tools)}个工具。") 