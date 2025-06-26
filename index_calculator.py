import json
import pandas as pd


def calculate_financial_indices():
    # 读取数据
    with open("tmp/data.json", "r") as f:
        data = json.load(f)

    # 处理空值并提取数据
    def extract_and_clean(report_type):
        df = pd.DataFrame(data.get(report_type, []))
        df = df.replace(-999, pd.NA)
        return df

    # 提取资产负债表和利润表数据
    balance_sheet = extract_and_clean("balance_sheet_年报")
    income_stmt = extract_and_clean("income_statement_年报")

    # 盈利能力分析
    net_profit = income_stmt["NETPROFIT"].iloc[0]
    operate_income = income_stmt["OPERATE_INCOME"].iloc[0]
    total_equity = balance_sheet["TOTAL_EQUITY"].iloc[0]
    total_assets = balance_sheet["TOTAL_ASSETS"].iloc[0]

    # 偿债能力分析
    total_liabilities = balance_sheet["TOTAL_LIABILITIES"].iloc[0]

    # 营运能力分析
    operate_income_annual = operate_income * 4  # 年化营业收入

    # 资产规模分析
    total_assets = balance_sheet["TOTAL_ASSETS"].iloc[0]

    # 杜邦分析
    net_profit_margin = net_profit / operate_income
    asset_turnover = operate_income_annual / total_assets
    equity_multiplier = total_assets / total_equity
    roe = net_profit_margin * asset_turnover * equity_multiplier

    # 构建结果字典
    result = {
        "盈利能力": {
            "净利润(元)": net_profit,
            "销售净利率": net_profit_margin,
            "净资产收益率(ROE)": net_profit / total_equity,
            "总资产收益率(ROA)": net_profit / total_assets,
        },
        "偿债能力": {"资产负债率": total_liabilities / total_assets, "产权比率": total_liabilities / total_equity},
        "营运能力": {"总资产周转率": asset_turnover},
        "资产规模": {"总资产(元)": total_assets, "总负债(元)": total_liabilities, "股东权益(元)": total_equity},
        "杜邦分析": {"销售净利率": net_profit_margin, "总资产周转率": asset_turnover, "权益乘数": equity_multiplier, "净资产收益率(ROE)": roe},
    }

    # 结果保留4位小数
    for category in result:
        for key in result[category]:
            if isinstance(result[category][key], float):
                result[category][key] = round(result[category][key], 4)
    return result
