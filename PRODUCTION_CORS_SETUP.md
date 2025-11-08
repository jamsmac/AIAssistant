# Production CORS Configuration Guide

**Status:** READY FOR DEPLOYMENT
**Date:** 2025-11-08
**Priority:** HIGH

---

## Overview

This guide explains how to configure CORS (Cross-Origin Resource Sharing) for production deployment. The CORS configuration has been fixed to prevent security vulnerabilities.

### What Was Fixed

**Before (INSECURE):**
```python
allowed_origins = ["*"]  # Allows ALL domains
allow_credentials = True  # INVALID COMBINATION!
```

**After (SECURE):**
```python
# Development: Specific localhost origins
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    # ... etc
]

# Production: Read from CORS_ORIGINS environment variable
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
```

---

## Quick Setup

### Method 1: Using the Setup Script (Recommended)

```bash
# Run the automated setup script
bash scripts/setup_production_cors.sh

# Follow the prompts to enter your frontend URL
# Example: https://your-app.vercel.app
```

### Method 2: Manual Railway Setup

#### Via Railway CLI:

```bash
# Login to Railway
railway login

# Set CORS origins
railway variables set CORS_ORIGINS="https://your-app.vercel.app,https://www.your-app.vercel.app"

# Set frontend URL (first URL from CORS_ORIGINS)
railway variables set FRONTEND_URL="https://your-app.vercel.app"

# Ensure environment is set to production
railway variables set ENVIRONMENT="production"

# Redeploy
railway up --detach
```

#### Via Railway Dashboard:

1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables" tab
4. Add these variables:
   - `CORS_ORIGINS` = `https://your-app.vercel.app,https://www.your-app.vercel.app`
   - `FRONTEND_URL` = `https://your-app.vercel.app`
   - `ENVIRONMENT` = `production`
5. Click "Deployments" → "Redeploy"

---

## Configuration Details

### Environment Variables

| Variable | Required | Format | Example |
|----------|----------|--------|---------|
| `CORS_ORIGINS` | **YES** | Comma-separated URLs | `https://app.com,https://www.app.com` |
| `FRONTEND_URL` | Recommended | Single URL | `https://app.com` |
| `ENVIRONMENT` | **YES** | `production` or `development` | `production` |

### CORS_ORIGINS Format

**Single Domain:**
```bash
CORS_ORIGINS="https://your-app.vercel.app"
```

**Multiple Domains:**
```bash
CORS_ORIGINS="https://your-app.vercel.app,https://www.your-app.vercel.app,https://custom-domain.com"
```

**Important:**
- ✅ Include `https://` prefix
- ✅ No trailing slashes
- ✅ Separate multiple URLs with commas (no spaces)
- ❌ Do NOT use `http://` in production (use HTTPS)
- ❌ Do NOT include paths (e.g., `/api`)

---

## Finding Your Frontend URL

### If Using Vercel:

1. Go to https://vercel.com/dashboard
2. Click on your project
3. Look for "Domains" section
4. Copy the production URL (usually `your-app.vercel.app`)

### If Using Netlify:

1. Go to https://app.netlify.com
2. Click on your site
3. Look for "Site settings" → "Domain management"
4. Copy your primary domain

### If Using Custom Domain:

Use your custom domain (e.g., `https://yourdomain.com`)

**Remember to include both:**
- `https://yourdomain.com`
- `https://www.yourdomain.com`

---

## Testing CORS Configuration

### 1. Test with curl

```bash
# Replace with your actual URLs
BACKEND_URL="https://your-app.railway.app"
FRONTEND_URL="https://your-frontend.vercel.app"

# Test preflight request
curl -X OPTIONS "$BACKEND_URL/api/auth/me" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  -v
```

**Expected Response Headers:**
```
Access-Control-Allow-Origin: https://your-frontend.vercel.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-CSRF-Token
```

### 2. Test with Browser Console

```javascript
// Open your frontend in browser
// Open Developer Console (F12)
// Run this:

fetch('https://your-backend.railway.app/api/health', {
  method: 'GET',
  credentials: 'include'
})
.then(r => r.json())
.then(data => console.log('✓ CORS working:', data))
.catch(err => console.error('✗ CORS error:', err));
```

**Expected:** Should see `✓ CORS working: {status: "healthy"}`

---

## Troubleshooting

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause:** CORS_ORIGINS not set or incorrect

**Solution:**
```bash
# Check current setting
railway variables | grep CORS_ORIGINS

# Set correct value
railway variables set CORS_ORIGINS="https://your-actual-frontend.vercel.app"

# Redeploy
railway up --detach
```

### Error: "Origin not allowed by Access-Control-Allow-Origin"

**Cause:** Frontend URL not in CORS_ORIGINS list

**Solution:**
```bash
# Get current value
railway variables get CORS_ORIGINS

# Add your frontend URL
railway variables set CORS_ORIGINS="https://existing.com,https://your-new-frontend.com"
```

### Error: "Wildcard '*' cannot be used with credentials"

**Cause:** Old configuration with `["*"]` still deployed

**Solution:**
```bash
# Verify CORS_ORIGINS is set
railway variables get CORS_ORIGINS

# If not set, set it
railway variables set CORS_ORIGINS="https://your-frontend.vercel.app"

# Force redeploy
railway up --detach
```

### CORS works locally but not in production

**Checklist:**
- [ ] `ENVIRONMENT=production` is set in Railway
- [ ] `CORS_ORIGINS` includes your production frontend URL
- [ ] Using HTTPS (not HTTP) for production URLs
- [ ] No trailing slashes in URLs
- [ ] Railway service has been redeployed after changes

---

## Development vs Production

### Development (Local)

**Allowed Origins:**
```python
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000"
]
```

**How to use:**
- No environment variables needed
- Just run the application locally
- CORS will automatically allow localhost origins

### Production

**Allowed Origins:**
- Read from `CORS_ORIGINS` environment variable
- Fallback to `FRONTEND_URL` if CORS_ORIGINS not set
- Default fallback: `https://aiassistant.vercel.app`

**Required:**
- `ENVIRONMENT=production`
- `CORS_ORIGINS=https://your-app.vercel.app`

---

## Security Best Practices

### ✅ DO:
- Use specific domain names
- Include both `https://domain.com` and `https://www.domain.com`
- Use HTTPS in production
- Keep CORS_ORIGINS updated when adding new frontends
- Test CORS after deployment

### ❌ DON'T:
- Use wildcard `["*"]` with `allow_credentials=True`
- Include HTTP URLs in production
- Use trailing slashes
- Include paths in CORS_ORIGINS
- Forget to redeploy after changing CORS_ORIGINS

---

## Multiple Environments

If you have multiple environments (staging, production, etc.), set different CORS_ORIGINS for each:

### Production:
```bash
CORS_ORIGINS="https://app.yourcompany.com,https://www.yourcompany.com"
```

### Staging:
```bash
CORS_ORIGINS="https://staging.yourcompany.com,https://staging-www.yourcompany.com"
```

### Development:
No need to set CORS_ORIGINS - automatically uses localhost

---

## Advanced: Custom CORS Configuration

If you need to customize CORS further, edit `api/middleware/cors.py`:

```python
# api/middleware/cors.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

---

## Verification Checklist

After setup, verify:

- [ ] `CORS_ORIGINS` is set in Railway
- [ ] `ENVIRONMENT=production` is set in Railway
- [ ] Railway service has been redeployed
- [ ] `curl` test passes (see Testing section)
- [ ] Browser console test passes
- [ ] No CORS errors in browser developer console
- [ ] Frontend can successfully call backend APIs
- [ ] Authenticated requests work (with credentials)

---

## Quick Reference

### Set CORS_ORIGINS:
```bash
railway variables set CORS_ORIGINS="https://your-frontend.vercel.app"
```

### Get Current Value:
```bash
railway variables get CORS_ORIGINS
```

### Test CORS:
```bash
curl -I https://your-backend.railway.app/api/health \
  -H "Origin: https://your-frontend.vercel.app"
```

### Redeploy:
```bash
railway up --detach
```

---

## Support

If you continue to have CORS issues:

1. Check Railway logs:
   ```bash
   railway logs
   ```

2. Verify environment variables:
   ```bash
   railway variables | grep -E "CORS|ENVIRONMENT|FRONTEND"
   ```

3. Test with verbose curl:
   ```bash
   curl -v -X OPTIONS https://your-backend.railway.app/api/health \
     -H "Origin: https://your-frontend.vercel.app" \
     -H "Access-Control-Request-Method: GET"
   ```

---

**Created:** 2025-11-08
**Updated:** 2025-11-08
**Status:** READY FOR PRODUCTION
