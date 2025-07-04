import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class AkShareClient:
    """AkShare数据客户端"""

    def get_balance_sheet(self, symbol: str, period: str = "年报") -> Optional[pd.DataFrame]:
        """
        获取资产负债表

        Args:
            symbol: 股票代码 (如: 000001)
            period: 报告期类型 ("年报", "中报", "一季报", "三季报")

        Returns:
            DataFrame: 资产负债表数据
        """
        try:
            logger.info(f"获取资产负债表数据: {symbol}, 期间: {period}")
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
            df = df[df["REPORT_TYPE"] == period]
            if df is not None and not df.empty:
                # 数据清洗和标准化
                logger.info(f"成功获取资产负债表数据: {symbol}, 共{len(df)}条记录")
                return df
            else:
                logger.warning(f"未获取到资产负债表数据: {symbol}")
                return None

        except Exception as e:
            logger.error(f"获取资产负债表失败: {symbol}, 错误: {str(e)}")
            return None

    def get_income_statement(self, symbol: str, period: str = "年报") -> Optional[pd.DataFrame]:
        """
        获取利润表

        Args:
            symbol: 股票代码
            period: 报告期类型

        Returns:
            DataFrame: 利润表数据
        """
        try:
            logger.info(f"获取利润表数据: {symbol}, 期间: {period}")
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
            df = df[df["REPORT_TYPE"] == period]
            if df is not None and not df.empty:
                df = self._clean_financial_data(df)
                logger.info(f"成功获取利润表数据: {symbol}, 共{len(df)}条记录")
                return df
            else:
                logger.warning(f"未获取到利润表数据: {symbol}")
                return None

        except Exception as e:
            logger.error(f"获取利润表失败: {symbol}, 错误: {str(e)}")
            return None

    def get_cash_flow(self, symbol: str, period: str = "年报") -> Optional[pd.DataFrame]:
        """
        获取现金流量表

        Args:
            symbol: 股票代码
            period: 报告期类型

        Returns:
            DataFrame: 现金流量表数据
        """
        try:
            logger.info(f"获取现金流量表数据: {symbol}, 期间: {period}")
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)

            if df is not None and not df.empty:
                df = self._clean_financial_data(df)
                df = df[df["REPORT_TYPE"] == period]
                logger.info(f"成功获取现金流量表数据: {symbol}, 共{len(df)}条记录")
                return df
            else:
                logger.warning(f"未获取到现金流量表数据: {symbol}")
                return None

        except Exception as e:
            logger.error(f"获取现金流量表失败: {symbol}, 错误: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票基本信息
        """
        try:
            logger.info(f"获取股票基本信息: {symbol}")

            # 获取股票基本信息
            symbol = symbol.replace("SH", "").replace("SZ", "")
            stock_info = ak.stock_individual_info_em(symbol=symbol)

            # 获取实时行情
            realtime_data = ak.stock_zh_a_spot_em()
            stock_realtime = realtime_data[realtime_data["代码"] == symbol]

            result = {
                "symbol": symbol,
                "basic_info": stock_info.to_dict() if stock_info is not None else {},
                "realtime_data": stock_realtime.to_dict("records")[0] if not stock_realtime.empty else {},
                "update_time": datetime.now().isoformat(),
            }
            logger.info(f"成功获取股票基本信息: {symbol}")
            return result

        except Exception as e:
            logger.error(f"获取股票基本信息失败: {symbol}, 错误: {str(e)}")
            return None

    def get_stock_value(self, symbol: str) -> Optional[Dict]:
        """
        获取股票估值信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票估值信息
        """
        try:
            logger.info("获取估值信息")

            # 获取股票估值信息
            symbol = symbol.replace("SH", "").replace("SZ", "").replace("sh", "").replace("sz", "")
            stock_value = ak.stock_value_em(symbol=symbol)
            # latest_date = stock_value['数据日期'].max()

            # 日期格式修改
            stock_value["数据日期"] = pd.to_datetime(stock_value["数据日期"].astype(str)).dt.date
            target_date = pd.to_datetime("2025-06-30").date()
            date_mask = stock_value["数据日期"] == target_date
            stock_value = stock_value[date_mask]

            logger.info(f"stock_value:{stock_value}")
            result = {
                "symbol": symbol,
                "stock_value": stock_value.to_dict() if stock_value is not None else {},
            }
            logger.info(f"成功获取估值信息:{symbol}")
            return result

        except Exception as e:
            logger.error(f"获取估值信息失败:{symbol}, 错误{str(e)}")
            return None

    def get_financial_indicators(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取财务指标数据

        Args:
            symbol: 股票代码

        Returns:
            DataFrame: 财务指标数据
        """
        try:
            logger.info(f"获取财务指标数据: {symbol}")
            symbol = symbol.replace("SH", "").replace("SZ", "")
            df = ak.stock_financial_abstract_ths(symbol=symbol)

            if df is not None and not df.empty:
                df = self._clean_financial_data(df)
                logger.info(f"成功获取财务指标数据: {symbol}, 共{len(df)}条记录")
                return df.sort_values(by="报告期", ascending=False)
            else:
                logger.warning(f"未获取到财务指标数据: {symbol}")
                return None

        except Exception as e:
            logger.error(f"获取财务指标失败: {symbol}, 错误: {str(e)}")
            return None

    def get_all_financial_data(self, symbol: str, periods: List[str] = None) -> Dict[str, pd.DataFrame]:  # type: ignore
        """
        获取所有财务数据

        Args:
            symbol: 股票代码
            periods: 报告期列表

        Returns:
            dict: 包含所有财务数据的字典
        """
        if periods is None:
            periods = ["年报", "中报"]

        result = {}

        for period in periods:
            logger.info(f"获取 {symbol} 的 {period} 数据")

            # 获取三大报表
            balance_sheet = self.get_balance_sheet(symbol, period)
            income_statement = self.get_income_statement(symbol, period)
            cash_flow = self.get_cash_flow(symbol, period)

            if balance_sheet is not None:
                result[f"balance_sheet_{period}"] = balance_sheet
            if income_statement is not None:
                result[f"income_statement_{period}"] = income_statement
            if cash_flow is not None:
                result[f"cash_flow_{period}"] = cash_flow

        # 获取财务指标
        financial_indicators = self.get_financial_indicators(symbol)
        if financial_indicators is not None:
            result["financial_indicators"] = financial_indicators

        # 获取股票基本信息
        stock_info = self.get_stock_info(symbol)
        if stock_info is not None:
            result["stock_info"] = stock_info

        # 获取估值信息
        stock_value_info = self.get_stock_value(symbol)
        if stock_value_info is not None:
            result["stock_value_info"] = stock_value_info

        logger.info(f"成功获取 {symbol} 的所有财务数据，包含 {len(result)} 个数据集")

        # test
        clean_result = {}
        for k, v in result.items():
            if isinstance(v, pd.DataFrame) and not v.empty:
                clean_result[k] = v.head(3).dropna(axis=1, how="all").fillna(-999).to_dict(orient="records")

        return clean_result

    def _clean_financial_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗财务数据
        Args:
            df: 原始数据

        Returns:
            DataFrame: 清洗后的数据
        """
        if df is None or df.empty:
            return df

        # 删除空行
        df = df.dropna(how="all")

        # 数据类型转换
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = pd.to_numeric(df[col], errors="ignore")  # type: ignore

        # 日期列处理
        date_columns = ["报告日期", "公告日期", "期间"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="ignore")  # type: ignore

        return df


if __name__ == "__main__":
    client = AkShareClient()
    df = client.get_all_financial_data("SH600000", ["一季报"])
    print(df)
