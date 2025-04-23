def pytest_configure(config):
    try:
        import google.adk
    except ImportError:
        import pytest
        pytest.exit(
            "\n未检测到 google-adk 依赖。\n请先运行 `conda activate adk` 进入正确的虚拟环境后再执行测试。\n"
        ) 