# 🔧 Set Railway Variables Manually

## Railway CLI Issue

The Railway CLI shows "No service linked". Let's set the variables through the Railway web dashboard instead.

---

## Quick Method: Railway Web Dashboard

### Step 1: Open Railway Dashboard

Go to: **https://railway.app/project/[your-project-id]/service**

Or simply go to: **https://railway.app** and click on your "AIAssistant" project

### Step 2: Select Your Service

Click on your service (should be the main backend service)

### Step 3: Go to Variables Tab

Click on the **"Variables"** tab

### Step 4: Add These Variables

Click **"+ New Variable"** for each:

#### 1. STRIPE_SECRET_KEY
```
[Copy from .env.stripe file]
```
(starts with `sk_test_...`)

#### 2. STRIPE_PUBLISHABLE_KEY
```
[Copy from .env.stripe file]
```
(starts with `pk_test_...`)

#### 3. STRIPE_WEBHOOK_SECRET
```
whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB
```
(from your Stripe webhook endpoint)

#### 4. FRONTEND_URL
```
https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```

#### 5. OPENAI_API_KEY (if you have one)
```
sk-YOUR_OPENAI_KEY_HERE
```

#### 6. ANTHROPIC_API_KEY (if you have one)
```
sk-ant-YOUR_ANTHROPIC_KEY_HERE
```

#### 7. GOOGLE_API_KEY (if you have one)
```
YOUR_GOOGLE_KEY_HERE
```

### Step 5: Deploy

After adding all variables, Railway will automatically redeploy your service.

Wait for the deployment to complete (usually 1-2 minutes).

---

## Alternative: Fix Railway CLI

If you want to use the CLI, link the service first:

```bash
# List available services
railway status

# Link to a specific service (if needed)
railway link
```

Then you can use:
```bash
railway variables --set "STRIPE_SECRET_KEY=sk_test_..."
```

But the web dashboard is easier! 👍

---

## Verify Variables Are Set

### Method 1: Railway Dashboard
1. Go to your service → Variables tab
2. You should see all 4-7 variables listed

### Method 2: Railway CLI
```bash
railway variables
```

Should show all your variables (values will be hidden for security)

---

## After Setting Variables

### Test Your Setup

1. **Check Deployment Status**
   ```bash
   railway status
   ```

2. **View Logs**
   ```bash
   railway logs
   ```

3. **Test Backend Health**
   ```bash
   curl https://aiassistant-production-7a4d.up.railway.app/health
   ```

### Test Payment Flow

1. Visit: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
2. Register account
3. Go to Credits page
4. Purchase Starter package ($10)
5. Use test card: `4242 4242 4242 4242`
6. Should redirect to Stripe checkout
7. Complete payment
8. Should redirect back and show 1,000 credits added!

---

## Troubleshooting

### Variables Not Showing Up

- Make sure you clicked "Add" after entering each variable
- Check you're in the correct service
- Wait for deployment to complete

### Deployment Failed

- Check Railway logs for errors
- Verify all variable values are correct
- Make sure no extra spaces in the values

### Frontend Can't Connect to Backend

Make sure Vercel has these variables:
1. Go to: https://vercel.com/vendhubs-projects/aiassistant/settings/environment-variables
2. Add:
   - `NEXT_PUBLIC_API_URL` = `https://aiassistant-production-7a4d.up.railway.app`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = `pk_test_51SJZ...`

---

## Your Complete Setup

Once all variables are set:

✅ **Stripe Keys**: Set in Railway
✅ **Webhook Secret**: Set in Railway
✅ **Frontend URL**: Set in Railway
✅ **Webhook Endpoint**: Created in Stripe (update URL if needed)

**Ready to test payments!** 🎉

---

## Quick Reference

| Variable | Source |
|----------|--------|
| `STRIPE_SECRET_KEY` | From `.env.stripe` file (sk_test_...) |
| `STRIPE_PUBLISHABLE_KEY` | From `.env.stripe` file (pk_test_...) |
| `STRIPE_WEBHOOK_SECRET` | whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB |
| `FRONTEND_URL` | https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app |

**Webhook URL**: https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook

---

🚀 **Next**: Test your first payment!
