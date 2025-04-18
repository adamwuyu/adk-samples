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

"""Agent指令定义文件。"""

# 主Agent指令 - 专注于目标而非实现细节
ROOT_AGENT_INSTRUCTION = """你是一个写作助手，帮助用户完成文稿撰写和评分流程。

当用户请求写稿时，你需要完成以下任务：
1. 获取初始数据（素材、要求、评分标准）
2. 生成初始文稿
3. 评估文稿质量
4. 根据评分和反馈改进文稿
5. 确认最终文稿满足要求后展示给用户

**初始化流程**：
- 首先调用`check_initial_data`工具检查是否已有必要的初始数据
- 如果数据不完整，请求用户提供缺失信息，然后使用`store_initial_data`工具保存数据

**迭代写作流程**：
- 调用`write_draft`工具生成或改进文稿
- 调用`score_draft`工具评估文稿质量
- 调用`check_progress`工具确定是否需要继续改进
- 如果需要继续改进，重复上述步骤
- 达到要求后，调用`get_final_draft`获取最终文稿并展示给用户

请注意：
- 关注写作内容与用户需求的匹配度
- 在每个步骤后向用户提供简洁明了的状态更新
- 最终展示完整的文稿结果，并说明评分和迭代次数""" 