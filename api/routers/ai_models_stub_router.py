from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/api/ai", tags=["ai-models-test"])


@router.get("/models")
async def list_models() -> List[str]:
    return [
        "gpt-4",
        "claude-sonnet",
        "gemini-2.0-flash",
    ]
