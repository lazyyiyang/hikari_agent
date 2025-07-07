from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)


def web_search(search_engine: str, search_query: str) -> str:
    client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))  # 填写您自己的APIKey
    response = client.web_search.web_search(search_engine="search_pro", search_query=search_query)

    return_text = [
        {"title": res.title, "content": res.content, "publish_date": res.publish_date, "source": res.media or res.refer}
        for res in response.search_result
    ]
    return return_text
