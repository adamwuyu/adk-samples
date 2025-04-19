"""测试新的标准化LLM工具功能。"""

import asyncio
import os
import logging
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.type import Content

# 导入Agent
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sequential_orchestrator_flat.agent import root_agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试数据
TEST_MATERIAL = """
AI写作工具是一种利用人工智能技术帮助人们创作文本内容的软件或应用。它们通常基于大型语言模型(LLM)，
如GPT系列、Claude或Gemini等，能够根据用户提供的提示(prompt)生成各种类型的文本。

这些工具的功能多种多样，从简单的文本补全、语法检查到完整的文章生成、创意写作等。市场上常见的AI写作工具包括
Jasper、Copy.ai、Rytr、Writesonic等，同时OpenAI的ChatGPT、Anthropic的Claude也被广泛用于写作辅助。

AI写作工具的工作原理是分析大量文本数据，学习语言模式、结构和风格，然后根据用户的需求生成相应的内容。
用户通常需要提供一些指导性信息，如主题、关键词、写作风格或特定要求，AI工具会据此生成相关内容。
"""

TEST_REQUIREMENTS = """
请分析AI写作工具的优缺点，内容应该全面客观，既要指出其便利性和效率提升，也要分析其局限性和潜在问题。
文章应该有清晰的结构，语言简洁明了，适合对AI技术有基本了解但不熟悉AI写作工具的读者。
"""

TEST_CRITERIA = """
评分标准：
1. 内容全面性(40%) - 是否全面分析了AI写作工具的优缺点
2. 结构清晰度(30%) - 文章结构是否清晰，逻辑是否连贯
3. 表达准确性(20%) - 语言是否准确，术语使用是否恰当
4. 目标适配性(10%) - 是否适合目标读者群体
"""

async def test_llm_tools_flow():
    """测试LLM工具的完整流程。"""
    logger.info("开始测试LLM工具流程...")
    
    # 创建会话服务和Runner
    session_service = InMemorySessionService()
    runner = Runner(session_service=session_service)
    
    # 创建会话并设置初始状态
    session = await session_service.create_session(
        app_name="sequential_orchestrator_flat_test",
        user_id="test_user",
        session_id="test_session"
    )
    
    # 构建初始消息
    initial_message = Content.text(
        "我想写一篇关于AI写作工具的文章。"
        "这是我的素材、要求和评分标准:\n"
        f"素材: {TEST_MATERIAL}\n"
        f"要求: {TEST_REQUIREMENTS}\n"
        f"评分标准: {TEST_CRITERIA}"
    )
    
    # 启动交互
    logger.info("发送初始消息，启动交互...")
    events = await runner.run_async(
        agent=root_agent,
        new_message=initial_message,
        session_id=session.id
    )
    
    # 等待用户查看首个响应
    user_input = input("\n请按Enter继续交互，或输入'q'退出: ")
    if user_input.lower() == 'q':
        return
    
    # 模拟用户请求生成初稿
    follow_up_message = Content.text("请开始为我生成初稿")
    logger.info("发送后续消息，请求生成初稿...")
    events = await runner.run_async(
        agent=root_agent,
        new_message=follow_up_message,
        session_id=session.id
    )
    
    # 等待用户查看生成结果
    user_input = input("\n请按Enter继续交互，查看最终结果，或输入'q'退出: ")
    if user_input.lower() == 'q':
        return
    
    # 模拟用户请求查看最终结果
    final_message = Content.text("请取回最终文稿结果")
    logger.info("发送最终消息，请求查看结果...")
    events = await runner.run_async(
        agent=root_agent,
        new_message=final_message,
        session_id=session.id
    )
    
    logger.info("测试完成！")

if __name__ == "__main__":
    asyncio.run(test_llm_tools_flow()) 