# 🚀 Railway Stripe Setup - Complete Guide

## Quick Setup Checklist (5 minutes)

Follow these steps to set up Stripe payments in Railway:

---

## Step 1: Set Variables in Railway (3 minutes)

### Option A: Using Railway Web Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Open: https://railway.app
   - Click on **"AIAssistant"** project
   - Select your service (backend service)

2. **Open Variables Tab**
   - Click on **"Variables"** tab
   - You'll see all current environment variables

3. **Add These 4 Variables:**

   | Variable Name | Value Source | Example |
   |--------------|--------------|---------|
   | `STRIPE_SECRET_KEY` | From `.env.stripe` file | `sk_test_...` |
   | `STRIPE_PUBLISHABLE_KEY` | From `.env.stripe` file | `pk_test_...` |
   | `STRIPE_WEBHOOK_SECRET` | From Stripe Dashboard (Step 2) | `whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB` |
   | `FRONTEND_URL` | Your Vercel URL | `https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app` |

4. **For each variable:**
   - Click **"+ New Variable"**
   - Enter variable name (exactly as shown above)
   - Enter value
   - Click **"Add"**

### Option B: Using Railway CLI

If you have Railway CLI installed and linked:

```bash
# Set Stripe Secret Key (from .env.stripe)
railway variables --set "STRIPE_SECRET_KEY=sk_test_YOUR_KEY"

# Set Stripe Publishable Key (from .env.stripe)
railway variables --set "STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY"

# Set Webhook Secret (from Stripe Dashboard)
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB"

# Set Frontend URL
railway variables --set "FRONTEND_URL=https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"
```

### Finding Your Stripe Keys

If you don't have `.env.stripe` file:

1. Go to: https://dashboard.stripe.com/test/apikeys
2. Copy **"Secret key"** (starts with `sk_test_`)
3. Copy **"Publishable key"** (starts with `pk_test_`)

---

## Step 2: Update Webhook URL in Stripe (1 minute)

### Current Webhook Info

- **Webhook ID**: `we_1SR4zwBk4MbPWMlrQLAtGDgw`
- **Current URL**: (needs to be updated)
- **New URL**: `https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook`

### Steps to Update

1. **Go to Stripe Dashboard**
   - Open: https://dashboard.stripe.com/test/webhooks
   - Find webhook: `we_1SR4zwBk4MbPWMlrQLAtGDgw`

2. **Edit Webhook**
   - Click on the webhook endpoint
   - Click **"..."** menu (three dots) → **"Update details"**
   - Or click **"Edit"** button

3. **Update URL**
   - In "Endpoint URL" field, enter:
     ```
     https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
     ```
   - Click **"Update endpoint"**

4. **Get Webhook Secret** (if not already set)
   - After updating, find **"Signing secret"** section
   - Click **"Reveal"**
   - Copy the secret (starts with `whsec_...`)
   - Add to Railway variables (if different from the one you already have)

### Verify Webhook Events

Make sure these events are selected:
- ✅ `checkout.session.completed` (REQUIRED)
- ✅ `payment_intent.succeeded` (recommended)
- ✅ `payment_intent.payment_failed` (recommended)
- ✅ `charge.refunded` (recommended)

---

## Step 3: Test Payment Flow (1 minute)

### Test Steps

1. **Visit Your Site**
   ```
   https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
   ```

2. **Register Account**
   - Click "Sign Up" or "Register"
   - Enter email and password
   - Complete registration

3. **Purchase Credits**
   - Navigate to "Credits" page (or "Buy Credits")
   - Click **"Purchase"** on **Starter** package ($10)

4. **Complete Payment**
   - You'll be redirected to Stripe Checkout
   - Use Stripe test card:
     - **Card Number**: `4242 4242 4242 4242`
     - **Expiry**: `12/34` (any future date)
     - **CVC**: `123` (any 3 digits)
     - **ZIP**: `12345` (any 5 digits)
   - Click **"Pay"**

5. **Verify Success**
   - Should redirect to `/credits/success` page
   - Should show: **"1,000 credits added"**
   - Check your credit balance - should show 1,000 credits

### Verify in Railway Logs

```bash
railway logs
```

Look for:
```
INFO: Handling Stripe webhook event: checkout.session.completed
INFO: Successfully added 1000 credits to user X from Stripe payment pi_...
```

### Verify in Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/payments
2. Should see successful payment
3. Click on payment → Check metadata includes `user_id` and `package_id`

---

## Troubleshooting

### Problem: Variables not set

**Check:**
```bash
railway variables
```

**Fix:**
- Make sure you're in the correct project and service
- Variables are case-sensitive
- No extra spaces in variable names or values

### Problem: Webhook not receiving events

**Check:**
1. Webhook URL is correct in Stripe Dashboard
2. Railway deployment is running: `railway status`
3. Webhook secret matches: Compare `STRIPE_WEBHOOK_SECRET` in Railway with Stripe Dashboard

**Fix:**
- Test webhook manually from Stripe Dashboard
- Check Railway logs for errors
- Verify webhook URL is accessible (should return 200 OK)

### Problem: "Invalid signature" error

**Check:**
- `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
- No extra spaces or newlines in the secret
- Using correct secret for test/live mode

**Fix:**
```bash
# Get fresh secret from Stripe Dashboard
# Set in Railway
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_NEW_SECRET"

# Restart Railway service
railway restart
```

### Problem: Payment succeeds but credits not added

**Check:**
1. Railway logs for webhook errors
2. Stripe Dashboard → Webhooks → Event details
3. Database `credit_transactions` table

**Fix:**
- Check webhook signature verification is passing
- Verify `user_id` is in checkout session metadata
- Check `credit_manager.add_credits()` is being called

### Problem: Redirects not working

**Check:**
- `FRONTEND_URL` is set correctly in Railway
- URL uses HTTPS in production
- Success/cancel URLs are correct

**Fix:**
```bash
railway variables --set "FRONTEND_URL=https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"
```

---

## Complete Environment Variables Checklist

Make sure ALL these are set in Railway:

```bash
# Stripe (REQUIRED)
✅ STRIPE_SECRET_KEY=sk_test_...
✅ STRIPE_PUBLISHABLE_KEY=pk_test_...
✅ STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend (REQUIRED)
✅ FRONTEND_URL=https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app

# Database (should already be set)
✅ DATABASE_URL=postgresql://...

# AI API Keys (should already be set)
✅ OPENAI_API_KEY=sk-...
✅ ANTHROPIC_API_KEY=sk-ant-...
✅ GOOGLE_API_KEY=...
```

---

## Your URLs Summary

| Service | URL |
|---------|-----|
| **Frontend** | https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app |
| **Backend API** | https://aiassistant-production-7a4d.up.railway.app |
| **Webhook Endpoint** | https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook |
| **Stripe Dashboard** | https://dashboard.stripe.com/test/webhooks |
| **Railway Dashboard** | https://railway.app |

---

## Next Steps After Setup

1. ✅ Test payment with test card
2. ✅ Verify credits are added correctly
3. ✅ Check transaction history
4. ✅ Test AI request with credits
5. ✅ Monitor Railway logs for any issues

---

## Quick Reference Commands

```bash
# View all Railway variables
railway variables

# Set a variable
railway variables --set "VARIABLE_NAME=value"

# View Railway logs
railway logs

# Check Railway status
railway status

# Restart Railway service
railway restart
```

---

**Ready to test your first payment!** 🎉

If you encounter any issues, check the troubleshooting section above or see:
- [STRIPE_SETUP.md](STRIPE_SETUP.md) - Detailed Stripe setup guide
- [STRIPE_WEBHOOK_SETUP.md](STRIPE_WEBHOOK_SETUP.md) - Webhook-specific guide
- [UPDATE_WEBHOOK.md](UPDATE_WEBHOOK.md) - Webhook URL update guide



