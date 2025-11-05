"""
Chat Router - Handles all AI chat endpoints
This is the core module for AI interactions
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import HistoryDatabase, get_db
from agents.auth import get_current_user
from agents.ai_router import AIRouter

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize services
db = get_db()
ai_router = AIRouter(db)

# Pydantic models
class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    task_type: Optional[str] = "general"
    complexity: Optional[str] = "medium"
    budget: Optional[str] = "medium"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    session_id: str
    model_used: str
    tokens_used: int
    cost: float
    cached: bool = False
    processing_time: float

class SessionRequest(BaseModel):
    name: Optional[str] = "New Chat"
    description: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str]
    tokens_used: Optional[int]
    created_at: str

class SessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    message_count: int

class HistoryResponse(BaseModel):
    sessions: List[SessionResponse]
    total_sessions: int
    total_messages: int

# Chat endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Main chat endpoint for single response
    """
    try:
        # Check cache first
        cached_response = db.get_cached_response(
            request.prompt,
            request.task_type
        )

        if cached_response:
            return ChatResponse(
                response=cached_response['response'],
                session_id=request.session_id or "default",
                model_used=cached_response['model'],
                tokens_used=cached_response['tokens_used'],
                cost=cached_response['cost'],
                cached=True,
                processing_time=0.0
            )

        # Process with AI router
        start_time = datetime.now()
        result = await ai_router.route_request(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Save to cache
        db.cache_response(
            prompt=request.prompt,
            task_type=request.task_type,
            response=result['response'],
            model=result['model_used'],
            tokens_used=result['tokens_used'],
            cost=result['cost']
        )

        # Save to history if user is authenticated
        if current_user:
            db.save_chat_message(
                user_id=current_user['id'],
                session_id=request.session_id,
                role="user",
                content=request.prompt
            )
            db.save_chat_message(
                user_id=current_user['id'],
                session_id=request.session_id,
                role="assistant",
                content=result['response'],
                model=result['model_used'],
                tokens_used=result['tokens_used']
            )

        return ChatResponse(
            response=result['response'],
            session_id=request.session_id or "default",
            model_used=result['model_used'],
            tokens_used=result['tokens_used'],
            cost=result['cost'],
            cached=False,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """
    Streaming chat endpoint using Server-Sent Events
    """
    async def generate():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected'})}\n\n"

            # Stream from AI router
            async for chunk in ai_router.route_request_stream(
                prompt=request.prompt,
                task_type=request.task_type,
                complexity=request.complexity,
                budget=request.budget,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming

            # Send completion message
            yield f"data: {json.dumps({'type': 'done', 'message': 'Stream complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

# Session management endpoints
@router.post("/sessions/create", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat session"""
    session_id = db.create_chat_session(
        user_id=current_user['id'],
        name=request.name,
        description=request.description
    )

    return SessionResponse(
        id=session_id,
        name=request.name,
        description=request.description,
        created_at=datetime.now().isoformat(),
        message_count=0
    )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Get all chat sessions for current user"""
    sessions = db.get_user_sessions(current_user['id'])

    return [
        SessionResponse(
            id=s['id'],
            name=s['name'],
            description=s['description'],
            created_at=s['created_at'],
            message_count=s['message_count']
        )
        for s in sessions
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all messages in a session"""
    messages = db.get_session_messages(current_user['id'], session_id)

    return [
        MessageResponse(
            id=m['id'],
            role=m['role'],
            content=m['content'],
            model=m.get('model'),
            tokens_used=m.get('tokens_used'),
            created_at=m['created_at']
        )
        for m in messages
    ]

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chat session and all its messages"""
    db.delete_session(current_user['id'], session_id)
    return {"message": "Session deleted successfully"}

# History endpoints
@router.get("/history", response_model=HistoryResponse)
async def get_history(current_user: dict = Depends(get_current_user)):
    """Get chat history summary"""
    sessions = db.get_user_sessions(current_user['id'])
    total_messages = sum(s['message_count'] for s in sessions)

    return HistoryResponse(
        sessions=[
            SessionResponse(
                id=s['id'],
                name=s['name'],
                description=s['description'],
                created_at=s['created_at'],
                message_count=s['message_count']
            )
            for s in sessions
        ],
        total_sessions=len(sessions),
        total_messages=total_messages
    )

# Model information endpoints
@router.get("/models")
async def get_models():
    """Get available AI models and their capabilities"""
    return {
        "models": [
            {
                "id": "claude-3-opus",
                "name": "Claude 3 Opus",
                "provider": "Anthropic",
                "capabilities": ["complex_reasoning", "coding", "analysis"],
                "max_tokens": 100000,
                "cost_per_1k": 0.015
            },
            {
                "id": "gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "capabilities": ["general", "coding", "creative"],
                "max_tokens": 128000,
                "cost_per_1k": 0.01
            },
            {
                "id": "gemini-pro",
                "name": "Gemini Pro",
                "provider": "Google",
                "capabilities": ["multimodal", "reasoning", "fast"],
                "max_tokens": 32000,
                "cost_per_1k": 0.0025
            },
            {
                "id": "deepseek-coder",
                "name": "DeepSeek Coder",
                "provider": "DeepSeek",
                "capabilities": ["coding", "debugging", "optimization"],
                "max_tokens": 16000,
                "cost_per_1k": 0.002
            },
            {
                "id": "grok-1",
                "name": "Grok-1",
                "provider": "xAI",
                "capabilities": ["reasoning", "humor", "real-time"],
                "max_tokens": 8000,
                "cost_per_1k": 0.005
            },
            {
                "id": "ollama-local",
                "name": "Ollama (Local)",
                "provider": "Local",
                "capabilities": ["privacy", "offline", "customizable"],
                "max_tokens": 4096,
                "cost_per_1k": 0.0
            }
        ]
    }

@router.get("/rankings")
async def get_rankings():
    """Get AI model rankings"""
    rankings = db.get_model_rankings()
    return {"rankings": rankings}

@router.get("/rankings/{category}")
async def get_rankings_by_category(category: str):
    """Get AI model rankings by category"""
    rankings = db.get_rankings_by_category(category)
    return {"category": category, "rankings": rankings}