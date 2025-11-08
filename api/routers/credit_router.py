"""
Credit System API Router
Handles credit balance, purchases, and transactions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import os

from api.routers.auth_router import get_current_user
from agents.credit_manager import CreditManager
from agents.model_selector import ModelSelector
from agents.payment_service import get_payment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credits", tags=["credits"])
credit_manager = CreditManager()
model_selector = ModelSelector()
payment_service = get_payment_service()


# ============= REQUEST/RESPONSE MODELS =============

class CreditBalanceResponse(BaseModel):
    """Credit balance response"""
    balance: int
    total_purchased: int
    total_spent: int
    created_at: Optional[str]
    updated_at: Optional[str]


class CreditPackage(BaseModel):
    """Credit package model"""
    id: int
    name: str
    credits: int
    price_usd: float
    bonus_credits: int
    total_credits: int
    discount_percentage: float
    price_per_credit: float
    description: Optional[str]
    display_order: int


class PurchaseRequest(BaseModel):
    """Credit purchase request"""
    package_id: int = Field(..., description="ID of the credit package to purchase")
    payment_method: str = Field("stripe", description="Payment method (stripe, paypal, etc.)")


class PurchaseResponse(BaseModel):
    """Credit purchase response"""
    success: bool
    message: str
    transaction_id: Optional[int]
    credits_added: Optional[int]
    new_balance: Optional[int]
    payment_url: Optional[str] = None  # For redirect to payment provider


class CreditTransaction(BaseModel):
    """Credit transaction model"""
    id: int
    user_id: int
    type: str  # purchase, spend, refund, bonus
    amount: int
    balance_before: int
    balance_after: int
    description: Optional[str]
    request_id: Optional[int]
    payment_id: Optional[int]
    metadata: Optional[str]
    created_at: str


class TransactionHistoryResponse(BaseModel):
    """Transaction history response with pagination"""
    transactions: List[CreditTransaction]
    total: int
    limit: int
    offset: int
    has_more: bool


class BonusCreditsRequest(BaseModel):
    """Request to grant bonus credits (admin only)"""
    user_id: int
    amount: int = Field(..., gt=0, description="Number of credits to grant")
    description: str = Field("Admin bonus", description="Reason for bonus")


# ============= ENDPOINTS =============

@router.get("/balance", response_model=CreditBalanceResponse)
async def get_balance(current_user: dict = Depends(get_current_user)):
    """
    Get current user's credit balance and statistics

    Returns:
        - balance: Current available credits
        - total_purchased: Total credits ever purchased
        - total_spent: Total credits ever spent
        - created_at: When credit account was created
        - updated_at: Last update time
    """
    try:
        stats = credit_manager.get_credit_stats(current_user["id"])
        return CreditBalanceResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting balance for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit balance"
        )


@router.get("/packages", response_model=List[CreditPackage])
async def get_packages(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get available credit packages for purchase

    Args:
        include_inactive: Include inactive packages (default: False)

    Returns:
        List of available credit packages with pricing and bonus information
    """
    try:
        active_only = not include_inactive
        packages = credit_manager.get_credit_packages(active_only=active_only)
        return [CreditPackage(**pkg) for pkg in packages]
    except Exception as e:
        logger.error(f"Error getting credit packages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit packages"
        )


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_credits(
    purchase: PurchaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Purchase credits using a package

    This creates a Stripe Checkout session and redirects the user to Stripe's
    hosted payment page. After successful payment, Stripe will send a webhook
    to /api/credits/webhook, which will add credits to the user's account.

    Args:
        purchase: Purchase request with package_id and payment_method

    Returns:
        Purchase response with checkout_url for redirect to Stripe
    """
    try:
        # Get package details
        package = credit_manager.get_package_by_id(purchase.package_id)

        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credit package {purchase.package_id} not found"
            )

        if not package.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This credit package is no longer available"
            )

        # Calculate total credits (base + bonus)
        total_credits = package['credits'] + package['bonus_credits']

        # Create Stripe Checkout Session
        if purchase.payment_method == 'stripe':
            # Get frontend URL from environment
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            success_url = f"{base_url}/credits/success"
            cancel_url = f"{base_url}/credits"

            result = payment_service.create_checkout_session(
                package_id=purchase.package_id,
                package_name=package['name'],
                package_credits=total_credits,
                package_price_usd=package['price_usd'],
                user_id=current_user['id'],
                user_email=current_user['email'],
                success_url=success_url,
                cancel_url=cancel_url
            )

            if not result['success']:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create checkout session: {result.get('error')}"
                )

            logger.info(
                f"Created Stripe checkout session {result['session_id']} for user {current_user['id']}"
            )

            return PurchaseResponse(
                success=True,
                message="Checkout session created. Redirect to payment page.",
                transaction_id=None,  # Will be created by webhook
                credits_added=None,  # Will be added by webhook
                new_balance=None,  # Will be updated by webhook
                payment_url=result['checkout_url']  # Redirect user here
            )

        else:
            # Fallback for demo/testing - immediately grant credits
            logger.warning(
                f"Using demo mode for payment method '{purchase.payment_method}'. "
                f"Credits granted immediately without payment."
            )

            description = (
                f"Purchased {package['name']} package "
                f"({package['credits']} credits + {package['bonus_credits']} bonus)"
            )

            success = credit_manager.add_credits(
                user_id=current_user['id'],
                amount=total_credits,
                description=description,
                payment_id=None,
                metadata={
                    'package_id': purchase.package_id,
                    'package_name': package['name'],
                    'payment_method': purchase.payment_method,
                    'price_usd': package['price_usd'],
                    'demo_mode': True
                }
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add credits to account"
                )

            new_balance = credit_manager.get_balance(current_user['id'])

            return PurchaseResponse(
                success=True,
                message=f"Successfully purchased {total_credits} credits (demo mode)",
                transaction_id=None,
                credits_added=total_credits,
                new_balance=new_balance,
                payment_url=None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing purchase for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process credit purchase"
        )


@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get transaction history for current user

    Args:
        limit: Maximum number of transactions to return (default: 50, max: 100)
        offset: Number of transactions to skip for pagination (default: 0)
        transaction_type: Filter by type - 'purchase', 'spend', 'refund', 'bonus' (optional)

    Returns:
        Paginated list of transactions with metadata
    """
    try:
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0

        # Validate transaction type
        valid_types = ['purchase', 'spend', 'refund', 'bonus']
        if transaction_type and transaction_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transaction type. Must be one of: {', '.join(valid_types)}"
            )

        # Get transactions
        transactions = credit_manager.get_transaction_history(
            user_id=current_user['id'],
            limit=limit,
            offset=offset,
            transaction_type=transaction_type
        )

        # Get total count for pagination
        total = credit_manager.get_total_transactions_count(
            user_id=current_user['id'],
            transaction_type=transaction_type
        )

        has_more = (offset + limit) < total

        return TransactionHistoryResponse(
            transactions=[CreditTransaction(**txn) for txn in transactions],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction history for user {current_user['id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history"
        )


@router.post("/admin/grant-bonus", response_model=dict)
async def grant_bonus_credits(
    bonus_request: BonusCreditsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Grant bonus credits to a user (superadmin only)

    Args:
        bonus_request: User ID, amount, and description

    Returns:
        Success confirmation
    """
    # Check if user is superadmin
    if current_user.get('role') != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can grant bonus credits"
        )

    try:
        success = credit_manager.grant_bonus_credits(
            user_id=bonus_request.user_id,
            amount=bonus_request.amount,
            description=bonus_request.description
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to grant bonus credits"
            )

        new_balance = credit_manager.get_balance(bonus_request.user_id)

        return {
            "success": True,
            "message": f"Granted {bonus_request.amount} credits to user {bonus_request.user_id}",
            "new_balance": new_balance
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting bonus credits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant bonus credits"
        )


@router.get("/admin/users", response_model=List[dict])
async def get_users_with_credits(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all users with credit information (superadmin only)"""
    if current_user.get('role') != 'superadmin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin only")

    try:
        import sqlite3
        from agents.database import DB_PATH

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.email, u.role, u.created_at,
                   COALESCE(uc.balance, 0) as balance,
                   COALESCE(uc.total_purchased, 0) as total_purchased,
                   COALESCE(uc.total_spent, 0) as total_spent
            FROM users u
            LEFT JOIN user_credits uc ON u.id = uc.user_id
            ORDER BY u.id DESC LIMIT ? OFFSET ?
        """, (limit, offset))

        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.get("/admin/analytics", response_model=dict)
async def get_credit_analytics(current_user: dict = Depends(get_current_user)):
    """Get credit system analytics (superadmin only)"""
    if current_user.get('role') != 'superadmin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin only")

    try:
        import sqlite3
        from agents.database import DB_PATH

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM user_credits WHERE balance > 0")
        users_with_balance = cursor.fetchone()['count']

        cursor.execute("SELECT COALESCE(SUM(balance), 0) as total FROM user_credits")
        total_balance = cursor.fetchone()['total']

        cursor.execute("SELECT COALESCE(SUM(total_purchased), 0) as total FROM user_credits")
        total_purchased = cursor.fetchone()['total']

        cursor.execute("SELECT COALESCE(SUM(total_spent), 0) as total FROM user_credits")
        total_spent = cursor.fetchone()['total']

        conn.close()

        return {
            "total_users": total_users,
            "users_with_balance": users_with_balance,
            "total_balance": total_balance,
            "total_purchased": total_purchased,
            "total_spent": total_spent,
            "estimated_revenue_usd": (total_purchased / 1000) * 10
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/estimate", response_model=dict)
async def estimate_cost(
    prompt: str,
    prefer_cheap: bool = False,
    provider: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Estimate credit cost for a prompt using intelligent model selection

    This endpoint analyzes your prompt and recommends the best AI model
    based on task type, complexity, and your available credits.

    Args:
        prompt: The prompt to estimate
        prefer_cheap: Prefer cheaper models even if quality is lower (default: False)
        provider: Force specific provider like 'openai', 'anthropic', etc. (optional)

    Returns:
        Estimated credit cost, selected model, and reasoning
    """
    try:
        # Get user's current credit balance
        user_balance = credit_manager.get_balance(current_user['id'])

        # Use ModelSelector to analyze and recommend model
        recommendation = model_selector.select_model(
            prompt=prompt,
            user_credits=user_balance,
            prefer_cheap=prefer_cheap,
            required_provider=provider
        )

        # Analyze prompt for additional context
        analysis = model_selector.analyze_prompt(prompt)

        return {
            "estimated_cost_credits": recommendation.estimated_cost_credits,
            "estimated_tokens": analysis.estimated_tokens,
            "selected_model": recommendation.model,
            "provider": recommendation.provider,
            "quality_score": recommendation.quality_score,
            "cost_tier": recommendation.cost_tier,
            "user_balance": user_balance,
            "sufficient_credits": user_balance >= recommendation.estimated_cost_credits,
            "task_analysis": {
                "task_type": analysis.task_type,
                "complexity": analysis.complexity,
                "requires_reasoning": analysis.requires_reasoning,
                "requires_code_generation": analysis.requires_code_generation,
                "requires_creativity": analysis.requires_creativity
            },
            "reasoning": recommendation.reasoning,
            "credits_per_1k_tokens": recommendation.credits_per_1k_tokens
        }

    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate cost: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Stripe webhook endpoint

    This endpoint receives webhook events from Stripe when payments are completed,
    failed, or refunded. It verifies the signature and processes the event.

    The most important event is 'checkout.session.completed', which is triggered
    when a user successfully completes a payment.

    NOTE: This endpoint does NOT require authentication because it's called by Stripe.
    Security is handled by webhook signature verification.

    Returns:
        Success/error response
    """
    try:
        # Get raw request body
        payload = await request.body()

        if not stripe_signature:
            logger.warning("Webhook received without stripe-signature header")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Missing stripe-signature header"}
            )

        # Verify webhook signature
        event = payment_service.verify_webhook_signature(payload, stripe_signature)

        if not event:
            logger.error("Webhook signature verification failed")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid signature"}
            )

        # Handle the event
        result = payment_service.handle_webhook_event(event)

        # If this was a successful checkout, add credits to user account
        if result.get('action') == 'checkout_completed' and result.get('data'):
            data = result['data']
            user_id = data.get('user_id')
            credits = data.get('credits')
            payment_intent = data.get('payment_intent')
            amount_usd = data.get('amount_usd')

            if user_id and credits:
                # Add credits to user account
                description = (
                    f"Purchased {credits} credits via Stripe "
                    f"(${amount_usd:.2f})"
                )

                success = credit_manager.add_credits(
                    user_id=user_id,
                    amount=credits,
                    description=description,
                    payment_id=payment_intent,
                    metadata={
                        'package_id': data.get('package_id'),
                        'session_id': data.get('session_id'),
                        'customer_email': data.get('customer_email'),
                        'payment_provider': 'stripe',
                        'amount_usd': amount_usd
                    }
                )

                if success:
                    logger.info(
                        f"Successfully added {credits} credits to user {user_id} "
                        f"from Stripe payment {payment_intent}"
                    )
                else:
                    logger.error(
                        f"Failed to add credits for user {user_id} "
                        f"after successful Stripe payment {payment_intent}"
                    )
                    # TODO: Add to failed transactions table for manual review

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "received": True}
        )

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get("/session/{session_id}")
async def get_checkout_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get Stripe checkout session status

    This endpoint allows the frontend to check if a payment was successful
    after the user returns from Stripe's hosted checkout page.

    Args:
        session_id: Stripe checkout session ID

    Returns:
        Session details including payment status
    """
    try:
        result = payment_service.retrieve_session(session_id)

        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve session: {result.get('error')}"
            )

        session = result['session']

        # Only allow users to view their own sessions
        session_user_id = session.get('metadata', {}).get('user_id')
        if session_user_id and int(session_user_id) != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own payment sessions"
            )

        return {
            "success": True,
            "session": session
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve checkout session"
        )
