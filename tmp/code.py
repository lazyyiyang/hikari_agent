import json

# import pandas as pd

# 读取数据
with open("tmp/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 初始化结果字典
result = {}


# 处理空值（-999）
def handle_null(value):
    return None if value == -999 else value


# 1. 营收分析
income_data = data.get("income_statement_年报", {})
result["营业收入"] = handle_null(income_data.get("OPERATE_INCOME"))
result["营业收入同比增长"] = handle_null(income_data.get("OPERATE_INCOME_YOY"))
result["利息净收入"] = handle_null(income_data.get("INTEREST_NI"))
result["利息净收入同比增长"] = handle_null(income_data.get("INTEREST_NI_YOY"))
result["手续费及佣金净收入"] = handle_null(income_data.get("FEE_COMMISSION_NI"))
result["手续费及佣金净收入同比增长"] = handle_null(income_data.get("FEE_COMMISSION_NI_YOY"))

# 2. 净利润分析
result["净利润"] = handle_null(income_data.get("NETPROFIT"))
result["净利润同比增长"] = handle_null(income_data.get("NETPROFIT_YOY"))
result["归母净利润"] = handle_null(income_data.get("PARENT_NETPROFIT"))
result["归母净利润同比增长"] = handle_null(income_data.get("PARENT_NETPROFIT_YOY"))
result["扣非净利润"] = handle_null(income_data.get("DEDUCT_PARENT_NETPROFIT"))
result["扣非净利润同比增长"] = handle_null(income_data.get("DEDUCT_PARENT_NETPROFIT_YOY"))

# 3. 资产质量分析
balance_data = data.get("balance_sheet_年报", {})
result["总资产"] = handle_null(balance_data.get("TOTAL_ASSETS"))
result["总负债"] = handle_null(balance_data.get("TOTAL_LIABILITIES"))
result["净资产"] = handle_null(balance_data.get("TOTAL_EQUITY"))
result["资产负债率"] = (
    handle_null(balance_data.get("TOTAL_LIABILITIES")) / handle_null(balance_data.get("TOTAL_ASSETS"))
    if handle_null(balance_data.get("TOTAL_ASSETS"))
    else None
)

# 贷款和垫款
result["贷款和垫款总额"] = handle_null(balance_data.get("LOAN_ADVANCE"))
result["贷款和垫款同比增长"] = handle_null(balance_data.get("LOAN_ADVANCE_YOY"))

# 信用减值损失
result["信用减值损失"] = handle_null(income_data.get("CREDIT_IMPAIRMENT_LOSS"))
result["信用减值损失同比变化"] = handle_null(income_data.get("CREDIT_IMPAIRMENT_LOSS_YOY"))

# 4. 盈利能力指标
indicators_data = data.get("financial_indicators", {})
result["净资产收益率"] = indicators_data.get("净资产收益率")
result["销售净利率"] = indicators_data.get("销售净利率")
result["基本每股收益"] = handle_null(indicators_data.get("基本每股收益"))

# 5. 股息分析
cash_flow_data = data.get("cash_flow_年报", {})
result["现金分红金额"] = handle_null(cash_flow_data.get("ASSIGN_DIVIDEND_PORFIT"))
result["现金分红金额同比增长"] = handle_null(cash_flow_data.get("ASSIGN_DIVIDEND_PORFIT_YOY"))

# 计算股息率（假设当前股价为10元）
share_capital = handle_null(balance_data.get("SHARE_CAPITAL"))
if share_capital and result["现金分红金额"]:
    dividend_per_share = result["现金分红金额"] / (share_capital * 10000)  # 转换为万股
    result["股息率"] = dividend_per_share / 10 * 100  # 假设股价10元
else:
    result["股息率"] = None

# 6. 现金流分析
result["经营活动现金流净额"] = handle_null(cash_flow_data.get("NETCASH_OPERATE"))
result["投资活动现金流净额"] = handle_null(cash_flow_data.get("NETCASH_INVEST"))
result["筹资活动现金流净额"] = handle_null(cash_flow_data.get("NETCASH_FINANCE"))
result["现金及现金等价物净增加额"] = handle_null(cash_flow_data.get("CCE_ADD"))

# 7. 关键财务比率
result["流动比率"] = indicators_data.get("流动比率")
result["速动比率"] = indicators_data.get("速动比率")
result["产权比率"] = indicators_data.get("产权比率")

# 8. 行业对比指标（示例）
# 这里可以添加与行业平均值的比较，需要行业数据

# 处理结果中的None值
result = {k: v for k, v in result.items() if v is not None}


# 转换科学计数法为大数字
def format_large_number(num):
    if isinstance(num, (int, float)):
        if abs(num) >= 1e8:
            return f"{num/1e8:.2f}亿"
        elif abs(num) >= 1e4:
            return f"{num/1e4:.2f}万"
    return num


result = {k: format_large_number(v) if isinstance(v, (int, float)) else v for k, v in result.items()}

# 返回结果
result
