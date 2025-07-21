import os
import json
from fastmcp import FastMCP
from typing import Annotated, Literal
from pydantic import Field
from openai import OpenAI
from dotenv import load_dotenv

# from template import CODER_PROMPT
from template import VALUATION_PROMPT, ANALYSIS_PROMPT
from data_sources import AkShareClient, HkAkShareClient

# from utils import parse_code
from loguru import logger

load_dotenv(override=True)

mcp = FastMCP()
ai_client = OpenAI(
    api_key=os.getenv("API_KEY", ""),
    base_url="https://api.deepseek.com",
)


@mcp.tool(description="输入A股上市公司股票代码，返回上市公司相关数据")
def fetch_a_stock_data(
    code: Annotated[str, Field(description="A股上市公司股票代码, 如: SH600000， SZ000001")],
) -> str:
    report_type = ["年报"]
    client = AkShareClient()
    result_dict = client.get_all_financial_data(code, report_type)
    with open("tmp/data.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)
    return "数据获取成功， 保存至tmp/data.json"


@mcp.tool(description="输入港股上市公司股票代码，返回上市公司相关数据")
def fetch_hk_stock_data(
    code: Annotated[str, Field(description="港股上市公司股票代码, 如: 00020")],
) -> str:
    try:
        client = HkAkShareClient()
        result_dict = client.get_fin_data(code)
        with open("tmp/data.json", "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=4)
        return "数据获取成功， 保存至tmp/data.json"
    except Exception as e:
        logger.error(f"Error fetching HK stock data: {code}")
        return "港股代码获取错误，重新输入正确的代码"


@mcp.tool(description="需要对整理后的上市公司数据进行分析")
def data_analysis(idea: Annotated[str, Field(description="待分析企业的行业特性")]) -> str:
    logger.info("分析结果生成中")
    data = {}
    if os.path.exists("tmp/data.json"):
        with open("tmp/data.json", "r", encoding="utf-8") as f1:
            data = json.load(f1)
    else:
        return "没有需要分析的上市企业财务数据，请先尝试获取一些相关上市企业的财务数据"
    # data = {k: v[0] for k, v in data.items()}
    # with open("tmp/search_data.json", "r", encoding="utf-8") as f2:
    #     search_data = json.load(f2)
    # data.update({"search_results": search_data})

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
    with open("tmp/analysis_result.md", "w", encoding="utf-8") as f:
        f.write(analysis_result)
    logger.info(f"数据分析结果\n {analysis_result}")
    return analysis_result


@mcp.tool(description="对公司进行估值，生成投资建议")
def corp_valuation(
    idea: Annotated[str, Field(description="专业详细的估值模型构建")],
    code: Annotated[str, Field(description="上市公司股票代码, 如: SH600000， SZ000001")],
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
    with open("tmp/valuation_data.md", "w", encoding="utf-8") as f:
        f.write(valuation_advice)
    return "数据获取成功， 保存至tmp/valuation_data.md"


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8005, path="/mcp")
