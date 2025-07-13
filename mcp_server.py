import os
import json
from fastmcp import FastMCP
from typing import Annotated, Literal
from pydantic import Field
from openai import OpenAI
from dotenv import load_dotenv

# from template import CODER_PROMPT
from template import VALUATION_PROMPT, ANALYSIS_PROMPT
from data_sources import AkShareClient, zhipu_web_search

# from utils import parse_code
from loguru import logger

load_dotenv(override=True)

mcp = FastMCP()
ai_client = OpenAI(
    api_key=os.getenv("API_KEY", ""),
    base_url="https://api.deepseek.com",
)


@mcp.tool(description="输入上市公司股票代码，返回上市公司相关数据")
def fetch_company_data(
    code: Annotated[str, Field(description="上市公司股票代码, 如: SH600000， SZ000001")],
    # report_type: Annotated[
    #     list[Literal["一季报", "中报", "三季报", "年报"]],
    #     Field(description="上市公司报告类型"),
    # ],
) -> str:
    report_type = ["年报"]
    client = AkShareClient()
    result_dict = client.get_all_financial_data(code, report_type)
    with open("tmp/data.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)
    return "数据获取成功， 保存至tmp/data.json"


@mcp.tool(description="需要对整理后的上市公司数据进行分析")
def data_analysis_coder(idea: Annotated[str, Field(description="专业详细的分析思路")]) -> str:
    logger.info("分析结果生成中")
    with open("tmp/data.json", "r", encoding="utf-8") as f1:
        data = json.load(f1)
    data = {k: v[0] for k, v in data.items()}
    with open("tmp/search_data.json", "r", encoding="utf-8") as f2:
        search_data = json.load(f2)
    data.update({"search_results": search_data})

    prompt = ANALYSIS_PROMPT.format(data=data, idea=idea)
    analysis_result = (
        ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a senior data analyst."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=0.5,
        )
        .choices[0]
        .message.content
    )
    logger.info(f"数据分析结果\n {analysis_result}")
    return analysis_result


@mcp.tool(description="对公司进行估值，生成投资建议")
def corp_valuation(
    idea: Annotated[str, Field(description="专业详细的估值模型构建")],
    stock_value_info: Annotated[list, Field(description="上市公司估值信息")],
    code: Annotated[str, Field(description="上市公司股票代码, 如: SH600000， SZ000001")],
    data_date: Annotated[str, Field(description="数据日期，如：2025-05-30")],
):
    client = AkShareClient()
    result_dict = client.get_stock_value(code)["stock_value"]
    logger.info(f"成功获取估值数据: {result_dict}")
    prompt = VALUATION_PROMPT.format(data=result_dict, idea=idea)
    valuation_advice = (
        ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a senior investment bank’s analyst."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=0.5,
        )
        .choices[0]
        .message.content
    )
    with open("tmp/valuation_data.json", "w", encoding="utf-8") as f:
        json.dump(valuation_advice, f, ensure_ascii=False, indent=4)
    return "数据获取成功， 保存至tmp/valuation_data.json"


@mcp.tool(description="对问题进行深度搜索，生成相应的建议")
def web_deep_search(idea: Annotated[str, Field(description="专业有根据的搜索")]) -> str:
    search_result = "默认搜索结果"
    try:
        search_result = zhipu_web_search.web_search(
            search_engine="search_pro",
            search_query=f"{idea} 浦发银行估值分析",
        )
        logger.info("深度搜索完成")
        with open("tmp/search_data.json", "w", encoding="utf-8") as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"深度搜索失败:{e}")
        search_result = f"搜索失败: {str(e)}"  # 异常时返回错误信息

    return "数据获取成功， 保存至tmp/search_data.json"


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8005, path="/mcp")
