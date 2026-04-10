"""
本地数据导入服务 - 从本地目录加载股票历史数据
数据格式: 每只一个CSV文件，文件名为股票代码
"""
import pandas as pd
import os
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from app.core.database import Stock, DailyPrice
import logging

logger = logging.getLogger(__name__)


class LocalDataService:
    """本地数据导入服务"""

    def __init__(self, data_path: str = "/Users/ch_shuai/Desktop/stock-source-前复权/前复权"):
        self.data_path = data_path

    def discover_stocks(self) -> List[str]:
        """
        发现本地数据目录中的所有股票代码

        Returns:
            股票代码列表
        """
        if not os.path.exists(self.data_path):
            logger.error(f"数据路径不存在: {self.data_path}")
            return []

        stocks = []
        for filename in os.listdir(self.data_path):
            if filename.endswith('.csv'):
                code = filename.replace('.csv', '')
                stocks.append(code)

        logger.info(f"发现 {len(stocks)} 只股票本地数据")
        return sorted(stocks)

    def read_stock_data(self, code: str) -> Optional[pd.DataFrame]:
        """
        读取单只股票的本地历史数据

        Args:
            code: 股票代码 (如: 000001)

        Returns:
            DataFrame with columns
        """
        filepath = os.path.join(self.data_path, f"{code}.csv")

        if not os.path.exists(filepath):
            logger.warning(f"文件不存在: {filepath}")
            return None

        try:
            df = pd.read_csv(filepath, encoding='utf-8')

            # 标准化列名映射
            column_mapping = {
                '日期': 'date',
                '代码': 'code',
                '名称': 'name',
                '所属行业': 'industry',
                '开盘价': 'open',
                '最高价': 'high',
                '最低价': 'low',
                '收盘价': 'close',
                '前收盘价': 'pre_close',
                '成交量（股）': 'volume',
                '成交额（元）': 'amount',
                '换手率': 'turnover',
                '涨幅%': 'pct_change',
                '振幅%': 'amplitude',
                '是否ST': 'is_st',
                '量比': 'volume_ratio',
                '总股本（股）': 'total_shares',
                '流通股本（股）': 'float_shares',
                '总市值（元）': 'total_market_cap',
                '流通市值（元）': 'float_market_cap',
                '滚动市盈率': 'pe_ttm',
                '市净率': 'pb',
                '滚动市销率': 'ps_ttm',
                '5日线': 'ma5',
                '10日线': 'ma10',
                '20日线': 'ma20',
                '60日线': 'ma60',
                '上市时间': 'list_date',
            }

            df = df.rename(columns=column_mapping)

            # 解析日期
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date

            # 按日期排序
            df = df.sort_values('date')

            return df

        except Exception as e:
            logger.error(f"读取 {code} 数据失败: {e}")
            return None

    def import_stock_to_db(self, db: Session, code: str) -> int:
        """
        将单只股票数据导入数据库

        Args:
            db: 数据库会话
            code: 股票代码

        Returns:
            导入的记录数
        """
        df = self.read_stock_data(code)
        if df is None or df.empty:
            return 0

        # 获取第一条记录的股票信息
        first_row = df.iloc[0]

        # 确保股票在股票表中存在
        stock = db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            market = "SH" if code.startswith('6') or code.startswith('5') else "SZ"
            industry = str(first_row.get('industry', '')) if pd.notna(first_row.get('industry')) else ''
            name = str(first_row.get('name', code)) if pd.notna(first_row.get('name')) else code

            stock = Stock(
                code=code,
                name=name,
                industry=industry,
                market=market
            )
            db.add(stock)
            db.flush()

        # 导入价格数据
        count = 0
        for _, row in df.iterrows():
            try:
                date_val = row['date']

                price_data = {
                    'open': float(row['open']) if pd.notna(row.get('open')) else 0,
                    'high': float(row['high']) if pd.notna(row.get('high')) else 0,
                    'low': float(row['low']) if pd.notna(row.get('low')) else 0,
                    'close': float(row['close']) if pd.notna(row.get('close')) else 0,
                    'volume': int(row['volume']) if pd.notna(row.get('volume')) else 0,
                }

                # 可选字段
                if 'amount' in row and pd.notna(row['amount']):
                    price_data['amount'] = float(row['amount'])
                if 'turnover' in row and pd.notna(row['turnover']):
                    price_data['turnover'] = float(row['turnover'])
                if 'pct_change' in row and pd.notna(row['pct_change']):
                    price_data['pct_change'] = float(row['pct_change'])

                # 检查是否已存在
                existing = db.query(DailyPrice).filter(
                    DailyPrice.code == code,
                    DailyPrice.date == date_val
                ).first()

                if existing:
                    # 更新
                    for key, value in price_data.items():
                        setattr(existing, key, value)
                else:
                    # 新建
                    price = DailyPrice(
                        code=code,
                        date=date_val,
                        **price_data
                    )
                    db.add(price)
                    count += 1

            except Exception as e:
                logger.debug(f"导入 {code} {row.get('date')} 失败: {e}")
                continue

        db.commit()
        logger.info(f"导入 {code}: {count} 条新记录")
        return count

    def batch_import(self, db: Session, limit: Optional[int] = None) -> Dict:
        """
        批量导入所有本地股票数据

        Args:
            db: 数据库会话
            limit: 限制导入股票数量

        Returns:
            导入统计
        """
        stocks = self.discover_stocks()

        if limit:
            stocks = stocks[:limit]

        results = {
            "total": len(stocks),
            "success": 0,
            "failed": 0,
            "total_records": 0,
            "stocks": []
        }

        logger.info(f"开始批量导入 {len(stocks)} 只股票")

        for i, code in enumerate(stocks):
            try:
                count = self.import_stock_to_db(db, code)
                results["success"] += 1
                results["total_records"] += count
                results["stocks"].append({
                    "code": code,
                    "records": count,
                    "status": "success"
                })

                if (i + 1) % 100 == 0:
                    logger.info(f"已导入 {i + 1}/{len(stocks)} 只股票")

            except Exception as e:
                logger.error(f"导入 {code} 失败: {e}")
                results["failed"] += 1
                results["stocks"].append({
                    "code": code,
                    "records": 0,
                    "status": "failed",
                    "error": str(e)
                })

        logger.info(f"批量导入完成: 成功 {results['success']}, 失败 {results['failed']}, 总记录 {results['total_records']}")
        return results

    def get_data_summary(self) -> Dict:
        """
        获取本地数据概览

        Returns:
            数据统计
        """
        stocks = self.discover_stocks()

        summary = {
            "data_path": self.data_path,
            "total_stocks": len(stocks),
            "sh_stocks": len([s for s in stocks if s.startswith('6') or s.startswith('5')]),
            "sz_stocks": len([s for s in stocks if s.startswith('0') or s.startswith('3')]),
            "sample_stocks": stocks[:5] if stocks else []
        }

        # 读取样本查看数据范围
        if stocks:
            sample_df = self.read_stock_data(stocks[0])
            if sample_df is not None:
                summary["date_range"] = {
                    "start": sample_df['date'].min().strftime("%Y-%m-%d") if len(sample_df) > 0 else None,
                    "end": sample_df['date'].max().strftime("%Y-%m-%d") if len(sample_df) > 0 else None,
                }
                summary["columns"] = list(sample_df.columns)

        return summary


# 全局本地数据服务实例
local_data_service = LocalDataService()
