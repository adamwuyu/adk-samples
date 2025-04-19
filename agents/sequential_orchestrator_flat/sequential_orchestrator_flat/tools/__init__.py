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

"""Tools for Sequential Orchestrator."""

import logging

from .logging_utils import setup_logging
from .state_manager import StateManager
from .state_tools import (
    check_initial_data,
    store_initial_data,
    get_final_draft
)
from .writing_tools import (
    write_draft,
    score_draft,
    check_progress
)

# 设置日志配置
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("初始化Sequential Orchestrator工具包，配置日志系统...")

__all__ = [
    # 状态管理工具
    "check_initial_data",
    "store_initial_data",
    "get_final_draft",
    
    # 写作与评分工具
    "write_draft",
    "score_draft",
    "check_progress",
    
    # 状态管理类
    "StateManager"
] 