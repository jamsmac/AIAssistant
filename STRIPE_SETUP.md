# Stripe Payment Integration Setup

## Overview

This guide explains how to set up Stripe payments for the credit system in production.

## Prerequisites

1. A Stripe account (sign up at [stripe.com](https://stripe.com))
2. Access to your Stripe Dashboard
3. SSL certificate for your production domain (required for webhooks)

---

## Step 1: Get Stripe API Keys

### Development (Test Mode)

1. Log into Stripe Dashboard: https://dashboard.stripe.com/test/apikeys
2. Click "Developers" → "API keys"
3. Copy your **Publishable key** (starts with `pk_test_`)
4. Copy your **Secret key** (starts with `sk_test_`)

### Production (Live Mode)

1. Activate your Stripe account (requires business verification)
2. Switch to "Live mode" in Stripe Dashboard
3. Go to "Developers" → "API keys"
4. Copy your **Publishable key** (starts with `pk_live_`)
5. Copy your **Secret key** (starts with `sk_live_`)

---

## Step 2: Set Environment Variables

### Backend (.env or environment)

Add these variables to your backend environment:

```bash
# Stripe Secret Key (REQUIRED)
STRIPE_SECRET_KEY=sk_test_...  # Use sk_live_... in production

# Stripe Webhook Secret (REQUIRED for webhooks)
STRIPE_WEBHOOK_SECRET=whsec_...  # Get from Step 3

# Frontend URL (for payment redirects)
FRONTEND_URL=http://localhost:3000  # Your frontend URL
```

### Frontend (.env.local)

Add these variables to your Next.js frontend:

```bash
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000  # Your backend URL

# Stripe Publishable Key (optional, for future client-side features)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Step 3: Set Up Stripe Webhooks

Webhooks allow Stripe to notify your backend when payments are completed.

### Development (Local Testing)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Other OS
   # See https://stripe.com/docs/stripe-cli#install
   ```

2. Log in to Stripe CLI:
   ```bash
   stripe login
   ```

3. Forward webhooks to your local backend:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/credits/webhook
   ```

4. Copy the webhook signing secret (starts with `whsec_`) and add to your `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### Production

1. Go to Stripe Dashboard → "Developers" → "Webhooks"
2. Click "Add endpoint"
3. Enter your webhook URL:
   ```
   https://your-domain.com/api/credits/webhook
   ```

4. Select events to listen for:
   - `checkout.session.completed` (REQUIRED)
   - `payment_intent.succeeded` (recommended)
   - `payment_intent.payment_failed` (recommended)
   - `charge.refunded` (recommended)

5. Click "Add endpoint"

6. Click on your new endpoint, then click "Reveal" under "Signing secret"

7. Copy the webhook secret (starts with `whsec_`) and add to your production environment:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## Step 4: Update Frontend URLs

### In Backend Code

Update [api/routers/credit_router.py](api/routers/credit_router.py:189):

```python
# Replace this:
base_url = "http://localhost:3000"  # TODO: Get from config

# With this:
base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
```

Add to your environment:
```bash
FRONTEND_URL=https://your-frontend-domain.com
```

### In Frontend Code

The frontend already uses `process.env.NEXT_PUBLIC_API_URL`, so just ensure it's set correctly in your deployment platform (Vercel, Railway, etc.)

---

## Step 5: Test the Integration

### 1. Start your backend:
```bash
cd autopilot-core
python3 -m uvicorn api.server:app --reload
```

### 2. Start Stripe webhook forwarding (development only):
```bash
stripe listen --forward-to http://localhost:8000/api/credits/webhook
```

### 3. Start your frontend:
```bash
cd web-ui
npm run dev
```

### 4. Test a payment:

1. Go to http://localhost:3000/credits
2. Click "Purchase" on any package
3. You'll be redirected to Stripe Checkout
4. Use Stripe test card:
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/34`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)

5. Complete the payment
6. You'll be redirected back to `/credits/success`
7. Credits should be added to your account automatically via webhook

### 5. Verify in logs:

Backend logs should show:
```
INFO: Handling Stripe webhook event: checkout.session.completed
INFO: Successfully added 1000 credits to user 1 from Stripe payment pi_...
```

---

## Step 6: Production Checklist

Before going live:

- [ ] Switch to Stripe Live mode keys
- [ ] Update `STRIPE_SECRET_KEY` with live key
- [ ] Set up production webhook endpoint
- [ ] Update `STRIPE_WEBHOOK_SECRET` with production webhook secret
- [ ] Update `FRONTEND_URL` to production domain
- [ ] Test with real (small) payment
- [ ] Verify credits are added correctly
- [ ] Check transaction history
- [ ] Verify email receipts are sent by Stripe

---

## Troubleshooting

### Problem: Webhook not receiving events

**Solution:**
- Check Stripe Dashboard → "Developers" → "Webhooks" → "Events"
- Verify webhook URL is correct and accessible
- Check webhook signing secret is correct
- Verify your backend is running and accessible from internet

### Problem: Payment succeeds but credits not added

**Solution:**
- Check backend logs for webhook errors
- Verify webhook signature verification is passing
- Check `credit_transactions` table in database
- Look for errors in Stripe Dashboard → "Webhooks" → "Event details"

### Problem: "Invalid signature" error

**Solution:**
- Verify `STRIPE_WEBHOOK_SECRET` matches the one in Stripe Dashboard
- Ensure you're using the correct secret for test/live mode
- Check you haven't accidentally included spaces or newlines in the secret

### Problem: Redirects not working

**Solution:**
- Verify `FRONTEND_URL` is set correctly
- Check success/cancel URLs in checkout session creation
- Ensure URLs are using HTTPS in production

---

## Security Best Practices

1. **Never commit API keys to git**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Use webhook signatures**
   - Always verify webhook signatures
   - Never skip signature verification in production

3. **Use HTTPS in production**
   - Stripe requires HTTPS for webhooks
   - Use SSL certificates for your domain

4. **Validate webhook events**
   - Check event type before processing
   - Verify user_id and amounts match expected values
   - Log all webhook events for audit

5. **Handle idempotency**
   - Stripe may send the same webhook multiple times
   - Use payment_intent ID to prevent duplicate credit additions
   - Current implementation adds credits once per payment_intent

---

## API Endpoints Reference

### POST /api/credits/purchase
Creates a Stripe Checkout session.

**Request:**
```json
{
  "package_id": 1,
  "payment_method": "stripe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Checkout session created",
  "payment_url": "https://checkout.stripe.com/..."
}
```

### POST /api/credits/webhook
Receives Stripe webhook events (called by Stripe, not your frontend).

**Headers:**
```
stripe-signature: t=...,v1=...
```

**Response:**
```json
{
  "success": true,
  "received": true
}
```

### GET /api/credits/session/{session_id}
Check checkout session status after payment.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "cs_...",
    "payment_status": "paid",
    "amount_total": 1000,
    "metadata": {...}
  }
}
```

---

## Cost Structure

The platform uses a **15% markup** on AI model costs:

| Package | Credits | Price | Effective Cost |
|---------|---------|-------|----------------|
| Starter | 1,000 | $10 | $0.010/credit |
| Basic | 5,500 | $45 | $0.008/credit |
| Pro | 13,500 | $100 | $0.007/credit |
| Business | 35,000 | $225 | $0.006/credit |
| Enterprise | 120,000 | $700 | $0.006/credit |

**Example:**
- User purchases "Starter" package ($10)
- Stripe charges $10
- User receives 1,000 credits
- Platform profit: ~15% of AI usage costs

---

## Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Testing Stripe](https://stripe.com/docs/testing)

---

**Last Updated**: November 7, 2025
**Status**: ✅ Ready for Production
