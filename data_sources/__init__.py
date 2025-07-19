"""
数据源模块
提供统一的数据获取接口
"""

from .akshare_client import AkShareClient
from .hk_akshare_client import HkAkShareClient

# from .search_client import SearchClient

__all__ = [
    "AkShareClient",
    "HkAkShareClient",
    #    "SearchClient",
]
