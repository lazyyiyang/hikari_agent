import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

def convert_large_numbers(df, columns=None, precision=2, inplace=False):
    # 选择要处理的列
    if columns is None:
        # 自动选择所有数值型列
        num_cols = df.select_dtypes(include=['int64', 'float64']).columns
    else:
        # 使用指定的列
        num_cols = [col for col in columns if col in df.columns]
    
    # 原地操作或创建副本
    if not inplace:
        df = df.copy()
    
    # 转换函数
    def format_number(x):
        try:
            x = float(x)
            abs_x = abs(x)
            if abs_x >= 1e8:  # 1亿以上
                return f"{x/1e8:.{precision}f}亿"
            elif abs_x >= 1e4:  # 1万以上
                return f"{x/1e4:.{precision}f}万"
            else:
                # 小于1万保持原样，移除多余的小数点
                return f"{x:.0f}" if x.is_integer() else f"{x:.{precision}f}"
        except (TypeError, ValueError):
            return x  # 非数值类型保持原样
    
    # 应用转换
    for col in num_cols:
        df[col] = df[col].apply(format_number)
    
    return None if inplace else df


def clean_df(df):
    df = convert_large_numbers(df).head(3)
    df = df.dropna(axis=1, how='any')
    return df.to_html(index=False)
    # return df.to_markdown(index=False)


def trans_table(df):
    # 创建透视表
    pivot_df = pd.pivot_table(
        df,
        index=["REPORT_DATE"],
        columns=["STD_ITEM_NAME"],
        values="AMOUNT"  # 注意：这里使用values="AMOUNT"而非["AMOUNT"]
    ).sort_index(ascending=False).reset_index()
    
    # 扁平化列名：将多级列名转换为单级列名
    pivot_df.columns = [
        col[0] if col[1] == '' else f"{col[1]}"  # 处理索引列和其他列
        for col in pivot_df.columns
    ]
    return pivot_df


class HkAkShareClient:
    def get_fin_data(self, stock_code: str) -> Dict:
        balance = ak.stock_financial_hk_report_em(stock=stock_code, symbol="资产负债表")
        income = ak.stock_financial_hk_report_em(stock=stock_code, symbol="利润表")
        cash_flow = ak.stock_financial_hk_report_em(stock=stock_code, symbol="现金流量表")

        balance = trans_table(balance)
        income = trans_table(income)
        cash_flow = trans_table(cash_flow)

        indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code)
        return {
            "balance_sheet": clean_df(balance),
            "income_statement": clean_df(income),
            "cash_flow_statement": clean_df(cash_flow),
            "analysis_indicator": clean_df(indicator)
        }

if __name__ == "__main__":
    client = HkAkShareClient()
    stock_code = "00020"  # 替换为实际的股票代码
    financial_data = client.get_fin_data(stock_code)
    print(financial_data)