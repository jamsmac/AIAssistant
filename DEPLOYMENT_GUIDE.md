# 🚀 AI Assistant - Deployment Guide

Complete guide for deploying AI Assistant to production.

---

## 📋 **Prerequisites**

### Required Accounts
- [x] Railway account (backend hosting)
- [x] Vercel account (frontend hosting)
- [x] GitHub repository

### Required API Keys
- [x] OpenAI API Key
- [x] Anthropic API Key
- [x] Google Gemini API Key (optional)
- [x] xAI Grok API Key (optional)

---

## 🔧 **Backend Deployment (Railway)**

### 1. Prepare Backend

```bash
# Navigate to project root
cd ~/autopilot-core

# Ensure all dependencies are listed
cat requirements.txt

# Test backend locally
python api/server.py
```

### 2. Deploy to Railway

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project (or create new)
railway link

# Add environment variables
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
railway variables set OPENAI_API_KEY=your-openai-key
railway variables set ANTHROPIC_API_KEY=your-anthropic-key
railway variables set GEMINI_API_KEY=your-gemini-key
railway variables set DATABASE_URL=./data/autopilot.db
railway variables set ENVIRONMENT=production

# Deploy
railway up

# Get deployment URL
railway status
```

### 3. Verify Backend

```bash
# Test health endpoint
curl https://your-railway-url.railway.app/api/health

# Should return: {"status":"healthy"}
```

---

## 🎨 **Frontend Deployment (Vercel)**

### 1. Prepare Frontend

```bash
# Navigate to frontend
cd web-ui

# Update API URL in .env.local
echo "NEXT_PUBLIC_API_URL=https://your-railway-url.railway.app" > .env.local

# Test build
npm run build

# Test locally
npm run dev
```

### 2. Deploy to Vercel

#### Option A: Via Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

#### Option B: Via GitHub Integration

1. Push code to GitHub
2. Go to https://vercel.com/new
3. Import your repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web-ui`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

5. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: Your Railway backend URL

6. Click "Deploy"

### 3. Verify Frontend

```bash
# Open in browser
open https://your-app.vercel.app

# Test:
# - Login page loads
# - Can register/login
# - Projects page works
# - API calls succeed
```

---

## 🔐 **Environment Variables**

### Backend (Railway)

```env
# Required
SECRET_KEY=<generated-secret>
DATABASE_URL=./data/autopilot.db
ENVIRONMENT=production

# API Keys (at least one required)
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
GEMINI_API_KEY=<your-key>
GROK_API_KEY=<your-key>

# Optional
CORS_ORIGINS=https://your-app.vercel.app
JWT_EXPIRATION_HOURS=24
```

### Frontend (Vercel)

```env
NEXT_PUBLIC_API_URL=https://your-railway-url.railway.app
```

---

## 📊 **Post-Deployment Checklist**

### Backend Health Check
- [ ] `/api/health` returns 200
- [ ] `/api/models` lists available models
- [ ] Rate limiting works (test with 11+ requests)
- [ ] Authentication works (register/login)

### Frontend Verification
- [ ] Login page accessible
- [ ] Registration works
- [ ] Dashboard loads
- [ ] Projects CRUD works
- [ ] Database CRUD works
- [ ] Chat interface works
- [ ] Toast notifications appear
- [ ] Error handling works

### Security Check
- [ ] HTTPS enabled
- [ ] API keys not exposed
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] JWT tokens working

---

## 🐛 **Troubleshooting**

### Backend Issues

**Problem**: `500 Internal Server Error`
```bash
# Check Railway logs
railway logs

# Common fixes:
# 1. Missing environment variable
# 2. Database path incorrect
# 3. API key invalid
```

**Problem**: CORS errors
```bash
# Update CORS_ORIGINS
railway variables set CORS_ORIGINS="https://your-app.vercel.app"
```

### Frontend Issues

**Problem**: `Failed to fetch`
```bash
# Check API URL
cat web-ui/.env.local

# Should be: NEXT_PUBLIC_API_URL=https://your-railway-url.railway.app
```

**Problem**: Build fails
```bash
# Check for TypeScript errors
cd web-ui
npm run build

# Fix any errors and redeploy
```

---

## 🔄 **Continuous Deployment**

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          cd web-ui
          vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
```

---

## 📈 **Monitoring**

### Railway Monitoring
- Dashboard: https://railway.app/dashboard
- Logs: `railway logs`
- Metrics: CPU, Memory, Network usage

### Vercel Monitoring
- Dashboard: https://vercel.com/dashboard
- Analytics: Automatic
- Logs: Function logs in dashboard

### Recommended Add-ons
- **Sentry**: Error tracking
- **LogRocket**: Session replay
- **Datadog**: Full observability

---

## 💰 **Cost Estimation**

### Monthly Costs

**Railway (Backend)**
- Hobby: $5/month (500 MB RAM, $0.000231/min)
- Estimated: $10-20/month

**Vercel (Frontend)**
- Hobby: Free (100 GB bandwidth)
- Pro: $20/month (1 TB bandwidth)

**API Costs**
- OpenAI: Pay per use (~$10-50/month)
- Anthropic: Pay per use (~$10-50/month)

**Total Estimated**: $30-120/month

---

## 🎯 **Production Optimization**

### Backend
```python
# Enable production mode
ENVIRONMENT=production

# Optimize database
# Use PostgreSQL instead of SQLite for production
DATABASE_URL=postgresql://...

# Add Redis for caching
REDIS_URL=redis://...
```

### Frontend
```bash
# Enable production optimizations in next.config.ts
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,
}
```

---

## 📚 **Additional Resources**

- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## ✅ **Success!**

Your AI Assistant is now live! 🎉

**Backend**: https://your-railway-url.railway.app
**Frontend**: https://your-app.vercel.app

Share it with your team and start building!
