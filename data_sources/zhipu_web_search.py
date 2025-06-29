from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))  # 填写您自己的APIKey

response = client.web_search.web_search(
    search_engine="search_pro", search_query="搜索浦发银行发展分析", count=5, search_recency_filter="oneYear", content_size="high"
)

return_text = "\n".join(f"{res.title}: {res.content}" for res in response.search_result)
print(return_text)
