"""
模块作用：
- 汇总导出数据层能力，给 CLI 和其他上层模块提供稳定入口。

联动关系：
- cli.py 从这里导入 AkShareChinaStockProvider 和 DataProviderError。
"""

from stock_agent_lab.data.akshare_provider import AkShareChinaStockProvider, DataProviderError

__all__ = ["AkShareChinaStockProvider", "DataProviderError"]
