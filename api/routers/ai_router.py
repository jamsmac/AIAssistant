"""
AI Router API Endpoints
Handles AI requests with automatic credit management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Import router with credits
try:
    from agents.ai_router_with_credits import AIRouterWithCredits
    ai_router = AIRouterWithCredits()
except Exception as e:
    logger.error(f"Failed to initialize AIRouterWithCredits: {e}")
    ai_router = None


# ============= REQUEST/RESPONSE MODELS =============

class AIRequest(BaseModel):
    """AI request model"""
    prompt: str = Field(..., min_length=1, description="User's prompt")
    task_type: Optional[str] = Field('general', description="Task type")
    complexity: Optional[str] = Field('medium', description="Complexity level")
    prefer_cheap: bool = Field(False, description="Prefer cheaper models")
    provider: Optional[str] = Field(None, description="Force specific provider")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    use_cache: bool = Field(True, description="Use response caching")


class AIResponse(BaseModel):
    """AI response model"""
    error: bool
    response: Optional[str] = None
    message: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    tokens: Optional[int] = None
    cost_credits: Optional[int] = None
    balance_before: Optional[int] = None
    balance_after: Optional[int] = None
    quality_score: Optional[float] = None
    reasoning: Optional[str] = None
    cached: Optional[bool] = False


# ============= ENDPOINTS =============

@router.post("/route", response_model=AIResponse)
async def route_ai_request(
    request: AIRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Route AI request with automatic credit management

    This endpoint:
    1. Checks user's credit balance
    2. Analyzes the prompt
    3. Selects the best AI model
    4. Executes the request
    5. Charges credits based on actual usage
    6. Returns the response with cost details

    Args:
        request: AI request with prompt and preferences

    Returns:
        AI response with cost and balance information
    """
    if not ai_router:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Router is not available"
        )

    try:
        result = ai_router.route_with_credits(
            prompt=request.prompt,
            user_id=current_user['id'],
            task_type=request.task_type,
            complexity=request.complexity,
            prefer_cheap=request.prefer_cheap,
            required_provider=request.provider,
            session_id=request.session_id,
            use_cache=request.use_cache
        )

        return AIResponse(**result)

    except Exception as e:
        logger.error(f"Error routing AI request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process AI request: {str(e)}"
        )


@router.post("/estimate", response_model=dict)
async def estimate_ai_cost(
    request: AIRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Estimate cost of AI request without executing it

    Returns detailed cost estimation including:
    - Estimated credits needed
    - Selected model and provider
    - Task analysis
    - User's current balance

    Args:
        request: AI request (only prompt is used)

    Returns:
        Cost estimation details
    """
    if not ai_router:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Router is not available"
        )

    try:
        result = ai_router.get_cost_estimate(
            prompt=request.prompt,
            user_id=current_user['id'],
            prefer_cheap=request.prefer_cheap,
            required_provider=request.provider
        )

        return result

    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate cost: {str(e)}"
        )
