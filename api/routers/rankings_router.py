"""
Rankings Router - Handles AI model rankings endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import get_db
from ranking_collector import RankingCollector

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get("")
async def get_rankings():
    """
    Получить агрегированные рейтинги всех AI моделей

    Returns:
        Dict с успехом, списком моделей с усредненными оценками и их количеством
    """
    try:
        db = get_db()
        rankings = db.get_all_rankings()
        return {
            "success": True,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}")
async def get_rankings_by_category(category: str, limit: int = 3):
    """
    Получить рейтинги для конкретной категории
    
    Parameters:
    - category: reasoning, coding, vision, chat, agents, translation, local
    - limit: количество моделей (default: 3)
    """
    try:
        db = get_db()
        rankings = db.get_rankings_by_category(category, limit)
        return {"category": category, "models": rankings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_rankings():
    """
    Обновить рейтинги (запустить сбор данных)
    
    Returns:
        Статистика обновления по категориям
    """
    try:
        collector = RankingCollector()
        stats = collector.collect_all_rankings()
        
        total = sum(stats.values())
        
        return {
            "success": True,
            "total_updated": total,
            "by_category": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def get_trusted_sources():
    """
    Получить список доверенных источников данных
    """
    try:
        db = get_db()
        sources = db.get_trusted_sources()
        return {"sources": sources, "count": len(sources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

