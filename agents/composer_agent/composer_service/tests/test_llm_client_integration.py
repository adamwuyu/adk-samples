import os
import pytest
import asyncio
from composer_service.llm.client import get_llm_client

def test_llm_client_real():
    """
    集成测试：需设置好 KINGDORA_BASE_URL 和 KINGDORA_API_KEY 环境变量。
    仅验证实例化和基本属性，不发送真实请求。
    """
    kingdora_base_url = os.getenv("KINGDORA_BASE_URL")
    kingdora_api_key = os.getenv("KINGDORA_API_KEY")
    if not kingdora_base_url or not kingdora_api_key:
        pytest.skip("未设置 KINGDORA_BASE_URL 或 KINGDORA_API_KEY，跳过集成测试")
    llm = get_llm_client()
    assert hasattr(llm, "model")
    assert llm.model == "openai/gpt-4.1-mini"

@pytest.mark.asyncio
def test_llm_client_generate_content_async():
    """
    测试 LiteLlm.generate_content_async 的标准用法。
    """
    from google.adk.models.llm_request import LlmRequest
    from google.genai.types import Content, Part, GenerateContentConfig
    llm_client = get_llm_client()
    config = GenerateContentConfig(tools=[])
    llm_request = LlmRequest(contents=[Content(parts=[Part(text="hi, 你是谁？")])], config=config)
    import asyncio
    async def run():
        async for resp in llm_client.generate_content_async(llm_request):
            print(f"generate_content_async 返回: {resp}")
            assert resp is not None
            break  # 只取第一个响应即可
    asyncio.get_event_loop().run_until_complete(run()) 