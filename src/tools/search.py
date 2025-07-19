# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from langchain_community.tools import DuckDuckGoSearchResults
from src.tools.decorators import create_logged_tool


LoggedDuckDuckGoSearch = create_logged_tool(DuckDuckGoSearchResults)

# Get the selected search tool
def get_web_search_tool(max_search_results: int):
    return LoggedDuckDuckGoSearch(
        name="web_search",
        num_results=max_search_results,
    )
