# server.py
import os
from fastmcp import FastMCP
from typing import Annotated, Literal
from pydantic import Field
import pandas as pd
from template import CODER_PROMPT
from data_sources import AkShareClient
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

from utils import parse_code

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
        Field(description="上市公司报告类型")
    ],
) -> pd.DataFrame:
    client = AkShareClient()
    df = client.get_all_financial_data(code, report_type)
    return df


@mcp.tool(description="需要对上市公司报告数据进行分析，生成数据分析代码")
def data_analysis_coder(
        data: Annotated[pd.DataFrame, Field(description="上市公司报告数据")]
) -> str:
    prompt = CODER_PROMPT.format(data=data.head().to_json(orient="records"))
    code = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a senior data analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.5
    ).choices[0].message.content
    code = parse_code(code, lang="python")
    return code


@mcp.tool(description="执行Python代码，返回执行结果")
def code_interpreter(
        code: Annotated[str, Field(description="需要执行的代码")],
        df: Annotated[pd.DataFrame, Field(description="需要执行代码的数据")],
) -> str:
    try:
        local_vars = {"df": df}
        exec(code, local_vars)
        result = local_vars.get("result", None)
        return result
    except Exception as e:
        return f"代码执行失败: {str(e)}"



if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")