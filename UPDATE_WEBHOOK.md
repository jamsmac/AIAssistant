# ⚠️ UPDATE YOUR STRIPE WEBHOOK URL

## Current Status

You've created a webhook endpoint, but it has the wrong URL!

**Your Webhook ID**: `we_1SR4zwBk4MbPWMlrQLAtGDgw`

**Current URL** (WRONG):
```
❌ https://your-railway-url.railway.app/api/credits/webhook
```

**Correct URL** (NEED TO UPDATE):
```
✅ https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
```

---

## How to Update (2 minutes)

### Step 1: Open Your Webhook

Go to: **https://dashboard.stripe.com/test/webhooks**

You should see your webhook endpoint with ID: `we_1SR4zwBk4MbPWMlrQLAtGDgw`

### Step 2: Edit the Endpoint

1. Click on the webhook endpoint
2. Click the **"..."** menu (three dots) in the top right
3. Select **"Update details"**

### Step 3: Change the URL

In the "Endpoint URL" field, replace:
```
https://your-railway-url.railway.app/api/credits/webhook
```

With:
```
https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
```

### Step 4: Save

Click **"Update endpoint"**

### Step 5: Get Webhook Secret

1. After updating, you'll see the webhook details page
2. Find the "Signing secret" section
3. Click **"Reveal"** to show the secret
4. Copy the secret (starts with `whsec_...`)

### Step 6: Set in Railway

Run this command with your webhook secret:

```bash
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE"
```

---

## Verify It Works

### Test the Webhook

1. In Stripe Dashboard, go to your webhook endpoint
2. Click **"Send test webhook"**
3. Select event: `checkout.session.completed`
4. Click **"Send test webhook"**

### Check Railway Logs

```bash
railway logs
```

Should see:
```
INFO: Handling Stripe webhook event: checkout.session.completed
```

---

## Complete Setup Checklist

After updating the webhook URL:

- [x] ✅ Webhook endpoint created in Stripe
- [ ] ⚠️ **Update webhook URL** (do this now!)
- [ ] 🔑 Set `STRIPE_WEBHOOK_SECRET` in Railway
- [ ] 🔑 Set `STRIPE_SECRET_KEY` in Railway
- [ ] 🔑 Set `STRIPE_PUBLISHABLE_KEY` in Railway
- [ ] 🌐 Set `FRONTEND_URL` in Railway
- [ ] 🧪 Test payment with card 4242 4242 4242 4242

---

## Quick Reference

### Your URLs

| What | URL |
|------|-----|
| **Webhook URL** | https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook |
| **Frontend** | https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app |
| **Backend API** | https://aiassistant-production-7a4d.up.railway.app |
| **Stripe Dashboard** | https://dashboard.stripe.com/test/webhooks |

### Set All Railway Variables

```bash
# Use the setup script
./set_railway_vars.sh

# Then add webhook secret
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET"
```

---

## After Updating

Once the webhook URL is corrected and all variables are set:

1. **Test Payment Flow**:
   - Visit: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
   - Register account
   - Purchase Starter package ($10)
   - Use test card: `4242 4242 4242 4242`
   - Verify 1,000 credits added

2. **Check Logs**:
   ```bash
   railway logs
   ```

3. **Verify in Stripe**:
   - Check Dashboard → Payments
   - Should see successful test payment

---

🎯 **Action Required**: Update your webhook URL in Stripe Dashboard now!

See [STRIPE_WEBHOOK_SETUP.md](STRIPE_WEBHOOK_SETUP.md) for detailed setup instructions.
