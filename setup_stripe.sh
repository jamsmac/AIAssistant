#!/bin/bash

# Stripe Configuration Setup Script
# This script helps you configure Stripe for the AI Assistant platform

echo "========================================"
echo "  AI Assistant - Stripe Setup"
echo "========================================"
echo ""

# Stripe Keys (Test Mode) - Get from Stripe Dashboard
# https://dashboard.stripe.com/test/apikeys
read -p "Enter your Stripe Secret Key (sk_test_...): " STRIPE_SECRET_KEY
read -p "Enter your Stripe Publishable Key (pk_test_...): " STRIPE_PUBLISHABLE_KEY

if [ -z "$STRIPE_SECRET_KEY" ] || [ -z "$STRIPE_PUBLISHABLE_KEY" ]; then
    echo "❌ Error: Stripe keys are required"
    exit 1
fi

echo ""
echo "✓ Stripe Keys Configured"
echo ""

# Check if Railway CLI is installed
if command -v railway &> /dev/null; then
    echo "Setting up Railway environment variables..."
    echo ""

    # Set Stripe keys
    railway variables set STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY"
    railway variables set STRIPE_PUBLISHABLE_KEY="$STRIPE_PUBLISHABLE_KEY"

    # Get Railway URL for webhook
    echo ""
    echo "⚠️  IMPORTANT: Set up Stripe webhook"
    echo ""
    echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
    echo "2. Click 'Add endpoint'"
    echo "3. Enter your Railway URL + /api/credits/webhook"
    echo "   Example: https://your-app.railway.app/api/credits/webhook"
    echo ""
    echo "4. Select these events:"
    echo "   - checkout.session.completed"
    echo "   - payment_intent.succeeded"
    echo "   - payment_intent.payment_failed"
    echo "   - charge.refunded"
    echo ""
    echo "5. Copy the webhook signing secret (starts with whsec_)"
    echo "6. Run: railway variables set STRIPE_WEBHOOK_SECRET=whsec_..."
    echo ""

else
    echo "⚠️  Railway CLI not found. Install it or set variables manually:"
    echo ""
    echo "STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY"
    echo "STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY"
    echo ""
fi

# Check if Vercel CLI is installed
if command -v vercel &> /dev/null; then
    echo "Setting up Vercel environment variables..."
    echo ""

    # Get Railway URL
    read -p "Enter your Railway backend URL (e.g., https://your-app.railway.app): " RAILWAY_URL

    if [ -z "$RAILWAY_URL" ]; then
        RAILWAY_URL="http://localhost:8000"
        echo "Using default: $RAILWAY_URL"
    fi

    # Set frontend variables
    cd web-ui 2>/dev/null || cd .

    vercel env add NEXT_PUBLIC_API_URL production <<< "$RAILWAY_URL"
    vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production <<< "$STRIPE_PUBLISHABLE_KEY"

    echo ""
    echo "✓ Vercel environment variables set"
    echo ""

    cd ..
else
    echo "⚠️  Vercel CLI not found. Set variables manually in Vercel Dashboard:"
    echo ""
    echo "NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app"
    echo "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY"
    echo ""
fi

echo "========================================"
echo "  Configuration Summary"
echo "========================================"
echo ""
echo "✓ Stripe Test Keys Ready"
echo "  - Secret Key: sk_test_...rok000BVZ1x9U"
echo "  - Publishable Key: pk_test_...00YUMru005CIl3FEU"
echo ""
echo "⚠️  TODO: Set up Stripe Webhook"
echo "  1. Create webhook at https://dashboard.stripe.com/test/webhooks"
echo "  2. Set STRIPE_WEBHOOK_SECRET in Railway"
echo ""
echo "⚠️  TODO: Update Frontend URL in Backend"
echo "  File: api/routers/credit_router.py:190"
echo "  Change: base_url = \"http://localhost:3000\""
echo "  To: base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')"
echo ""
echo "📚 Full documentation: STRIPE_SETUP.md"
echo ""
echo "🚀 Ready to test payments!"
echo ""
