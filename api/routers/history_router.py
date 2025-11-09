"""
History Router - Handles chat history and request history endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import csv
import io
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import get_db
from agents.auth import get_current_user_from_token

router = APIRouter(prefix="/api/history", tags=["history"])


# Response models
class HistoryResponse(BaseModel):
    requests: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class HistoryStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    by_model: Dict[str, int]
    by_task_type: Dict[str, int]


@router.get("", response_model=HistoryResponse)
async def get_history(
    page: int = 1,
    page_size: int = 50,
    task_type: Optional[str] = None,
    model: Optional[str] = None,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить историю запросов
    
    Parameters:
    - page: Номер страницы (default: 1)
    - page_size: Размер страницы (default: 50)
    - task_type: Фильтр по типу задачи
    - model: Фильтр по модели
    """
    try:
        user_id = token_data.get('user_id') or token_data.get('id')
        db = get_db()
        
        # Build query
        query = "SELECT * FROM requests WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)").split("ORDER BY")[0]
        count_params = params[:-2]  # Remove LIMIT and OFFSET params
        
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(count_query, count_params)
            total = cursor.fetchone()[0]
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        requests = [dict(row) for row in rows]
        
        return HistoryResponse(
            requests=requests,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=HistoryStatsResponse)
async def get_history_stats(
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить статистику по истории запросов
    """
    try:
        user_id = token_data.get('user_id') or token_data.get('id')
        db = get_db()
        
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute(
                """SELECT COUNT(*), SUM(tokens_used), SUM(cost), 
                          GROUP_CONCAT(DISTINCT model), GROUP_CONCAT(DISTINCT task_type)
                   FROM requests
                   WHERE user_id = ? OR user_id IS NULL""",
                (user_id,)
            )
            row = cursor.fetchone()
        
        total_requests = row[0] or 0
        total_tokens = row[1] or 0
        total_cost = row[2] or 0.0
        
        # Get by model
        cursor = conn.execute(
            """SELECT model, COUNT(*) as count
               FROM requests
               WHERE user_id = ? OR user_id IS NULL
               GROUP BY model""",
            (user_id,)
        )
        by_model = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get by task type
        cursor = conn.execute(
            """SELECT task_type, COUNT(*) as count
               FROM requests
               WHERE user_id = ? OR user_id IS NULL
               GROUP BY task_type""",
            (user_id,)
        )
        by_task_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return HistoryStatsResponse(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            by_model=by_model,
            by_task_type=by_task_type
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"History stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_history(
    format: str = "csv",
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Экспортировать историю запросов
    
    Parameters:
    - format: Формат экспорта (csv, json) - default: csv
    """
    try:
        user_id = token_data.get('user_id') or token_data.get('id')
        db = get_db()
        
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM requests
                   WHERE user_id = ? OR user_id IS NULL
                   ORDER BY timestamp DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[col[0] for col in rows[0].keys()] if rows else [])
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=history_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        else:
            return {"requests": [dict(row) for row in rows]}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

