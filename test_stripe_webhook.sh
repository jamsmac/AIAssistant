#!/bin/bash

# Test Stripe Webhook Setup
# Run this after updating webhook URL in Stripe Dashboard

echo "=== Stripe Webhook Test ==="
echo ""

# Backend URL
BACKEND_URL="https://aiassistant-production-7a4d.up.railway.app"

echo "1. Testing webhook endpoint..."
curl -X POST "$BACKEND_URL/api/credits/webhook" \
  -H "Content-Type: application/json" \
  -d '{"type": "checkout.session.completed"}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "2. Testing create checkout session (requires auth)..."
echo "   Visit: $BACKEND_URL/docs"
echo "   Or test via frontend: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"

echo ""
echo "=== Next Steps ==="
echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
echo "2. Find webhook: we_1SR4zwBk4MbPWMlrQLAtGDgw"
echo "3. Update endpoint URL to: $BACKEND_URL/api/credits/webhook"
echo "4. Test payment with card: 4242 4242 4242 4242"
echo ""
