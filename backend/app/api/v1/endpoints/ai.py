"""
AI服务 API - 大模型辅助分析
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from app.core.database import get_db, Stock, DailyPrice, NewsItem
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


@router.post("/analyze-stock")
async def analyze_stock(
    code: str,
    analysis_type: str = Query("comprehensive", regex="^(technical|fundamental|sentiment|comprehensive)$"),
    db: Session = Depends(get_db)
):
    """AI分析个股"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "股票不存在"}

    try:
        analysis = await ai_service.analyze_stock(db, code, analysis_type)
        return {
            "code": code,
            "name": stock.name,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}


@router.post("/analyze-market")
async def analyze_market(
    analysis_type: str = Query("overview", regex="^(overview|sentiment|sector|risk)$"),
    db: Session = Depends(get_db)
):
    """AI分析市场整体"""
    try:
        analysis = await ai_service.analyze_market(db, analysis_type)
        return {
            "analysis_type": analysis_type,
            "analysis": analysis,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}


@router.post("/strategy-review")
async def review_strategy(
    strategy_id: int,
    review_type: str = Query("performance", regex="^(performance|risk|optimization|logic)$"),
    db: Session = Depends(get_db)
):
    """AI策略评估"""
    try:
        review = await ai_service.review_strategy(db, strategy_id, review_type)
        return {
            "strategy_id": strategy_id,
            "review_type": review_type,
            "review": review,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"评估失败: {str(e)}"}


@router.post("/generate-strategy")
async def generate_strategy(
    market_condition: str,
    risk_preference: str = Query("moderate", regex="^(conservative|moderate|aggressive)$"),
    investment_style: str = Query("blend", regex="^(value|growth|momentum|blend)$"),
    db: Session = Depends(get_db)
):
    """AI生成策略建议"""
    try:
        strategy = await ai_service.generate_strategy(market_condition, risk_preference, investment_style)
        return {
            "inputs": {
                "market_condition": market_condition,
                "risk_preference": risk_preference,
                "investment_style": investment_style
            },
            "generated_strategy": strategy,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"生成失败: {str(e)}"}


@router.post("/sentiment-analysis")
async def analyze_sentiment(
    text: Optional[str] = None,
    news_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """情感分析"""
    if news_id:
        news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news:
            return {"error": "新闻不存在"}
        text = news.title + " " + news.content

    if not text:
        return {"error": "请提供文本或新闻ID"}

    try:
        sentiment = await ai_service.analyze_sentiment(text)
        return {
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": sentiment,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}


@router.post("/stock-selection")
async def ai_stock_selection(
    criteria: str,
    max_results: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """AI智能选股"""
    try:
        selections = await ai_service.stock_selection(db, criteria, max_results)
        return {
            "criteria": criteria,
            "max_results": max_results,
            "selections": selections,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"选股失败: {str(e)}"}


@router.post("/chat")
async def chat_with_ai(
    message: str,
    context: Optional[dict] = None
):
    """AI问答助手"""
    try:
        response = await ai_service.chat(message, context)
        return {
            "user_message": message,
            "ai_response": response,
            "context_used": context is not None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"对话失败: {str(e)}"}


@router.post("/report/daily")
async def generate_daily_report(
    date: Optional[str] = None,
    report_type: str = Query("brief", regex="^(brief|detailed|technical)$"),
    db: Session = Depends(get_db)
):
    """生成AI日报"""
    try:
        report = await ai_service.generate_daily_report(db, date, report_type)
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "report_type": report_type,
            "report": report,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"生成失败: {str(e)}"}


@router.post("/risk-warning")
async def analyze_risk_warning(
    code: Optional[str] = None,
    portfolio: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """AI风险预警分析"""
    codes = [code] if code else (portfolio or [])

    if not codes:
        return {"error": "请提供股票代码或组合"}

    try:
        warnings = await ai_service.analyze_risks(db, codes)
        return {
            "codes": codes,
            "risk_warnings": warnings,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}


@router.get("/models/status")
async def get_ai_models_status():
    """获取AI模型状态"""
    return {
        "models": [
            {
                "name": "Claude-3-Sonnet",
                "type": "LLM",
                "status": "active",
                "capabilities": ["文本分析", "策略生成", "问答"]
            },
            {
                "name": "XGBoost-Predictor",
                "type": "ML",
                "status": "active",
                "capabilities": ["价格预测", "趋势分类"]
            },
            {
                "name": "Sentiment-Analyzer",
                "type": "NLP",
                "status": "active",
                "capabilities": ["情感分析", "舆情监测"]
            }
        ],
        "api_status": {
            "anthropic": "connected",
            "local_models": "running"
        }
    }
