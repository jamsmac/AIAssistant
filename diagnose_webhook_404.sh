#!/bin/bash

# Diagnose Webhook 404 Issue
# This script helps identify why /api/credits/webhook returns 404

echo "=== Webhook 404 Diagnosis ==="
echo ""

# Check if backend is running
echo "1. Checking backend health..."
BACKEND_URL="https://aiassistant-production-7a4d.up.railway.app"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health")
echo "   Health endpoint status: $HEALTH_STATUS"

if [ "$HEALTH_STATUS" != "200" ]; then
    echo "   ❌ Backend is not healthy!"
    exit 1
else
    echo "   ✅ Backend is healthy"
fi

echo ""

# Check if webhook endpoint exists
echo "2. Checking webhook endpoint..."
WEBHOOK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/credits/webhook")
echo "   Webhook endpoint status: $WEBHOOK_STATUS"

if [ "$WEBHOOK_STATUS" == "404" ]; then
    echo "   ❌ Webhook endpoint returns 404 - router not loaded!"
    echo ""
    echo "   Possible causes:"
    echo "   - Credit router failed to import"
    echo "   - Credit manager module not found"
    echo "   - Database tables missing"
    echo "   - Railway environment variables missing"
    echo ""
    echo "   Next steps:"
    echo "   1. Check Railway logs for import errors"
    echo "   2. Verify credit_manager.py exists"
    echo "   3. Check database tables exist"
    echo "   4. Redeploy the service"
    exit 1
elif [ "$WEBHOOK_STATUS" == "405" ]; then
    echo "   ✅ Webhook endpoint exists (405 = Method Not Allowed, expected for GET)"
else
    echo "   ✅ Webhook endpoint responds with status: $WEBHOOK_STATUS"
fi

echo ""

# Check Railway logs for router loading
echo "3. Checking Railway logs for router loading..."
echo "   Run this command to see logs:"
echo "   railway logs --service a356894b-78b6-4746-8cf4-69103f40b474 | grep -E '(Credit router|credit_router|Could not load)' | tail -10"

echo ""

# Check environment variables
echo "4. Checking environment variables..."
echo "   Run this command to check Stripe vars:"
echo "   railway variables --service a356894b-78b6-4746-8cf4-69103f40b474 | grep STRIPE"

echo ""

# Test webhook with proper payload
echo "5. Testing webhook with proper payload..."
WEBHOOK_TEST=$(curl -s -X POST "$BACKEND_URL/api/credits/webhook" \
  -H "Content-Type: application/json" \
  -H "stripe-signature: test_sig" \
  -d '{"type": "checkout.session.completed"}' \
  -w "Status: %{http_code}")

echo "   Webhook test result: $WEBHOOK_TEST"

echo ""

# Summary
if [ "$WEBHOOK_STATUS" == "404" ]; then
    echo "=== SUMMARY ==="
    echo "❌ PROBLEM: Webhook endpoint /api/credits/webhook returns 404"
    echo "🔧 SOLUTION: Credit router failed to load during startup"
    echo ""
    echo "Check Railway logs for specific error messages:"
    echo "railway logs --service a356894b-78b6-4746-8cf4-69103f40b474 | grep -A5 -B5 'Could not load'"
else
    echo "=== SUMMARY ==="
    echo "✅ SUCCESS: Webhook endpoint is accessible"
    echo "🎉 Ready for Stripe webhook configuration!"
fi

echo ""
echo "=== Next Steps ==="
echo "1. If 404 persists: Check Railway logs for import errors"
echo "2. If working: Update webhook URL in Stripe Dashboard"
echo "3. Test with real payment to verify end-to-end flow"

