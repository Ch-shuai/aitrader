"""
资讯中心 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core.database import get_db, NewsItem
from app.services.data_service import NewsService

router = APIRouter()
news_service = NewsService()


@router.get("/list")
async def get_news_list(
    category: Optional[str] = None,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    sentiment: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取新闻列表"""
    query = db.query(NewsItem)

    if category:
        query = query.filter(NewsItem.category == category)
    if source:
        query = query.filter(NewsItem.source == source)
    if sentiment:
        query = query.filter(NewsItem.sentiment == sentiment)
    if keyword:
        query = query.filter(
            NewsItem.title.contains(keyword) | NewsItem.content.contains(keyword)
        )
    if start_date:
        query = query.filter(NewsItem.publish_time >= start_date)
    if end_date:
        query = query.filter(NewsItem.publish_time <= end_date)

    news = query.order_by(NewsItem.publish_time.desc()).limit(limit).all()

    return {
        "total": len(news),
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content[:200] + "..." if len(n.content) > 200 else n.content,
                "source": n.source,
                "url": n.url,
                "category": n.category,
                "sentiment": n.sentiment,
                "related_stocks": n.related_stocks,
                "publish_time": n.publish_time.strftime("%Y-%m-%d %H:%M:%S") if n.publish_time else None,
            }
            for n in news
        ]
    }


@router.get("/latest")
async def get_latest_news(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取最新资讯"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    news = db.query(NewsItem).filter(
        NewsItem.publish_time >= cutoff_time
    ).order_by(NewsItem.publish_time.desc()).limit(limit).all()

    return {
        "hours": hours,
        "total": len(news),
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "source": n.source,
                "category": n.category,
                "sentiment": n.sentiment,
                "publish_time": n.publish_time.strftime("%Y-%m-%d %H:%M:%S") if n.publish_time else None,
            }
            for n in news
        ]
    }


@router.get("/{news_id}")
async def get_news_detail(news_id: int, db: Session = Depends(get_db)):
    """获取新闻详情"""
    news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not news:
        return {"error": "新闻不存在"}

    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "source": news.source,
        "url": news.url,
        "category": news.category,
        "sentiment": news.sentiment,
        "related_stocks": news.related_stocks,
        "publish_time": news.publish_time.strftime("%Y-%m-%d %H:%M:%S") if news.publish_time else None,
        "created_at": news.created_at.strftime("%Y-%m-%d %H:%M:%S") if news.created_at else None,
    }


@router.get("/sources/list")
async def get_news_sources(db: Session = Depends(get_db)):
    """获取新闻来源列表"""
    from sqlalchemy import func

    sources = db.query(
        NewsItem.source,
        func.count(NewsItem.id).label('count')
    ).group_by(NewsItem.source).all()

    return {
        "sources": [
            {"name": s.source, "count": s.count}
            for s in sources if s.source
        ]
    }


@router.get("/categories/list")
async def get_news_categories(db: Session = Depends(get_db)):
    """获取新闻分类列表"""
    from sqlalchemy import func

    categories = db.query(
        NewsItem.category,
        func.count(NewsItem.id).label('count')
    ).group_by(NewsItem.category).all()

    return {
        "categories": [
            {"name": c.category, "count": c.count}
            for c in categories if c.category
        ]
    }


@router.get("/sentiment/stats")
async def get_sentiment_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """获取情感统计"""
    from sqlalchemy import func

    cutoff_date = datetime.now() - timedelta(days=days)

    stats = db.query(
        NewsItem.sentiment,
        func.count(NewsItem.id).label('count')
    ).filter(
        NewsItem.publish_time >= cutoff_date
    ).group_by(NewsItem.sentiment).all()

    total = sum(s.count for s in stats)

    return {
        "period_days": days,
        "total": total,
        "sentiment_distribution": [
            {
                "sentiment": s.sentiment or "neutral",
                "count": s.count,
                "percentage": round(s.count / total * 100, 2) if total > 0 else 0
            }
            for s in stats
        ]
    }


@router.post("/sync")
async def sync_news(
    keyword: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """同步新闻数据"""
    count = news_service.fetch_news(db, keyword, limit)

    return {
        "message": f"同步完成，新增{count}条新闻",
        "synced_count": count
    }


@router.get("/search")
async def search_news(
    q: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索新闻"""
    news = db.query(NewsItem).filter(
        NewsItem.title.contains(q) | NewsItem.content.contains(q)
    ).order_by(NewsItem.publish_time.desc()).limit(limit).all()

    return {
        "query": q,
        "total": len(news),
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content[:200] + "..." if len(n.content) > 200 else n.content,
                "source": n.source,
                "category": n.category,
                "publish_time": n.publish_time.strftime("%Y-%m-%d %H:%M:%S") if n.publish_time else None,
            }
            for n in news
        ]
    }
