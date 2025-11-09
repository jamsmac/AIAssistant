"""
Models Router - Handles AI models listing and information
"""

from fastapi import APIRouter
from typing import Dict, Any
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.ai_router import AIRouter

router = APIRouter(prefix="/api", tags=["models"])

# Initialize services
ai_router = AIRouter()


@router.get("/models")
async def list_models():
    """
    Список всех доступных моделей и их статус
    """
    available = ai_router._get_available_models()
    
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

