#!/bin/bash

# Quick Stripe Setup Verification Script
# Checks if all required variables are set in Railway

echo "=========================================="
echo "  Stripe Setup Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not found${NC}"
    echo "Install it: npm i -g @railway/cli"
    echo ""
    echo "You can still check variables manually in Railway Dashboard:"
    echo "https://railway.app"
    echo ""
    exit 1
fi

echo "Checking Railway variables..."
echo ""

# Required variables
REQUIRED_VARS=(
    "STRIPE_SECRET_KEY"
    "STRIPE_PUBLISHABLE_KEY"
    "STRIPE_WEBHOOK_SECRET"
    "FRONTEND_URL"
)

# Check each variable
ALL_SET=true
for var in "${REQUIRED_VARS[@]}"; do
    value=$(railway variables 2>/dev/null | grep "^$var=" | cut -d'=' -f2-)
    
    if [ -z "$value" ]; then
        echo -e "${RED}❌ $var${NC} - NOT SET"
        ALL_SET=false
    else
        # Mask sensitive values
        if [[ "$var" == *"SECRET"* ]] || [[ "$var" == *"KEY"* ]]; then
            masked="${value:0:10}...${value: -4}"
            echo -e "${GREEN}✅ $var${NC} - $masked"
        else
            echo -e "${GREEN}✅ $var${NC} - $value"
        fi
    fi
done

echo ""

if [ "$ALL_SET" = true ]; then
    echo -e "${GREEN}=========================================="
    echo "  ✓ All Stripe variables are set!"
    echo "==========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Verify webhook URL in Stripe Dashboard:"
    echo "   https://dashboard.stripe.com/test/webhooks"
    echo "   URL should be: https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook"
    echo ""
    echo "2. Test payment flow:"
    echo "   https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"
    echo ""
else
    echo -e "${YELLOW}=========================================="
    echo "  ⚠️  Some variables are missing"
    echo "==========================================${NC}"
    echo ""
    echo "To set missing variables:"
    echo ""
    echo "Option 1: Railway Dashboard (Easiest)"
    echo "1. Go to: https://railway.app"
    echo "2. Select 'AIAssistant' project"
    echo "3. Click your service → 'Variables' tab"
    echo "4. Add missing variables"
    echo ""
    echo "Option 2: Railway CLI"
    echo "railway variables --set \"VARIABLE_NAME=value\""
    echo ""
    echo "See RAILWAY_STRIPE_SETUP.md for detailed instructions"
    echo ""
fi

# Check webhook URL
echo "=========================================="
echo "  Webhook URL Check"
echo "=========================================="
echo ""
echo "Expected webhook URL:"
echo "https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook"
echo ""
echo "To verify in Stripe Dashboard:"
echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
echo "2. Find webhook: we_1SR4zwBk4MbPWMlrQLAtGDgw"
echo "3. Verify URL matches above"
echo ""

# Test webhook endpoint
echo "=========================================="
echo "  Testing Webhook Endpoint"
echo "=========================================="
echo ""

WEBHOOK_URL="https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook"

response=$(curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL" -X POST 2>/dev/null)

if [ "$response" = "400" ] || [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Webhook endpoint is accessible${NC}"
    echo "   Response code: $response (expected: 400 or 200)"
    echo "   Note: 400 is OK - means endpoint exists but needs proper Stripe signature"
else
    echo -e "${YELLOW}⚠️  Webhook endpoint check failed${NC}"
    echo "   Response code: $response"
    echo "   This might be normal if Railway is restarting"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "📖 Full guide: RAILWAY_STRIPE_SETUP.md"
echo ""



