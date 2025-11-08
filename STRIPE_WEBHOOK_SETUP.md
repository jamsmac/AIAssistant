# 🔗 Stripe Webhook Setup - Complete Guide

## Your Railway Webhook URL

```
https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
```

---

## Quick Setup (3 minutes)

### Step 1: Open Stripe Dashboard

Go to: **https://dashboard.stripe.com/test/webhooks**

### Step 2: Add Endpoint

1. Click **"Add endpoint"** button

2. Enter webhook URL:
   ```
   https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
   ```

3. Click **"Select events"**

4. Choose these events:
   - ☑️ `checkout.session.completed` (REQUIRED)
   - ☑️ `payment_intent.succeeded`
   - ☑️ `payment_intent.payment_failed`
   - ☑️ `charge.refunded`

5. Click **"Add endpoint"**

### Step 3: Get Webhook Secret

1. Click on your newly created endpoint

2. In the "Signing secret" section, click **"Reveal"**

3. Copy the secret (starts with `whsec_...`)

### Step 4: Set in Railway

Run this command with your webhook secret:

```bash
railway variables set STRIPE_WEBHOOK_SECRET="whsec_YOUR_SECRET_HERE"
```

---

## Verify Setup

### Test the Webhook

1. In Stripe Dashboard, go to your webhook endpoint

2. Click **"Send test webhook"**

3. Select event: `checkout.session.completed`

4. Click **"Send test webhook"**

5. Should see: **"Test webhook sent successfully"**

### Check Railway Logs

```bash
railway logs
```

Look for:
```
INFO: Webhook received without stripe-signature header
```
or
```
INFO: Handling Stripe webhook event: checkout.session.completed
```

---

## Complete Environment Variables Checklist

Make sure all these are set in Railway:

```bash
# Stripe (from .env.stripe file)
railway variables set STRIPE_SECRET_KEY="[from .env.stripe]"
railway variables set STRIPE_PUBLISHABLE_KEY="[from .env.stripe]"
railway variables set STRIPE_WEBHOOK_SECRET="whsec_[from Stripe Dashboard]"

# Frontend
railway variables set FRONTEND_URL="https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"

# AI APIs (add your own)
railway variables set OPENAI_API_KEY="sk-..."
railway variables set ANTHROPIC_API_KEY="sk-ant-..."
railway variables set GOOGLE_API_KEY="..."
```

---

## Test the Complete Flow

### 1. Visit Your Site
```
https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```

### 2. Register Account
- Click "Sign Up"
- Enter email and password

### 3. Purchase Credits
- Go to "Credits" page
- Click "Purchase" on Starter package ($10)

### 4. Complete Payment
- Use test card: `4242 4242 4242 4242`
- Expiry: `12/34`
- CVC: `123`
- ZIP: `12345`

### 5. Verify Success
- Should redirect to success page
- Should show: "1,000 credits added"
- Check Railway logs for webhook confirmation

---

## Troubleshooting

### Webhook not called

**Check**:
1. URL is correct in Stripe Dashboard
2. Railway deployment is running: `railway status`
3. Webhook secret is set: `railway variables`

**Fix**:
```bash
# Verify Railway is running
railway status

# Check logs for errors
railway logs

# Manually trigger webhook from Stripe Dashboard
```

### "Invalid signature" error

**Check**:
1. Webhook secret matches Stripe Dashboard
2. No extra spaces in the secret

**Fix**:
```bash
# Get fresh secret from Stripe Dashboard
# Set in Railway
railway variables set STRIPE_WEBHOOK_SECRET="whsec_NEW_SECRET"

# Restart Railway
railway up --detach
```

---

## Your URLs Summary

| Service | URL |
|---------|-----|
| **Frontend** | https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app |
| **Backend** | https://aiassistant-production-7a4d.up.railway.app |
| **Webhook** | https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook |
| **Stripe Dashboard** | https://dashboard.stripe.com/test/webhooks |
| **GitHub** | https://github.com/jamsmac/AIAssistant |

---

## Next Steps After Webhook Setup

1. ✅ Set environment variables in Railway
2. ✅ Test payment with test card
3. ✅ Verify credits added
4. ✅ Check transaction history
5. ✅ Test AI request with credits

---

**Ready to test your first payment!** 🎉

See [QUICK_START.md](QUICK_START.md) for the complete testing guide.
