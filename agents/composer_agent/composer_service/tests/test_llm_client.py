import os
import sys
import pytest
from unittest import mock

# 动态导入 client.py，便于 patch 其中的 LiteLlm
import importlib.util
spec = importlib.util.spec_from_file_location(
    "client", os.path.join(os.path.dirname(__file__), "../llm/client.py")
)
client = importlib.util.module_from_spec(spec)
sys.modules["client"] = client
spec.loader.exec_module(client)

# 测试：环境变量和依赖都正常时，get_llm_client 能正确返回实例
# 并校验所有参数传递无误

def test_get_llm_client_success(monkeypatch):
    # 构造一个假的 LiteLlm 类用于替换真实依赖
    class DummyLiteLlm:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    # 设置环境变量，模拟正常配置
    monkeypatch.setenv("KINGDORA_BASE_URL", "http://test-url")
    monkeypatch.setenv("KINGDORA_API_KEY", "test-key")
    # patch client.LiteLlm 为 DummyLiteLlm，避免依赖真实包
    with mock.patch.object(client, "LiteLlm", DummyLiteLlm):
        llm = client.get_llm_client()
        assert isinstance(llm, DummyLiteLlm)
        # 校验所有参数传递正确
        assert llm.kwargs["model"] == "openai/gpt-4.1-mini"
        assert llm.kwargs["api_base"] == "http://test-url"
        assert llm.kwargs["api_key"] == "test-key"
        assert llm.kwargs["stream"] is False
        assert llm.kwargs["temperature"] == 0.2

# 测试：环境变量缺失时，get_llm_client 应抛出 EnvironmentError

def test_get_llm_client_missing_env(monkeypatch):
    # 删除环境变量，模拟缺失场景
    monkeypatch.delenv("KINGDORA_BASE_URL", raising=False)
    monkeypatch.delenv("KINGDORA_API_KEY", raising=False)
    # 断言抛出 EnvironmentError
    with pytest.raises(EnvironmentError):
        client.get_llm_client()

# 测试：依赖包 LiteLlm 缺失时，get_llm_client 应抛出 ImportError

def test_get_llm_client_missing_litellm(monkeypatch):
    # 设置环境变量，排除环境变量缺失的干扰
    monkeypatch.setenv("KINGDORA_BASE_URL", "http://test-url")
    monkeypatch.setenv("KINGDORA_API_KEY", "test-key")
    # patch client.LiteLlm 为 None，模拟依赖未安装
    with mock.patch.object(client, "LiteLlm", None):
        # 断言抛出 ImportError
        with pytest.raises(ImportError):
            client.get_llm_client() 