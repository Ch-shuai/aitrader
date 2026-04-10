"""
策略中心 API - 14大核心策略
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db, Strategy, Signal
from app.services.strategy_service import StrategyService

router = APIRouter()
strategy_service = StrategyService()


@router.get("/categories")
async def get_strategy_categories():
    """获取策略分类"""
    return {
        "categories": [
            {
                "id": "value",
                "name": "价值投资策略",
                "strategies": [
                    {"code": "value_fscore", "name": "F-Score价值策略", "description": "基于Piotroski F-Score的价值选股"},
                    {"code": "value_dividend", "name": "红利策略", "description": "高股息率价值投资"},
                    {"code": "value_low_pb", "name": "低PB策略", "description": "市净率低于行业平均"},
                ]
            },
            {
                "id": "growth",
                "name": "成长投资策略",
                "strategies": [
                    {"code": "growth_earnings", "name": "盈利增长策略", "description": "季度盈利加速增长"},
                    {"code": "growth_can_slim", "name": "CANSLIM策略", "description": "欧奈尔成长股模型"},
                    {"code": "growth_quality", "name": "质量成长策略", "description": "高ROE+高成长"},
                ]
            },
            {
                "id": "momentum",
                "name": "动量策略",
                "strategies": [
                    {"code": "momentum_price", "name": "价格动量策略", "description": "20日/60日价格动量"},
                    {"code": "momentum_earnings", "name": "盈利动量策略", "description": "盈利惊喜动量"},
                    {"code": "momentum_industry", "name": "行业动量策略", "description": "领涨行业选股"},
                ]
            },
            {
                "id": "technical",
                "name": "技术分析策略",
                "strategies": [
                    {"code": "tech_breakout", "name": "突破策略", "description": "突破20日/60日新高"},
                    {"code": "tech_trend", "name": "趋势跟踪策略", "description": "均线多头排列"},
                    {"code": "tech_reversal", "name": "均值回归策略", "description": "超卖反弹信号"},
                ]
            },
            {
                "id": "multi_factor",
                "name": "多因子策略",
                "strategies": [
                    {"code": "mf_quality_value", "name": "质量价值", "description": "高质量+低估值"},
                    {"code": "mf_small_cap", "name": "小盘成长", "description": "小市值+高成长"},
                ]
            },
        ]
    }


@router.get("/list")
async def list_strategies(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取策略列表"""
    query = db.query(Strategy)

    if category:
        query = query.filter(Strategy.strategy_type == category)
    if status:
        query = query.filter(Strategy.status == status)

    strategies = query.all()

    return {
        "total": len(strategies),
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "description": s.description,
                "type": s.strategy_type,
                "status": s.status,
                "version": s.version,
                "is_active": s.is_active,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
            }
            for s in strategies
        ]
    }


@router.post("/create")
async def create_strategy(
    name: str,
    code: str,
    description: str = "",
    strategy_type: str = "custom",
    params: dict = None,
    db: Session = Depends(get_db)
):
    """创建新策略"""
    # 检查code是否已存在
    existing = db.query(Strategy).filter(Strategy.code == code).first()
    if existing:
        return {"error": "策略代码已存在"}

    strategy = Strategy(
        name=name,
        code=code,
        description=description,
        strategy_type=strategy_type,
        params=params or {},
        status="stopped",
        is_active=True
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)

    return {
        "id": strategy.id,
        "message": "策略创建成功"
    }


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """获取策略详情"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    return {
        "id": strategy.id,
        "name": strategy.name,
        "code": strategy.code,
        "description": strategy.description,
        "type": strategy.strategy_type,
        "params": strategy.params,
        "status": strategy.status,
        "version": strategy.version,
        "is_active": strategy.is_active,
        "created_at": strategy.created_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.created_at else None,
        "updated_at": strategy.updated_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.updated_at else None,
    }


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    params: Optional[dict] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """更新策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    if name:
        strategy.name = name
    if description:
        strategy.description = description
    if params:
        strategy.params = params
    if is_active is not None:
        strategy.is_active = is_active

    db.commit()
    return {"message": "策略更新成功"}


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """启动策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    strategy.status = "running"
    db.commit()

    return {"message": f"策略 '{strategy.name}' 已启动"}


@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """停止策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    strategy.status = "stopped"
    db.commit()

    return {"message": f"策略 '{strategy.name}' 已停止"}


@router.post("/{strategy_id}/run")
async def run_strategy_once(
    strategy_id: int,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """单次运行策略生成信号"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    try:
        signals = strategy_service.run_strategy(db, strategy, date)
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "signals_generated": len(signals),
            "signals": [
                {
                    "code": s.code,
                    "type": s.signal_type,
                    "trigger_price": s.trigger_price,
                    "confidence": s.confidence,
                    "reason": s.reason,
                    "buy_grade": s.buy_grade
                }
                for s in signals
            ]
        }
    except Exception as e:
        return {"error": f"策略运行失败: {str(e)}"}


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """删除策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    db.delete(strategy)
    db.commit()

    return {"message": "策略已删除"}


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: int,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取策略产生的信号"""
    query = db.query(Signal).filter(Signal.strategy_id == strategy_id)

    if status:
        query = query.filter(Signal.status == status)

    signals = query.order_by(Signal.created_at.desc()).limit(limit).all()

    return {
        "strategy_id": strategy_id,
        "total": len(signals),
        "items": [
            {
                "id": s.id,
                "code": s.code,
                "signal_type": s.signal_type,
                "trigger_price": s.trigger_price,
                "confidence": s.confidence,
                "reason": s.reason,
                "buy_grade": s.buy_grade,
                "status": s.status,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
            }
            for s in signals
        ]
    }


@router.get("/preset/{strategy_code}")
async def get_preset_strategy_detail(strategy_code: str):
    """获取预设策略详情"""
    presets = {
        "value_fscore": {
            "name": "F-Score价值策略",
            "description": "基于Piotroski F-Score的价值选股策略",
            "logic": """
                1. ROA > 0 (资产回报率正)
                2. CFO > 0 (经营现金流正)
                3. ROA同比改善
                4. CFO > ROA (现金流>利润)
                5. 负债率同比下降
                6. 流动比率同比改善
                7. 未增发新股
                8. 毛利率同比改善
                9. 资产周转率同比改善
                F-Score >= 7 买入
            """,
            "params": {
                "fscore_threshold": 7,
                "pe_max": 15,
                "pb_max": 1.5
            }
        },
        "momentum_price": {
            "name": "价格动量策略",
            "description": "基于价格动量的趋势跟踪策略",
            "logic": """
                1. 20日收益率排名前20%
                2. 60日收益率为正
                3. 价格在20日均线上方
                4. 成交量大于20日均量
            """,
            "params": {
                "momentum_window": 20,
                "lookback_window": 60,
                "volume_threshold": 1.0
            }
        },
        "tech_breakout": {
            "name": "突破策略",
            "description": "突破近期高点的动量策略",
            "logic": """
                1. 收盘价突破20日最高价
                2. 成交量放大(大于5日均量1.5倍)
                3. 价格在60日均线上方
            """,
            "params": {
                "breakout_window": 20,
                "volume_multiplier": 1.5,
                "trend_ma": 60
            }
        },
        "growth_can_slim": {
            "name": "CANSLIM策略",
            "description": "威廉·欧奈尔成长股选股模型",
            "logic": """
                C: 当前季度EPS同比大幅增长(>25%)
                A: 过去5年EPS持续增长
                N: 新产品/新管理层/股价新高
                S: 供给紧张(小股本)
                L: 行业龙头
                I: 机构持股增加
                M: 市场趋势向上
            """,
            "params": {
                "eps_growth_min": 25,
                "rs_rating_min": 80,
                "inst_own_min": 5
            }
        }
    }

    if strategy_code not in presets:
        return {"error": "预设策略不存在"}

    return presets[strategy_code]
