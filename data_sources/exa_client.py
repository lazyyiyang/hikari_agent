from exa_py import Exa

import os
from dotenv import load_dotenv

load_dotenv(override=True)


exa = Exa(os.getenv("EXA_API_KEY"))
query = "商汤科技 公司简介 发展历程 核心技术"
result_with_text_and_highlights = exa.search_and_contents(
    query,
    # text=True,
    highlights=True,
    num_results=3,
    include_domains=["zh.wikipedia.org", "finance.sina.com.cn", "wallstreetcn.com"],
    start_published_date="2024-01-01",
    end_published_date="2025-06-01",
)

print(result_with_text_and_highlights)
