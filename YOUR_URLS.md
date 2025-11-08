# 🌐 Your Platform URLs

## Production URLs

### Frontend (Vercel)
```
https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```
- User registration and login
- Credit purchase page
- Transaction history
- AI chat interface
- Admin dashboard

### Backend (Railway)
```
https://aiassistant-production-7a4d.up.railway.app
```
- REST API endpoints
- Automatic deploys from GitHub

### Stripe Webhook
```
https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
```
**Use this URL in Stripe Dashboard!**

---

## Setup Links

### Stripe Dashboard (Test Mode)
```
https://dashboard.stripe.com/test/webhooks
```
Create webhook with the URL above ☝️

### GitHub Repository
```
https://github.com/jamsmac/AIAssistant
```
All code and documentation

---

## Quick Commands

### Set Railway Variables
```bash
# Run the setup script
./set_railway_vars.sh

# Or manually:
railway variables --set "STRIPE_SECRET_KEY=[from .env.stripe]"
railway variables --set "STRIPE_PUBLISHABLE_KEY=[from .env.stripe]"
railway variables --set "FRONTEND_URL=https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app"
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_[from Stripe]"
```

### Check Deployment
```bash
railway status
railway logs
```

---

## Test Payment

1. **Visit**: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
2. **Register**: Create account
3. **Buy Credits**: Starter package ($10)
4. **Test Card**: 4242 4242 4242 4242
5. **Verify**: Should see 1,000 credits added

---

## Documentation

- [STRIPE_WEBHOOK_SETUP.md](STRIPE_WEBHOOK_SETUP.md) - Webhook setup guide
- [QUICK_START.md](QUICK_START.md) - Complete setup
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Overview

---

✅ **Your webhook URL**: https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
