# Composer Agent

## 目录结构
```bash
agents/composer-agent  
├── pyproject.toml  
├── pytest.ini  
├── README.md  
├── .vscode/  
└── composer_service/  
    ├── __init__.py  
    ├── agents/  
    ├── tools/  
    ├── workflow/  
    └── tests/  
```

## 快速开始
```bash
cd agents/composer-agent
pip install -e .
# 单元测试
pytest
# Web UI 调试
adk web
```

# Composer 项目

本项目严格遵循ADK规范，采用包中包结构，所有Agent、Tool、流程控制均模块化组织。  
开发与测试请参考docs/composer开发.md。 