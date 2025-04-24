import os
import pytest
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