"""
FastAPI сервер для AI Development System
Предоставляет REST API для взаимодействия с AI агентами
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
import uvicorn
from fastapi.responses import StreamingResponse
import asyncio
import json

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))
# Добавляем путь к директории agents
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from ai_router import AIRouter
from database import get_db
from ranking_collector import RankingCollector
from auth import hash_password, verify_password, create_jwt_token, verify_jwt_token

# Инициализация FastAPI
app = FastAPI(
    title="AI Development System API",
    description="REST API для управления AI агентами и автоматизации разработки",
    version="1.0.0"
)

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:5173"  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация AI Router
router = AIRouter()

# ============================================
# Pydantic Models (схемы данных)
# ============================================

class ChatRequest(BaseModel):
    """Запрос к AI модели"""
    prompt: str = Field(..., description="Текст запроса", min_length=1)
    task_type: Literal['architecture', 'code', 'review', 'test', 'devops', 'research', 'chat', 'general'] = Field(
        default='chat',
        description="Тип задачи"
    )
    complexity: int = Field(default=5, ge=1, le=10, description="Сложность задачи (1-10)")
    budget: Literal['free', 'cheap', 'medium', 'expensive'] = Field(
        default='cheap',
        description="Бюджетный лимит"
    )
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Ответ от AI"""
    response: str
    model: str
    tokens: int
    cost: float
    error: bool = False

class ProjectRequest(BaseModel):
    """Запрос на создание проекта"""
    idea: str = Field(..., description="Описание идеи проекта", min_length=10)
    budget: Literal['free', 'cheap', 'medium', 'premium'] = Field(
        default='medium',
        description="Бюджетный лимит"
    )

class ProjectResponse(BaseModel):
    """Ответ с результатом создания проекта"""
    project_id: str
    architecture: dict
    code: dict
    review: dict
    total_cost: float
    status: str

class StatsResponse(BaseModel):
    """Статистика использования"""
    calls: int
    tokens: int
    cost: float
    avg_cost_per_call: float
    by_model: dict
    available_models: dict

class HealthResponse(BaseModel):
    """Статус здоровья сервиса"""
    status: str
    services: dict
    router_stats: dict

class HistoryResponse(BaseModel):
    """Ответ с историей запросов"""
    total: int
    items: list
    page: int
    limit: int

class HistoryStatsResponse(BaseModel):
    """Статистика по истории"""
    general: dict
    by_model: list
    by_task: list
    by_date: list

# ============================================
# Authentication Models
# ============================================

class RegisterRequest(BaseModel):
    """Запрос на регистрацию нового пользователя"""
    email: EmailStr
    password: str = Field(min_length=8, description="Password (min 8 characters)")

class LoginRequest(BaseModel):
    """Запрос на вход в систему"""
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    """Информация о пользователе"""
    id: int
    email: str
    created_at: str
    last_login_at: Optional[str] = None

class AuthResponse(BaseModel):
    """Ответ с токеном аутентификации"""
    token: str
    user: UserInfo

# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "status": "running",
        "message": "AI Development System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Отправить запрос к AI
    
    Примеры:
```json
    {
        "prompt": "Напиши функцию для сортировки массива",
        "task_type": "code",
        "complexity": 3,
        "budget": "free"
    }
```
    """
    try:
        result = router.route(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            session_id=request.session_id
        )
        
        # Сохраняем в историю
        db = get_db()
        db.add_request(
            prompt=request.prompt,
            response=result['response'],
            model=result['model'],
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            tokens=result.get('tokens', 0),
            cost=result.get('cost', 0.0),
            error=result.get('error', False)
        )
        
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """
    Создать полный проект из идеи
    
    Выполняет полный цикл:
    1. Создание архитектуры (Claude/GPT-4)
    2. Генерация кода (GPT-4/DeepSeek)
    3. Код-ревью (Gemini/DeepSeek)
    
    Примеры:
```json
    {
        "idea": "CRM система для управления вендинговыми автоматами",
        "budget": "medium"
    }
```
    """
    try:
        # 1. Архитектура
        print(f"📐 Creating architecture for: {request.idea}")
        architecture = router.route(
            prompt=f"""Create detailed software architecture for this project:

Project: {request.idea}

Include:
1. Tech stack recommendations
2. System architecture (frontend, backend, database)
3. API endpoints structure
4. Database schema
5. Key components and their responsibilities

Return in structured format.""",
            task_type='architecture',
            complexity=8,
            budget=request.budget
        )
        
        # 2. Генерация кода
        print(f"💻 Generating code...")
        code = router.route(
            prompt=f"""Based on this architecture, generate production-ready starter code:

ARCHITECTURE:
{architecture['response']}

Generate:
1. Main application structure
2. Core API endpoints (at least 3)
3. Database models
4. Configuration files

Use TypeScript for frontend, Python/FastAPI for backend.""",
            task_type='code',
            complexity=7,
            budget=request.budget
        )
        
        # 3. Код-ревью
        print(f"🔍 Running code review...")
        review = router.route(
            prompt=f"""Review this generated code:

CODE:
{code['response'][:2000]}...

Check for:
1. Security issues
2. Best practices
3. Performance concerns
4. Missing error handling

Provide brief summary with score (0-100).""",
            task_type='review',
            complexity=5,
            budget='cheap'
        )
        
        # Формирование ответа
        project_id = f"proj_{hash(request.idea) % 100000:05d}"
        total_cost = (
            architecture.get('cost', 0) + 
            code.get('cost', 0) + 
            review.get('cost', 0)
        )
        
        return ProjectResponse(
            project_id=project_id,
            architecture=architecture,
            code=code,
            review=review,
            total_cost=total_cost,
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Получить статистику использования AI моделей
    
    Возвращает:
    - Общее количество запросов
    - Использованные токены
    - Затраченные средства
    - Статистику по каждой модели
    - Доступность моделей
    """
    try:
        stats = router.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка состояния сервиса
    
    Проверяет:
    - Доступность AI моделей
    - Статистику использования
    - Общее состояние системы
    """
    try:
        available = router._get_available_models()
        stats = router.get_stats()
        
        return HealthResponse(
            status="healthy",
            services={
                "anthropic": available['claude'],
                "openai": available['openai'],
                "openrouter": available['openrouter'],
                "gemini": available['gemini'],
                "ollama": available['ollama']
            },
            router_stats={
                "total_calls": stats['calls'],
                "total_cost": stats['cost']
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """
    Список всех доступных моделей и их статус
    """
    available = router._get_available_models()
    
    models_info = {
        "claude": {
            "name": "Claude Sonnet 4.5",
            "available": available['claude'],
            "use_cases": ["architecture", "research", "complex_code"],
            "cost": "$$$ (Premium)"
        },
        "openai": {
            "name": "GPT-4 Turbo",
            "available": available['openai'],
            "use_cases": ["code", "test", "general"],
            "cost": "$$ (Medium)"
        },
        "openrouter": {
            "name": "DeepSeek V3",
            "available": available['openrouter'],
            "use_cases": ["code", "devops", "review"],
            "cost": "$ (Cheap)"
        },
        "gemini": {
            "name": "Gemini 2.0 Flash",
            "available": available['gemini'],
            "use_cases": ["review", "quick_code", "validation"],
            "cost": "FREE"
        },
        "ollama": {
            "name": "Ollama (Local)",
            "available": available['ollama'],
            "use_cases": ["offline", "private", "unlimited"],
            "cost": "FREE (Local)"
        }
    }
    
    return models_info

@app.get("/api/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    model: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Получить историю запросов к AI
    
    Parameters:
    - limit: количество записей (max 100)
    - offset: смещение для пагинации
    - model: фильтр по модели
    - task_type: фильтр по типу задачи
    - search: поиск по тексту
    """
    try:
        db = get_db()
        
        # Ограничиваем максимальный limit
        limit = min(limit, 100)
        
        items = db.get_history(
            limit=limit,
            offset=offset,
            model=model,
            task_type=task_type,
            search=search
        )
        
        # Общее количество (для пагинации)
        # Упрощенно - берем из текущих результатов
        total = len(items) + offset
        
        return HistoryResponse(
            total=total,
            items=items,
            page=offset // limit + 1 if limit > 0 else 1,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/stats", response_model=HistoryStatsResponse)
async def get_history_stats():
    """
    Получить статистику по истории запросов
    
    Возвращает:
    - Общую статистику
    - Статистику по моделям
    - Статистику по типам задач
    - Статистику по датам (последние 7 дней)
    """
    try:
        db = get_db()
        stats = db.get_stats()
        return HistoryStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/export")
async def export_history(
    format: str = "json",
    model: Optional[str] = None,
    task_type: Optional[str] = None
):
    """
    Экспорт истории в файл
    
    Parameters:
    - format: json или csv
    - model: фильтр по модели
    - task_type: фильтр по типу задачи
    """
    try:
        import tempfile
        from fastapi.responses import FileResponse
        
        db = get_db()
        
        # Создаем временный файл
        suffix = ".json" if format == "json" else ".csv"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        
        # Экспорт
        if format == "json":
            count = db.export_to_json(
                temp_file.name,
                model=model,
                task_type=task_type
            )
        else:
            count = db.export_to_csv(
                temp_file.name,
                model=model,
                task_type=task_type
            )
        
        filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        
        return FileResponse(
            temp_file.name,
            media_type="application/octet-stream",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AI Models Ranking Endpoints
# ============================================

@app.get("/api/rankings")
async def get_rankings():
    """
    Получить все рейтинги AI моделей по категориям
    
    Returns:
        Dict с рейтингами по каждой категории (ТОП-3)
    """
    try:
        db = get_db()
        rankings = db.get_all_rankings()
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rankings/{category}")
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


@app.post("/api/rankings/update")
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


@app.get("/api/rankings/sources")
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

# ============================================
# Streaming Chat Endpoint
# ============================================

async def stream_chat_response(prompt: str, task_type: str, complexity: int, budget: str, session_id: str = None):
    """
    Генератор для потоковой передачи ответа
    """
    try:
        # Получаем полный ответ от роутера
        result = router.route(
            prompt=prompt,
            task_type=task_type,
            complexity=complexity,
            budget=budget,
            session_id=session_id
        )
        
        # Отправляем метаданные первым сообщением
        metadata = {
            'type': 'metadata',
            'model': result['model'],
            'cost': result['cost'],
            'context_used': result.get('context_used', False),
            'context_length': result.get('context_length', 0)
        }
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # Симулируем streaming - разбиваем ответ на части
        response_text = result['response']
        words = response_text.split()
        
        # Отправляем слова по частям
        for i, word in enumerate(words):
            chunk = word + (' ' if i < len(words) - 1 else '')
            yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
            await asyncio.sleep(0.05)
        
        # Отправляем сигнал завершения
        yield f"data: {json.dumps({'type': 'done', 'tokens': result['tokens']})}\n\n"
        
        # Сохраняем в историю
        db = get_db()
        db.add_request(
            prompt=prompt,
            response=response_text,
            model=result['model'],
            task_type=task_type,
            complexity=complexity,
            budget=budget,
            tokens=result.get('tokens', 0),
            cost=result.get('cost', 0.0),
            error=result.get('error', False)
        )
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Потоковый чат с AI (Server-Sent Events)
    """
    return StreamingResponse(
        stream_chat_response(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            session_id=request.session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """
    Регистрация нового пользователя

    Parameters:
    - email: Email пользователя
    - password: Пароль (минимум 8 символов)

    Returns:
    - token: JWT токен
    - user: Информация о пользователе
    """
    try:
        db = get_db()

        # Проверяем существование пользователя
        existing = db.get_user_by_email(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Хэшируем пароль
        password_hash = hash_password(request.password)

        # Создаем пользователя
        user_id = db.create_user(request.email, password_hash)

        # Получаем пользователя
        user = db.get_user_by_email(request.email)

        # Генерируем токен
        token = create_jwt_token(user_id, request.email)

        return AuthResponse(
            token=token,
            user=UserInfo(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Вход в систему

    Parameters:
    - email: Email пользователя
    - password: Пароль

    Returns:
    - token: JWT токен
    - user: Информация о пользователе
    """
    try:
        db = get_db()

        # Получаем пользователя
        user = db.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Проверяем пароль
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Обновляем время последнего входа
        db.update_user_last_login(user['id'])

        # Генерируем токен
        token = create_jwt_token(user['id'], user['email'])

        return AuthResponse(
            token=token,
            user=UserInfo(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me", response_model=UserInfo)
async def get_current_user(authorization: str = Header(None)):
    """
    Получить информацию о текущем пользователе (protected endpoint)

    Headers:
    - Authorization: Bearer {token}

    Returns:
    - Информация о пользователе
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = authorization.replace("Bearer ", "")
        payload = verify_jwt_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        db = get_db()
        user = db.get_user_by_email(payload['email'])

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return UserInfo(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# JWT Middleware Helper
# ============================================

def get_current_user_from_token(authorization: str = Header(None)) -> Dict:
    """
    Dependency для получения текущего пользователя из JWT токена

    Usage:
    ```python
    @app.get("/api/protected")
    async def protected_route(current_user: Dict = Depends(get_current_user_from_token)):
        return {"message": f"Hello {current_user['email']}!"}
    ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    user = db.get_user_by_email(payload['email'])

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Example of protected endpoint
@app.get("/api/protected-example")
async def protected_route_example(current_user: Dict = Depends(get_current_user_from_token)):
    """
    Пример защищенного эндпоинта

    Требует валидный JWT токен в заголовке Authorization
    """
    return {
        "message": f"Hello {current_user['email']}!",
        "user_id": current_user['id'],
        "member_since": current_user['created_at']
    }

# ============================================
# Session Management Endpoints
# ============================================

@app.post("/api/sessions/create")
async def create_session():
    """Создать новую чат-сессию"""
    try:
        db = get_db()
        session_id = db.create_session()
        return {"session_id": session_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Получить все сообщения сессии"""
    try:
        db = get_db()
        messages = db.get_session_messages(session_id)
        return {"session_id": session_id, "messages": messages, "count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def get_all_sessions():
    """Получить список всех сессий"""
    try:
        db = get_db()
        sessions = db.get_all_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Удалить сессию"""
    try:
        db = get_db()
        db.delete_session(session_id)
        return {"success": True, "message": f"Session {session_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Запуск сервера
# ============================================

if __name__ == "__main__":
    print("🚀 Starting AI Development System API Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/health")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
