# ⚡ Stripe Quick Setup - 5 Minutes

## 🎯 Your Task

Set up Stripe payment integration in Railway and test it.

---

## ✅ Step 1: Set Variables in Railway (3 minutes)

### Go to Railway Dashboard

1. Open: **https://railway.app**
2. Click **"AIAssistant"** project
3. Select your **backend service**
4. Click **"Variables"** tab

### Add These 4 Variables:

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `STRIPE_SECRET_KEY` | `sk_test_...` | From `.env.stripe` or https://dashboard.stripe.com/test/apikeys |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` | From `.env.stripe` or https://dashboard.stripe.com/test/apikeys |
| `STRIPE_WEBHOOK_SECRET` | `whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB` | From Stripe Dashboard (see Step 2) |
| `FRONTEND_URL` | `https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app` | Your Vercel URL |

**For each variable:**
- Click **"+ New Variable"**
- Enter name exactly as shown
- Paste value
- Click **"Add"**

---

## ✅ Step 2: Update Webhook URL in Stripe (1 minute)

### Go to Stripe Dashboard

1. Open: **https://dashboard.stripe.com/test/webhooks**
2. Find webhook: **`we_1SR4zwBk4MbPWMlrQLAtGDgw`**
3. Click on it

### Update URL

1. Click **"..."** menu → **"Update details"**
2. Change **"Endpoint URL"** to:
   ```
   https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
   ```
3. Click **"Update endpoint"**

### Get Webhook Secret (if needed)

1. Find **"Signing secret"** section
2. Click **"Reveal"**
3. Copy secret (starts with `whsec_...`)
4. Add to Railway variables if different from the one provided

---

## ✅ Step 3: Test Payment (1 minute)

### Visit Your Site

```
https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```

### Test Flow

1. **Register Account**
   - Click "Sign Up"
   - Enter email and password

2. **Purchase Credits**
   - Go to "Credits" page
   - Click **"Purchase"** on **Starter** package ($10)

3. **Complete Payment**
   - Use Stripe test card:
     - Card: `4242 4242 4242 4242`
     - Expiry: `12/34`
     - CVC: `123`
     - ZIP: `12345`
   - Click **"Pay"**

4. **Verify Success**
   - Should redirect to success page
   - Should show: **"1,000 credits added"**
   - Check balance - should be 1,000 credits

---

## 🔍 Verify Setup

### Check Railway Variables

Run this script:
```bash
./check_stripe_setup.sh
```

Or manually check:
```bash
railway variables
```

### Check Railway Logs

```bash
railway logs
```

Look for:
```
INFO: Handling Stripe webhook event: checkout.session.completed
INFO: Successfully added 1000 credits to user X
```

### Check Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/payments
2. Should see successful test payment
3. Check webhook events: https://dashboard.stripe.com/test/webhooks

---

## 🐛 Troubleshooting

### Variables Not Set?

- Make sure you're in correct Railway project/service
- Variables are case-sensitive
- No extra spaces

### Webhook Not Working?

- Verify URL in Stripe Dashboard matches exactly
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
- Test webhook manually from Stripe Dashboard

### Payment Succeeds But No Credits?

- Check Railway logs for errors
- Verify webhook is receiving events in Stripe Dashboard
- Check `user_id` is in checkout session metadata

---

## 📚 Full Documentation

- **Complete Guide**: [RAILWAY_STRIPE_SETUP.md](RAILWAY_STRIPE_SETUP.md)
- **Stripe Setup**: [STRIPE_SETUP.md](STRIPE_SETUP.md)
- **Webhook Setup**: [STRIPE_WEBHOOK_SETUP.md](STRIPE_WEBHOOK_SETUP.md)

---

## 🎉 You're Done!

After completing these 3 steps, your Stripe integration should be working!

**Test it now:**
1. Visit your site
2. Register account
3. Buy Starter package
4. Verify 1,000 credits added

---

**Quick Links:**
- Railway: https://railway.app
- Stripe Dashboard: https://dashboard.stripe.com/test/webhooks
- Your Site: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app


