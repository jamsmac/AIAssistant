# 🚀 Railway Deployment - Complete Guide

This project is **100% ready** for Railway deployment!

---

## ⚡ Quick Deploy (30 seconds)

```bash
./deploy_railway.sh
```

That's it! The script handles everything automatically.

---

## 📋 What's Included

| File | Purpose | Size |
|------|---------|------|
| `Procfile` | Railway start command | 56 B |
| `deploy_railway.sh` | Automated deployment script | 6.5 KB |
| `RAILWAY_DEPLOY_STEPS.md` | Detailed manual instructions | 6.2 KB |
| `DEPLOY_QUICK.md` | Quick reference guide | 2.0 KB |

---

## 🎯 Three Ways to Deploy

### 1️⃣ Automated (Recommended)
```bash
./deploy_railway.sh
```
- **Time:** 3-5 minutes
- **Difficulty:** Easy
- **Best for:** First-time deployment

### 2️⃣ Manual Step-by-Step
```bash
cat RAILWAY_DEPLOY_STEPS.md
```
- **Time:** 5-7 minutes  
- **Difficulty:** Medium
- **Best for:** Learning the process

### 3️⃣ Quick Commands
```bash
cat DEPLOY_QUICK.md
```
- **Time:** 2-3 minutes
- **Difficulty:** Advanced
- **Best for:** Experienced users

---

## 🔧 Requirements

- ✅ Railway CLI installed (`/usr/local/bin/railway`)
- ✅ Railway account (free)
- ✅ GitHub/Google/Email for login
- ✅ `.env` file configured

---

## 📊 What You Get

After deployment:

- ✅ **Production URL:** `https://your-app.up.railway.app`
- ✅ **HTTPS/SSL:** Automatic & free
- ✅ **19 API Endpoints:** All working
- ✅ **JWT Auth:** Fully functional
- ✅ **Swagger UI:** Available at `/docs`
- ✅ **Health Monitoring:** Built-in
- ✅ **Free Tier:** 500 hours/month + $5 credits

---

## 🚀 Deployment Process

The automated script will:

1. ✅ Check Railway CLI installation
2. ✅ Login (opens browser)
3. ✅ Initialize project
4. ✅ Set environment variables from `.env`
5. ✅ Deploy application
6. ✅ Provide production URL

**Total time:** 3-5 minutes

---

## 🔐 Environment Variables

Automatically configured from your `.env`:

- `SECRET_KEY` - JWT secret
- `JWT_EXPIRATION_HOURS` - Token lifetime
- `GEMINI_API_KEY` - Google Gemini
- `OPENROUTER_API_KEY` - OpenRouter
- `ANTHROPIC_API_KEY` - Claude
- `OPENAI_API_KEY` - GPT-4
- `DATABASE_PATH` - SQLite path

---

## ✅ Post-Deployment Testing

```bash
# Get your URL
railway domain

# Health check
curl https://YOUR_URL/api/health

# Test registration
curl -X POST https://YOUR_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@prod.com","password":"testpass123"}'

# Open API docs
open https://YOUR_URL/docs
```

---

## 🔧 Useful Commands

```bash
railway logs          # View logs
railway status        # Check status
railway open          # Open dashboard
railway variables     # List env vars
railway up            # Redeploy
```

---

## 🆘 Troubleshooting

### Deployment Failed
```bash
railway logs    # Check errors
railway up      # Try again
```

### No Domain
```bash
railway domain create
```

### Variables Not Set
```bash
railway variables
railway variables set KEY="value"
```

---

## 💰 Pricing

**Free Tier:**
- ✅ 500 execution hours/month
- ✅ $5 free credits/month
- ✅ Auto-sleep after 15min inactivity
- ✅ Auto-wake on request
- ✅ Perfect for development & testing

**Paid Plans:** Start at $5/month for unlimited hours

---

## 📚 Documentation

- **Quick Start:** [`DEPLOY_QUICK.md`](DEPLOY_QUICK.md)
- **Detailed Guide:** [`RAILWAY_DEPLOY_STEPS.md`](RAILWAY_DEPLOY_STEPS.md)
- **Full Deployment Options:** [`DEPLOY.md`](DEPLOY.md)
- **Project Documentation:** [`README.md`](README.md)

---

## 🎉 Ready to Deploy?

```bash
./deploy_railway.sh
```

Or read the detailed guide:

```bash
cat RAILWAY_DEPLOY_STEPS.md
```

---

## 📞 Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Project Issues:** Check logs with `railway logs`

---

**Status:** ✅ Ready for Production  
**Deployment Time:** ~3-5 minutes  
**Difficulty:** ⭐ Easy (automated script)

🚀 **Let's deploy your AI system to production!**
