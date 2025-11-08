# 🚀 Quick Start Guide - AI Assistant Platform

## Get Your Platform Running in 15 Minutes!

Your Stripe test keys are already configured. Follow these steps to launch.

---

## Step 1: Configure Railway Backend (5 minutes)

### Set Environment Variables

Run the Railway CLI commands:

```bash
# Stripe Keys (get from https://dashboard.stripe.com/test/apikeys)
railway variables set STRIPE_SECRET_KEY="sk_test_YOUR_KEY_HERE"
railway variables set STRIPE_PUBLISHABLE_KEY="pk_test_YOUR_KEY_HERE"

# Frontend URL (use your Vercel URL)
railway variables set FRONTEND_URL="https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"

# AI API Keys (add your own)
railway variables set OPENAI_API_KEY="sk-YOUR_KEY_HERE"
railway variables set ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"
railway variables set GOOGLE_API_KEY="YOUR_KEY_HERE"
```

### Get Your Railway URL

```bash
railway status
# Note your deployment URL: https://your-app.railway.app
```

---

## Step 2: Set Up Stripe Webhook (3 minutes)

### Create Webhook Endpoint

1. Go to: https://dashboard.stripe.com/test/webhooks

2. Click **"Add endpoint"**

3. Enter webhook URL:
   ```
   https://your-app.railway.app/api/credits/webhook
   ```
   (Replace with your actual Railway URL)

4. Select events to listen for:
   - ☑️ `checkout.session.completed`
   - ☑️ `payment_intent.succeeded`
   - ☑️ `payment_intent.payment_failed`
   - ☑️ `charge.refunded`

5. Click **"Add endpoint"**

### Get Webhook Secret

1. Click on your new webhook endpoint

2. Click **"Reveal"** under "Signing secret"

3. Copy the secret (starts with `whsec_...`)

4. Set it in Railway:
   ```bash
   railway variables set STRIPE_WEBHOOK_SECRET="whsec_..."
   ```

---

## Step 3: Configure Vercel Frontend (2 minutes)

### Set Environment Variables in Vercel Dashboard

1. Go to: https://vercel.com/vendhubs-projects/aiassistant/settings/environment-variables

2. Add these variables:

   **NEXT_PUBLIC_API_URL**:
   ```
   https://your-app.railway.app
   ```

   **NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY**:
   ```
   pk_test_YOUR_KEY_HERE
   ```
   (Get from https://dashboard.stripe.com/test/apikeys)

3. Redeploy frontend:
   ```bash
   cd web-ui
   vercel --prod
   ```

---

## Step 4: Test Payment Flow (5 minutes)

### 1. Visit Your Site

Go to: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app

### 2. Create Account

- Click "Sign Up"
- Enter email and password
- Register

### 3. Purchase Credits

- Click "Credits" in navigation
- Select "Starter Package" ($10)
- Click "Purchase"

### 4. Complete Payment (Stripe Test Mode)

You'll be redirected to Stripe Checkout. Use these **test card** details:

```
Card number: 4242 4242 4242 4242
Expiry: 12/34 (any future date)
CVC: 123 (any 3 digits)
ZIP: 12345 (any 5 digits)
Name: Test User
Email: test@example.com
```

### 5. Verify Success

After payment:
- You'll be redirected to success page
- Should show: "Payment Successful! 1,000 credits added"
- Click "View Transaction History" to see your purchase

### 6. Check Backend Logs

In Railway dashboard, check logs for:
```
INFO: Created Stripe checkout session cs_test_... for user 1
INFO: Handling Stripe webhook event: checkout.session.completed
INFO: Successfully added 1000 credits to user 1 from Stripe payment pi_...
```

✅ **Success!** Your payment system is working!

---

## Step 5: Test AI Request (2 minutes)

### 1. Go to Chat

Click "Chat" in navigation

### 2. Enter Prompt

Try: `"Write a Python function to calculate fibonacci numbers"`

### 3. View Cost Estimate

Should show:
- Estimated cost: ~5 credits
- Selected model: gpt-4o-mini
- Your balance: 1,000 credits

### 4. Submit Request

Click "Send" - AI response should appear

### 5. Check Credits

- Balance should be reduced (995 credits)
- Go to "Transaction History" to see AI request charge

✅ **Success!** Your AI system is working!

---

## Alternative: Use Setup Script

Or run the automated setup script:

```bash
./setup_stripe.sh
```

This script will:
- Configure Stripe keys in Railway
- Set up Vercel environment variables
- Show webhook setup instructions

---

## Test Card Numbers

Stripe provides various test cards for different scenarios:

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | ✅ Success |
| 4000 0000 0000 0002 | ❌ Declined |
| 4000 0000 0000 9995 | ❌ Insufficient funds |
| 4000 0000 0000 0077 | ❌ Expired card |
| 4000 0000 0000 0127 | ❌ Incorrect CVC |

All test cards:
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

---

## Troubleshooting

### Payment succeeds but no credits added

**Check**:
1. Railway logs for webhook errors
2. Stripe Dashboard → Webhooks → Events
3. Webhook secret is correct
4. Webhook URL is accessible

**Fix**:
- Manually trigger webhook from Stripe Dashboard
- Check `STRIPE_WEBHOOK_SECRET` environment variable
- Verify Railway deployment is running

### Frontend can't connect to backend

**Check**:
1. Vercel environment variables
2. Railway deployment status
3. CORS configuration

**Fix**:
- Set `NEXT_PUBLIC_API_URL` in Vercel
- Restart Vercel deployment
- Check Railway logs for errors

### "Invalid signature" error

**Check**:
1. Webhook secret matches Stripe Dashboard
2. Using correct mode (test vs live)

**Fix**:
- Get fresh webhook secret from Stripe
- Update `STRIPE_WEBHOOK_SECRET` in Railway
- Restart Railway deployment

---

## What's Next?

### Immediate Testing
- [ ] Test all 5 credit packages
- [ ] Try different AI prompts
- [ ] Check admin panel analytics
- [ ] Test transaction history pagination

### Before Production Launch
- [ ] Switch Stripe to Live mode
- [ ] Get live API keys from Stripe
- [ ] Update webhook to use live keys
- [ ] Test with small real payment ($10)
- [ ] Set up monitoring and alerts

### Feature Additions
- [ ] Add email notifications
- [ ] Implement subscription plans
- [ ] Save payment methods
- [ ] Add referral system

---

## Your URLs

**Frontend (Vercel)**:
```
https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```

**Backend (Railway)**:
```
https://your-app.railway.app
```
(Get from `railway status`)

**Stripe Dashboard**:
```
https://dashboard.stripe.com/test/dashboard
```

**GitHub Repository**:
```
https://github.com/jamsmac/AIAssistant
```

---

## Support

### Documentation
- [STRIPE_SETUP.md](STRIPE_SETUP.md) - Complete Stripe guide
- [LAUNCH_STATUS.md](LAUNCH_STATUS.md) - Deployment status
- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - Full docs

### Resources
- [Stripe Test Cards](https://stripe.com/docs/testing)
- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)

---

## 🎉 Congratulations!

You now have a fully functional AI assistant platform with real payment processing!

**Your platform includes**:
- ✅ Credit-based pricing
- ✅ Stripe payments
- ✅ 22 AI models
- ✅ Intelligent routing
- ✅ Beautiful UI
- ✅ Admin dashboard

**Ready to accept real payments!** 💰

---

**Last Updated**: November 7, 2025
**Status**: ✅ Ready for Testing
**Test Mode**: Active
