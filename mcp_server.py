import os
import json
from fastmcp import FastMCP
from typing import Annotated, Literal
from pydantic import Field
from openai import OpenAI
from exa_py import Exa
from dotenv import load_dotenv

from template import CODER_PROMPT  # , SUMMARY_PROMPT
from data_sources import AkShareClient
from utils import parse_code
from loguru import logger
from index_calculator import calculate_financial_indices
from zhipuai import ZhipuAI

load_dotenv(override=True)

mcp = FastMCP()
ai_client = OpenAI(
    api_key=os.getenv("API_KEY", ""),
    base_url="https://api.deepseek.com",
)
exa = Exa(os.getenv("EXA_API_KEY"))
zhipuai_client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))


@mcp.tool(description="输入上市公司股票代码，返回上市公司财务指标数据")
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

    result = calculate_financial_indices()
    return f"数据获取成功， 保存至tmp/data.json \n【{code}指标计算结果】：{result}"


@mcp.tool(description="思考分析，提出数据分析需求，生成数据分析python代码")
def data_analysis_coder(idea: Annotated[str, Field(description="思考后，提出的数据分析需求（不包含图表）")]) -> str:
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
    with open("tmp/code.py", "r") as file:
        script_code = file.read()
    try:
        exec(script_code, local_vars)
        result = local_vars.get("result")
        return result
    except Exception as e:
        logger.error(f"代码执行失败: {str(e)}")
        return f"代码执行失败: {str(e)}"


# @mcp.tool(description="对当前状态的分析需求使用web检索")
# def exa_search(query: Annotated[str, Field(description="检索问题")]) -> str:
#     response = exa.search_and_contents(
#         query,
#         summary=True,
#         num_results=25,
#         start_published_date="2024-01-01",
#         end_published_date="2025-06-01",
#     )
#     results = "\n".join(
#         [
#             f"{res.published_date[:10]}: 《{res.title}》 | {res.summary}\n"
#             for res in response.results
#             if not res.summary.startswith("I am sorry")
#         ]
#     )
#     return results


@mcp.tool(description="对当前状态的分析需求使用web检索")
def web_search(query: Annotated[str, Field(description="检索问题")]) -> str:
    # response = zhipuai_client.web_search.web_search(
    #     search_engine="search_pro",
    #     search_query=query,
    #     count=5,
    #     search_recency_filter="oneYear",
    #     content_size="high"
    #     )
    # results = "\n".join(f"{res.title}: {res.content}" for res in response.search_result)
    with open("tmp/web_content.txt", "r", encoding="utf-8") as f:
        results = f.read()
    return results


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")
