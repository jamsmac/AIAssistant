# Password Rotation Guide
**CRITICAL: Complete within 24 hours**

Date: 2025-11-08
Reason: Weak passwords exposed in `.env.backup` Git history

---

## Overview

The following passwords were exposed in Git history and MUST be rotated:
- `POSTGRES_PASSWORD=autopilot`
- `REDIS_PASSWORD=autopilot_redis_2024`
- `MINIO_ROOT_PASSWORD=autopilot_minio_2024`
- `SYSTEM_PASSWORD=autopilot_system_2024`

---

## Step 1: Generate New Secure Passwords

Run these commands to generate cryptographically secure passwords:

```bash
# Generate all new passwords at once
echo "# New Secure Passwords - $(date)"
echo "# Save these in a secure password manager!"
echo ""
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)"
echo "SYSTEM_PASSWORD=$(openssl rand -base64 32)"
echo "SECRET_KEY=$(openssl rand -base64 48)"
echo "CSRF_SECRET=$(openssl rand -base64 32)"
```

**SAVE THE OUTPUT** in a secure password manager (1Password, Bitwarden, etc.)

---

## Step 2: Update Local Environment

### Option A: Update `.env.backup` (if you need to keep it)

```bash
# Create a new .env.backup with strong passwords
cp .env.backup .env.backup.old

# Edit .env.backup and replace passwords with generated ones
nano .env.backup  # or your preferred editor
```

### Option B: Delete `.env.backup` (recommended)

```bash
# If you don't need this file, delete it
rm .env.backup

# Or archive it
mv .env.backup ~/.env.backup.archive.$(date +%Y%m%d)
```

---

## Step 3: Update Production Environment (Railway)

**IMPORTANT:** Update these in Railway Dashboard or CLI:

### Via Railway CLI:

```bash
# Check Railway is logged in
railway login

# Check current project
railway status

# Update passwords one by one
railway variables set POSTGRES_PASSWORD="<paste-generated-password-here>"
railway variables set REDIS_PASSWORD="<paste-generated-password-here>"
railway variables set MINIO_ROOT_PASSWORD="<paste-generated-password-here>"
railway variables set SYSTEM_PASSWORD="<paste-generated-password-here>"

# Also set these if not already configured
railway variables set SECRET_KEY="<paste-generated-secret-here>"
railway variables set CSRF_SECRET="<paste-generated-secret-here>"
```

### Via Railway Dashboard:

1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables" tab
4. Update each password:
   - `POSTGRES_PASSWORD`
   - `REDIS_PASSWORD`
   - `MINIO_ROOT_PASSWORD`
   - `SYSTEM_PASSWORD`
   - `SECRET_KEY`
   - `CSRF_SECRET`

---

## Step 4: Update CORS Configuration

Set the CORS_ORIGINS variable for your production frontend:

```bash
# Get your Vercel/frontend URL first
# Example: https://aiassistant-omega.vercel.app

railway variables set CORS_ORIGINS="https://your-frontend.vercel.app,https://www.your-frontend.vercel.app"
```

Or in Railway Dashboard:
- Add variable: `CORS_ORIGINS`
- Value: `https://your-frontend.vercel.app`

---

## Step 5: Restart Services

After updating passwords, restart all services:

### Railway:
```bash
railway up --detach
```

Or use the Dashboard:
1. Go to your project
2. Click "Deployments"
3. Click "Redeploy"

### Local Development:
```bash
# Stop all containers
docker-compose down

# Remove volumes (optional, for clean restart)
docker-compose down -v

# Start with new passwords
docker-compose up -d
```

---

## Step 6: Verify Changes

### Check Railway Variables:
```bash
railway variables | grep -E "PASSWORD|SECRET|CORS"
```

**Expected output:**
```
POSTGRES_PASSWORD: ••••••••••••••••••••••••••••••••
REDIS_PASSWORD: ••••••••••••••••••••••••••••••••
MINIO_ROOT_PASSWORD: ••••••••••••••••••••••••••••••••
SYSTEM_PASSWORD: ••••••••••••••••••••••••••••••••
SECRET_KEY: ••••••••••••••••••••••••••••••••••••••••••
CSRF_SECRET: ••••••••••••••••••••••••••••••••
CORS_ORIGINS: https://your-frontend.vercel.app
```

### Test Database Connection:
```bash
# Should connect successfully with new password
psql "postgresql://autopilot:<new-password>@<host>:5432/autopilot"
```

### Test Application:
```bash
# Check health endpoint
curl https://your-railway-app.railway.app/api/health

# Expected: {"status": "healthy"}
```

---

## Step 7: Clean Up Git History (Advanced - Optional)

**WARNING:** This rewrites Git history. Coordinate with team first!

### Option A: Remove .env.backup from entire history

```bash
# Install git-filter-repo (recommended tool)
pip install git-filter-repo

# Remove file from all commits
git filter-repo --path .env.backup --invert-paths

# Force push (only if you're sure!)
git push origin --force --all
```

### Option B: Use BFG Repo-Cleaner

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove file from history
java -jar bfg-1.14.0.jar --delete-files .env.backup

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

**Note:** Git history cleanup is NOT required for security if:
1. Repository is private
2. Passwords have been rotated
3. File is removed from latest commits

---

## Checklist

### Immediate (Today):
- [ ] Generate new secure passwords (Step 1)
- [ ] Save passwords in password manager
- [ ] Update Railway environment variables (Step 3)
- [ ] Set CORS_ORIGINS in Railway (Step 4)
- [ ] Restart Railway services (Step 5)
- [ ] Test application health (Step 6)
- [ ] Delete or secure local `.env.backup` (Step 2)

### Short-term (This Week):
- [ ] Update local `.env` with new passwords
- [ ] Test all services (Postgres, Redis, MinIO)
- [ ] Verify Stripe integration still works
- [ ] Check application logs for auth errors
- [ ] Document password rotation in team wiki

### Optional (If Repository Was Public):
- [ ] Review Git history cleanup necessity
- [ ] Coordinate with team before rewriting history
- [ ] Execute Git history cleanup (Step 7)
- [ ] Notify team of force push

---

## Troubleshooting

### Issue: Railway deployment fails after password change

**Solution:**
```bash
# Check logs
railway logs

# Common issues:
# 1. Typo in password - double-check copy/paste
# 2. Special characters in password - use base64 passwords
# 3. Service not restarted - force redeploy
```

### Issue: Database connection refused

**Symptoms:** `psql: connection refused` or `could not connect to server`

**Solutions:**
1. Wait 2-3 minutes for database to restart
2. Check password was updated correctly
3. Verify database service is running in Railway
4. Check database URL format

### Issue: CORS errors in browser

**Symptoms:** `Access-Control-Allow-Origin` errors

**Solutions:**
1. Verify `CORS_ORIGINS` is set correctly
2. Include both `https://domain.com` and `https://www.domain.com`
3. Restart Railway service after changing CORS_ORIGINS
4. Check browser console for exact error

### Issue: Stripe webhooks failing

**Solution:**
```bash
# Verify Stripe webhook secret is still set
railway variables | grep STRIPE_WEBHOOK_SECRET

# If missing, get from Stripe Dashboard and set
railway variables set STRIPE_WEBHOOK_SECRET="whsec_..."
```

---

## Security Best Practices Going Forward

1. **Never commit `.env` files to Git**
   - Already in `.gitignore` ✅
   - Use `.env.example` for documentation

2. **Use strong, unique passwords**
   - Minimum 32 characters
   - Generated cryptographically (not predictable patterns)
   - Different for each service

3. **Rotate secrets regularly**
   - Every 90 days for critical systems
   - Immediately if suspected compromise
   - After team member departure

4. **Use secret management tools**
   - Railway Variables (for Railway)
   - Vercel Environment Variables (for Vercel)
   - Consider HashiCorp Vault for advanced needs

5. **Monitor for exposed secrets**
   - Enable GitHub secret scanning (if using GitHub)
   - Use pre-commit hooks (detect-secrets)
   - Regular security audits

6. **Document secret locations**
   - Maintain secure inventory of where secrets are stored
   - Use password manager for team sharing
   - Keep backup encryption keys separate

---

## Emergency Contact

If you suspect active exploitation:
1. **Immediately** rotate all passwords
2. Check Railway logs for suspicious activity
3. Review database access logs
4. Check for unauthorized API requests
5. Contact Railway support if needed

---

## Completion Verification

Once complete, verify:

```bash
# 1. Check all passwords are set
railway variables | grep -E "PASSWORD|SECRET" | wc -l
# Should show at least 6 variables

# 2. Test application
curl https://your-app.railway.app/api/health
# Should return: {"status": "healthy"}

# 3. Check CORS
curl -I https://your-app.railway.app/api/auth/me \
  -H "Origin: https://your-frontend.vercel.app"
# Should include: Access-Control-Allow-Origin header

# 4. Verify .env.backup not in Git
git ls-files | grep .env.backup
# Should return nothing
```

---

**Created:** 2025-11-08
**Priority:** CRITICAL
**Deadline:** Within 24 hours
**Status:** PENDING
