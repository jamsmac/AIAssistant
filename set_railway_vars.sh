#!/bin/bash

# Railway Environment Variables Setup
# This script sets all required environment variables in Railway

echo "=========================================="
echo "  Setting Railway Environment Variables"
echo "=========================================="
echo ""

# Load Stripe keys from .env.stripe
if [ -f .env.stripe ]; then
    source .env.stripe
    echo "✓ Loaded Stripe keys from .env.stripe"
else
    echo "❌ Error: .env.stripe file not found"
    echo "Please make sure .env.stripe exists with your Stripe keys"
    exit 1
fi

echo ""
echo "Setting variables in Railway..."
echo ""

# Set Stripe variables
echo "1. Setting STRIPE_SECRET_KEY..."
railway variables --set "STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY"

echo "2. Setting STRIPE_PUBLISHABLE_KEY..."
railway variables --set "STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY"

echo "3. Setting FRONTEND_URL..."
railway variables --set "FRONTEND_URL=https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"

echo ""
echo "⚠️  IMPORTANT: You still need to set STRIPE_WEBHOOK_SECRET"
echo ""
echo "Steps:"
echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
echo "2. Create webhook endpoint:"
echo "   URL: https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook"
echo "3. Copy the webhook secret (whsec_...)"
echo "4. Run:"
echo "   railway variables --set \"STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET\""
echo ""
echo "=========================================="
echo "✓ Stripe variables configured!"
echo "=========================================="
echo ""
echo "Next: Set up webhook in Stripe Dashboard"
echo "See: STRIPE_WEBHOOK_SETUP.md"
echo ""
