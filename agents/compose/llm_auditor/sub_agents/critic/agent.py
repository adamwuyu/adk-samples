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

"""Critic agent for identifying and verifying statements using search tools."""

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types
from google.adk.models.lite_llm import LiteLlm
import os
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults

from . import prompt

gpt_instance = LiteLlm(
    model="openai/gpt-4o",
    api_base=os.getenv("ONEAPI_BASE_URL"),
    api_key=os.getenv("ONEAPI_API_KEY"),
    stream=True
)
gpt_4o_mini_instance = LiteLlm(
    model="openai/gpt-4o-mini",
    api_base=os.getenv("ONEAPI_BASE_URL"),
    api_key=os.getenv("ONEAPI_API_KEY"),
    stream=True
)

# Instantiate LangChain Tavily tool
# You can customize parameters like max_results if needed
tavily_search_instance = TavilySearchResults(
    # max_results=5, # Example customization
)

# Wrap with LangchainTool, providing name and description
adk_tavily_tool = LangchainTool(
    name="InternetSearch",
    description="Searches the internet for up-to-date information, news, and answers using Tavily.",
    tool=tavily_search_instance
)


def _render_reference(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Appends grounding references to the response."""
    del callback_context
    if (
        not llm_response.content or
        not llm_response.content.parts or
        not llm_response.grounding_metadata
    ):
        return llm_response
    references = []
    for chunk in llm_response.grounding_metadata.grounding_chunks or []:
        title, uri, text = '', '', ''
        if chunk.retrieved_context:
            title = chunk.retrieved_context.title
            uri = chunk.retrieved_context.uri
            text = chunk.retrieved_context.text
        elif chunk.web:
            title = chunk.web.title
            uri = chunk.web.uri
        parts = [s for s in (title, text) if s]
        if uri and parts:
            parts[0] = f'[{parts[0]}]({uri})'
        if parts:
            references.append('* ' + ': '.join(parts) + '\n')
    if references:
        reference_text = ''.join(['\n\nReference:\n\n'] + references)
        llm_response.content.parts.append(types.Part(text=reference_text))
    if all(part.text is not None for part in llm_response.content.parts):
        all_text = '\n'.join(part.text for part in llm_response.content.parts)
        llm_response.content.parts[0].text = all_text
        del llm_response.content.parts[1:]
    return llm_response


critic_agent = Agent(
    model=gpt_4o_mini_instance,
    name='critic_agent',
    instruction=prompt.CRITIC_PROMPT,
    tools=[adk_tavily_tool],
    after_model_callback=_render_reference,
)
