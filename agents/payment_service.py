"""
Payment Service - Stripe Integration
Handles payment processing for credit purchases
"""

import os
import logging
import stripe
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')


class PaymentService:
    """Service for handling Stripe payments"""

    def __init__(self):
        """Initialize payment service"""
        self.stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

        if not self.stripe_api_key:
            logger.warning("STRIPE_SECRET_KEY not set - payments will not work")

        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key

    def create_checkout_session(
        self,
        package_id: int,
        package_name: str,
        package_credits: int,
        package_price_usd: float,
        user_id: int,
        user_email: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for credit purchase

        Args:
            package_id: Credit package ID
            package_name: Package name (e.g., "Starter Package")
            package_credits: Number of credits
            package_price_usd: Price in USD
            user_id: User ID
            user_email: User email
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel

        Returns:
            Dict with session info or error
        """
        try:
            # Create Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(package_price_usd * 100),  # Stripe uses cents
                        'product_data': {
                            'name': f"{package_name} - {package_credits:,} Credits",
                            'description': f"AI Assistant Credits Package",
                            'images': [],  # Optional: add product image URL
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=str(user_id),  # Link payment to user
                metadata={
                    'user_id': str(user_id),
                    'package_id': str(package_id),
                    'credits': str(package_credits),
                    'package_name': package_name,
                },
                payment_intent_data={
                    'metadata': {
                        'user_id': str(user_id),
                        'package_id': str(package_id),
                        'credits': str(package_credits),
                    }
                }
            )

            logger.info(f"Created Stripe checkout session {session.id} for user {user_id}")

            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
                'amount': package_price_usd,
                'currency': 'usd'
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def retrieve_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a Checkout Session

        Args:
            session_id: Stripe session ID

        Returns:
            Dict with session data or error
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                'success': True,
                'session': {
                    'id': session.id,
                    'payment_status': session.payment_status,
                    'customer_email': session.customer_email,
                    'amount_total': session.amount_total / 100,  # Convert cents to dollars
                    'currency': session.currency,
                    'metadata': session.metadata,
                    'payment_intent': session.payment_intent,
                }
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving session: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify Stripe webhook signature

        Args:
            payload: Request body as bytes
            signature: Stripe-Signature header value

        Returns:
            Event dict if valid, None if invalid
        """
        if not self.stripe_webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not set - skipping signature verification")
            # In development, you might want to parse the payload anyway
            # In production, always return None if secret is not set
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.stripe_webhook_secret
            )
            return event

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying webhook: {e}")
            return None

    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook event

        Args:
            event: Stripe event dict

        Returns:
            Dict with handling result
        """
        event_type = event.get('type')

        logger.info(f"Handling Stripe webhook event: {event_type}")

        # Handle different event types
        if event_type == 'checkout.session.completed':
            return self._handle_checkout_completed(event)

        elif event_type == 'payment_intent.succeeded':
            return self._handle_payment_succeeded(event)

        elif event_type == 'payment_intent.payment_failed':
            return self._handle_payment_failed(event)

        elif event_type == 'charge.refunded':
            return self._handle_refund(event)

        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {
                'success': True,
                'handled': False,
                'event_type': event_type
            }

    def _handle_checkout_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle checkout.session.completed event

        This is the primary event for successful purchases.
        """
        session = event['data']['object']

        # Extract metadata
        user_id = session.get('metadata', {}).get('user_id')
        package_id = session.get('metadata', {}).get('package_id')
        credits = session.get('metadata', {}).get('credits')

        payment_intent = session.get('payment_intent')
        amount_total = session.get('amount_total', 0) / 100  # cents to dollars

        logger.info(
            f"Checkout completed: user_id={user_id}, package_id={package_id}, "
            f"credits={credits}, amount=${amount_total}, payment_intent={payment_intent}"
        )

        return {
            'success': True,
            'handled': True,
            'action': 'checkout_completed',
            'data': {
                'user_id': int(user_id) if user_id else None,
                'package_id': int(package_id) if package_id else None,
                'credits': int(credits) if credits else None,
                'amount_usd': amount_total,
                'payment_intent': payment_intent,
                'session_id': session.get('id'),
                'customer_email': session.get('customer_email'),
            }
        }

    def _handle_payment_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_intent.succeeded event"""
        payment_intent = event['data']['object']

        user_id = payment_intent.get('metadata', {}).get('user_id')
        amount = payment_intent.get('amount', 0) / 100

        logger.info(f"Payment succeeded: user_id={user_id}, amount=${amount}")

        return {
            'success': True,
            'handled': True,
            'action': 'payment_succeeded',
            'data': {
                'user_id': int(user_id) if user_id else None,
                'amount_usd': amount,
                'payment_intent': payment_intent.get('id'),
            }
        }

    def _handle_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_intent.payment_failed event"""
        payment_intent = event['data']['object']

        user_id = payment_intent.get('metadata', {}).get('user_id')
        error = payment_intent.get('last_payment_error', {})

        logger.warning(
            f"Payment failed: user_id={user_id}, error={error.get('message')}"
        )

        return {
            'success': True,
            'handled': True,
            'action': 'payment_failed',
            'data': {
                'user_id': int(user_id) if user_id else None,
                'error': error.get('message'),
                'payment_intent': payment_intent.get('id'),
            }
        }

    def _handle_refund(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.refunded event"""
        charge = event['data']['object']

        amount_refunded = charge.get('amount_refunded', 0) / 100
        payment_intent = charge.get('payment_intent')

        logger.info(f"Charge refunded: amount=${amount_refunded}, pi={payment_intent}")

        return {
            'success': True,
            'handled': True,
            'action': 'refund',
            'data': {
                'amount_refunded_usd': amount_refunded,
                'payment_intent': payment_intent,
                'charge_id': charge.get('id'),
            }
        }

    def create_refund(
        self,
        payment_intent_id: str,
        amount_usd: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment

        Args:
            payment_intent_id: Stripe payment intent ID
            amount_usd: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            Dict with refund info or error
        """
        try:
            refund_params = {
                'payment_intent': payment_intent_id,
            }

            if amount_usd is not None:
                refund_params['amount'] = int(amount_usd * 100)  # Convert to cents

            if reason:
                refund_params['reason'] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Created refund {refund.id} for payment {payment_intent_id}")

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_payment_methods(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer's payment methods

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict with payment methods or error
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card',
            )

            return {
                'success': True,
                'payment_methods': [
                    {
                        'id': pm.id,
                        'brand': pm.card.brand,
                        'last4': pm.card.last4,
                        'exp_month': pm.card.exp_month,
                        'exp_year': pm.card.exp_year,
                    }
                    for pm in payment_methods.data
                ]
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting payment methods: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
_payment_service = None


def get_payment_service() -> PaymentService:
    """Get or create PaymentService singleton"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
