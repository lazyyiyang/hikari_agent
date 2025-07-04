import os
import json
from fastmcp import FastMCP
from typing import Annotated, Literal
from pydantic import Field
from openai import OpenAI
from dotenv import load_dotenv

from template import CODER_PROMPT, VALUATION_PROMPT
from data_sources import AkShareClient
from utils import parse_code
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
    report_type: Annotated[
        list[Literal["一季报", "中报", "三季报", "年报"]],
        Field(description="上市公司报告类型"),
    ],
) -> str:
    client = AkShareClient()
    result_dict = client.get_all_financial_data(code, report_type)
    with open("tmp/data.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)
    return "数据获取成功， 保存至tmp/data.json"


@mcp.tool(description="需要对整理后的上市公司数据进行分析，生成数据分析代码")
def data_analysis_coder(idea: Annotated[str, Field(description="专业详细的分析思路")]) -> str:
    logger.info("代码生成中")
    with open("tmp/data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data = {k: v[0] for k, v in data.items()}
    prompt = CODER_PROMPT.format(data=data, idea=idea)
    code = (
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
    code = parse_code(code, lang="python")
    with open("tmp/code.py", "w", encoding="utf-8") as f:
        f.write(code)
    logger.info(f"代码生成结果\n{code}")
    return "代码生成成功， 保存至tmp/code.py"


@mcp.tool(description="对公司进行估值，生成投资建议")
def corp_valuation(
    idea: Annotated[str, Field(description="专业详细的估值模型构建")],
    stock_value_info: Annotated[list, Field(description="上市公司估值信息")],
    code: Annotated[str, Field(description="上市公司股票代码, 如: SH600000， SZ000001")],
    data_date: Annotated[str, Field(description="数据日期，如：2025-05-30")],
) -> dict:
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

    return valuation_advice


# @mcp.tool(description="由于上市公司数据指标较多，使用该工具对数据进行指标过滤，生成相应的过滤python代码，得到更便于分析的数据")
# def index_select_coder(idea: Annotated[str, Field(description="分析思路")]) -> str:
#     logger.info("代码生成中")
#     with open("tmp/data.json", "r", encoding="utf-8") as f:
#         data = json.load(f)
#     data = {k: v[0] for k, v in data.items()}
#     prompt = INDEX_SELECT_PROMPT.format(data=data, idea=idea)
#     code = (
#         ai_client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": "You are a senior data analyst."},
#                 {"role": "user", "content": prompt},
#             ],
#             max_tokens=4096,
#             temperature=0.5,
#         )
#         .choices[0]
#         .message.content
#     )
#     code = parse_code(code, lang="python")
#     with open('tmp/code.py', 'w', encoding="utf-8") as f:
#         f.write(code)
#     logger.info(f"代码生成结果\n{code}")
#     return code


@mcp.tool(description="执行Python代码，返回执行结果")
def code_interpreter(
    # code: Annotated[str, Field(description="需要执行的代码")],
    # data: Annotated[Dict, Field(description="需要执行代码的数据")],
) -> str:
    local_vars = {}  # {"data": data}
    with open("tmp/code.py", "r", encoding="utf-8") as file:
        script_code = file.read()
    try:
        exec(script_code, local_vars)
        result = local_vars.get("result")
        return result
    except Exception as e:
        logger.error(f"代码执行失败: {str(e)}")
        return f"代码执行失败: {str(e)}\n错误代码：{script_code}"


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8005, path="/mcp")
