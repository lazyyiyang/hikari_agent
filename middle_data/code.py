import json
import pandas as pd

# 读取数据
with open("tmp/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 初始化结果字典
result = {}


# 处理空值（-999替换为NaN）
def clean_data(df):
    return df.replace(-999, pd.NA)


# 1. 财务表现分析
balance_sheet = pd.DataFrame(data["balance_sheet_年报"])
balance_sheet = clean_data(balance_sheet)
income_statement = pd.DataFrame(data["income_statement_年报"])
income_statement = clean_data(income_statement)

result["总资产(元)"] = balance_sheet["TOTAL_ASSETS"].iloc[0]
result["总负债(元)"] = balance_sheet["TOTAL_LIABILITIES"].iloc[0]
result["净资产(元)"] = balance_sheet["TOTAL_EQUITY"].iloc[0]
result["资产负债率"] = f"{balance_sheet['TOTAL_LIABILITIES'].iloc[0] / balance_sheet['TOTAL_ASSETS'].iloc[0] * 100:.2f}%"
result["营业收入(元)"] = income_statement["OPERATE_INCOME"].iloc[0]
result["净利润(元)"] = income_statement["NETPROFIT"].iloc[0]
result["归母净利润(元)"] = income_statement["PARENT_NETPROFIT"].iloc[0]

# 2. 盈利能力分析
result["净资产收益率(ROE)"] = f"{income_statement['NETPROFIT'].iloc[0] / balance_sheet['TOTAL_EQUITY'].iloc[0] * 100:.2f}%"
result["总资产收益率(ROA)"] = f"{income_statement['NETPROFIT'].iloc[0] / balance_sheet['TOTAL_ASSETS'].iloc[0] * 100:.2f}%"
result["净利率"] = f"{income_statement['NETPROFIT'].iloc[0] / income_statement['OPERATE_INCOME'].iloc[0] * 100:.2f}%"

# 3. 资产质量分析
result["不良贷款率"] = "需从不良贷款数据计算"  # 原始数据中无直接指标
result["拨备覆盖率"] = "需从拨备数据计算"  # 原始数据中无直接指标
result["贷款总额(元)"] = balance_sheet["LOAN_ADVANCE"].iloc[0]

# 4. 资本充足率分析
result["资本充足率"] = "需从监管指标计算"  # 原始数据中无直接指标
result["核心一级资本充足率"] = "需从监管指标计算"

# 5. 业务结构分析
result["利息净收入占比"] = f"{income_statement['INTEREST_NI'].iloc[0] / income_statement['OPERATE_INCOME'].iloc[0] * 100:.2f}%"
result[
    "手续费净收入占比"
] = f"{income_statement['FEE_COMMISSION_NI'].iloc[0] / income_statement['OPERATE_INCOME'].iloc[0] * 100:.2f}%"

# 6. 历史趋势分析（需要多期数据）
result["总资产同比增长"] = f"{balance_sheet['TOTAL_ASSETS_YOY'].iloc[0]:.2f}%"
result["营业收入同比增长"] = f"{income_statement['OPERATE_INCOME_YOY'].iloc[0]:.2f}%"
result["净利润同比增长"] = f"{income_statement['NETPROFIT_YOY'].iloc[0]:.2f}%"
result["归母净利润同比增长"] = f"{income_statement['PARENT_NETPROFIT_YOY'].iloc[0]:.2f}%"

# 补充财务指标
financial_indicators = pd.DataFrame(data["financial_indicators"])
result["基本每股收益(元)"] = financial_indicators["基本每股收益"].iloc[0]
result["每股净资产(元)"] = financial_indicators["每股净资产"].iloc[0]
result["净资产收益率(最新)"] = financial_indicators["净资产收益率"].iloc[0]

# 现金流动分析
cash_flow = pd.DataFrame(data["cash_flow_年报"])
cash_flow = clean_data(cash_flow)
result["经营活动现金流净额(元)"] = cash_flow["NETCASH_OPERATE"].iloc[0]
result["投资活动现金流净额(元)"] = cash_flow["NETCASH_INVEST"].iloc[0]
result["筹资活动现金流净额(元)"] = cash_flow["NETCASH_FINANCE"].iloc[0]


# 格式化大数字
def format_large_number(num):
    if pd.isna(num):
        return "N/A"
    if abs(num) >= 1e12:
        return f"{num/1e12:.2f}万亿"
    elif abs(num) >= 1e8:
        return f"{num/1e8:.2f}亿"
    elif abs(num) >= 1e4:
        return f"{num/1e4:.2f}万"
    return str(num)


for key in list(result.keys()):
    if isinstance(result[key], (int, float)) and not pd.isna(result[key]):
        if "率" not in key and "收益" not in key and "比" not in key:
            result[key] = format_large_number(result[key])

result
