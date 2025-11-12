# 🚀 Railway Deployment Guide - Phase 1 Fixes

**Status**: ✅ Code pushed to GitHub, ready for deployment
**Git Tag**: `v2.0-phase1-critical-fixes`
**Commit**: `c5d4d8c`

---

## ✅ Pre-Deployment Checklist

**Completed**:
- [x] All P1 critical fixes implemented
- [x] 19/19 tests passing
- [x] Code committed and pushed to GitHub
- [x] Railway volume configuration in place
- [x] Backup script created and tested
- [x] Documentation complete
- [x] Git tag created: `v2.0-phase1-critical-fixes`

**Ready for Deployment**: ✅ YES

---

## 🔧 Deployment Steps (Manual via Railway Dashboard)

Since Railway CLI requires interactive mode, follow these steps via the Railway dashboard:

### Step 1: Access Railway Dashboard

1. Go to: https://railway.app
2. Login as: jamsmac@gmail.com
3. Select Project: **AIAssistant**
4. Select Environment: **production** (or create staging environment)

### Step 2: Configure Volume (CRITICAL - First Time Only)

**IMPORTANT**: This must be done before deploying to prevent data loss

1. Click on your service
2. Go to **Settings** → **Volumes**
3. Click **+ New Volume**
4. Configure:
   - **Mount Path**: `/app/data`
   - **Volume Name**: `data-volume`
   - **Size**: 1 GB (can increase later)
5. Click **Create Volume**

**Verification**: You should see the volume listed with status "Active"

### Step 3: Verify Environment Variables

Go to **Variables** tab and verify these are set:

**Required**:
```bash
SECRET_KEY=<your-secret-key>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
DATABASE_URL=<if-using-postgres>
```

**Optional (for backups)**:
```bash
AWS_ACCESS_KEY_ID=<for-s3-backups>
AWS_SECRET_ACCESS_KEY=<for-s3-backups>
S3_BUCKET=<backup-bucket-name>
BACKUP_WEBHOOK_URL=<notification-webhook>
```

### Step 4: Deploy

**Option A: Auto-Deploy (Recommended)**

Railway will automatically deploy when you push to GitHub:

```bash
# Already done ✓
git push origin main --tags
```

1. Go to **Deployments** tab
2. You should see a new deployment starting automatically
3. Status will show: Building → Deploying → Active

**Option B: Manual Deploy via Railway CLI**

If you prefer CLI and can access a terminal:

```bash
# Link to project (interactive)
railway link

# Select environment
railway environment

# Deploy specific service
railway up --service <service-name>
```

**Option C: Manual Trigger**

1. Go to **Deployments** tab
2. Click **Deploy** button
3. Select branch: `main`
4. Click **Deploy Now**

### Step 5: Monitor Deployment

Watch the deployment logs in real-time:

1. Click on the running deployment
2. View **Logs** tab
3. Look for key success messages:

```
✅ "SECRET_KEY validated successfully"
✅ "Workflow scheduler started successfully with X jobs"
✅ "Cache cleanup scheduler started"
✅ "API startup complete"
```

**Expected startup time**: 30-60 seconds

### Step 6: Verify Deployment Health

Once deployment shows **Active**:

1. **Health Check**
   - Railway should show green checkmark if healthcheck passes
   - Or visit: `https://your-app.railway.app/api/health`
   - Expected response: `{"status": "healthy", ...}`

2. **Check Scheduler**
   ```bash
   # Via Railway CLI
   railway logs | grep "scheduler"

   # Should see:
   # "Workflow scheduler started successfully with X jobs"
   ```

3. **Verify Volume Mounted**
   ```bash
   railway run ls -la /app/data

   # Should show:
   # drwxr-xr-x data
   # -rw-r--r-- history.db
   # -rw-r--r-- autopilot_cache.db
   ```

### Step 7: Test Critical Features

**A. Test Scheduler Endpoints**

```bash
# Get scheduled jobs (will need auth token)
curl https://your-app.railway.app/api/workflows/schedule/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: {"jobs": [...], "total_count": X}
```

**B. Test OAuth Availability**

```bash
curl https://your-app.railway.app/api/integrations/
# Should list available integrations including Gmail, Google Drive
```

**C. Create Test Workflow with Schedule**

1. Login to web UI: https://your-app.railway.app
2. Go to **Workflows**
3. Create new workflow with schedule trigger:
   ```json
   {
     "name": "Test Scheduled Workflow",
     "trigger": {
       "type": "schedule",
       "config": {
         "schedule": {
           "type": "interval",
           "interval": {"minutes": 5}
         }
       }
     },
     "actions": [
       {
         "type": "send_notification",
         "config": {"message": "Scheduler working!"}
       }
     ]
   }
   ```
4. Save and wait 5 minutes
5. Check execution logs - should see automatic execution

---

## 🧪 Post-Deployment Verification

### Critical Tests (Do these immediately)

1. **Data Persistence Test**
   ```bash
   # Create test data
   railway run sqlite3 /app/data/history.db \
     "INSERT INTO users (email, password_hash) VALUES ('test@deploy.com', 'hash123');"

   # Trigger redeploy
   railway up --detach

   # After redeploy, verify data still exists
   railway run sqlite3 /app/data/history.db \
     "SELECT * FROM users WHERE email='test@deploy.com';"

   # ✅ Should return the test user
   ```

2. **Scheduler Running Test**
   ```bash
   # Check scheduler status in logs
   railway logs --tail 100 | grep -i scheduler

   # Should see:
   # ✅ "Workflow scheduler started successfully"
   # ✅ No errors about scheduler failing
   ```

3. **Backup Script Test**
   ```bash
   # Run backup manually
   railway run bash scripts/backup_db.sh

   # Check backup created
   railway run ls -lh /app/data/backups/

   # Should see timestamped backup files
   ```

4. **API Endpoints Test**
   ```bash
   # Test health
   curl https://your-app.railway.app/api/health

   # Test scheduler endpoints (need auth)
   curl https://your-app.railway.app/api/workflows/schedule/jobs \
     -H "Cookie: auth_token=YOUR_TOKEN"
   ```

### 48-Hour Soak Test Checklist

Monitor these over 48 hours:

**Day 1 (Nov 10)**:
- [ ] Application stays up (no crashes)
- [ ] Scheduler executes workflows on time
- [ ] Logs show no errors
- [ ] Memory usage stable
- [ ] CPU usage normal
- [ ] Database file size growing normally
- [ ] No volume errors

**Day 2 (Nov 11)**:
- [ ] Scheduled workflows still running
- [ ] Data still persists
- [ ] Performance still good
- [ ] No memory leaks
- [ ] Backups running (if scheduled)

**Day 3 (Nov 12)**:
- [ ] All systems stable
- [ ] Ready for production traffic
- [ ] Create deployment report

---

## 📊 Monitoring During Soak Test

### Railway Dashboard Metrics

Monitor these in Railway dashboard:

1. **Deployments**
   - Status: Active ✓
   - Uptime: Should be 100%
   - Restarts: Should be 0

2. **Metrics**
   - CPU: Should be < 50% average
   - Memory: Should be stable (not climbing)
   - Network: Responding to requests

3. **Logs**
   - No ERROR level messages
   - INFO logs show scheduler running
   - No exceptions or tracebacks

### Log Patterns to Watch For

**Good Signs** ✅:
```
INFO: Workflow scheduler started successfully with X jobs
INFO: Cache cleanup scheduler started
INFO: API startup complete
INFO: Executing scheduled workflow X
```

**Warning Signs** ⚠️:
```
WARNING: Workflow scheduler failed to start
ERROR: Database connection failed
ERROR: Volume not mounted
ERROR: Out of memory
```

**Critical Issues** ❌:
```
CRITICAL: Database file corrupted
CRITICAL: Cannot write to /app/data
ERROR: Scheduler crashed
```

### What to Do If Issues Found

**Minor Issues** (warnings):
- Document in soak test report
- Fix in next deployment
- Continue monitoring

**Major Issues** (errors):
- Investigate immediately
- Check logs: `railway logs --tail 500`
- Rollback if necessary: Deploy previous commit

**Critical Issues**:
- Rollback immediately
- Restore from backup if data affected
- Do NOT deploy to production
- Fix issues and re-test

---

## 🔄 Testing Data Persistence (Critical!)

This is the most important test - verify Railway volume works:

### Test Procedure

1. **Baseline - Record Current State**
   ```bash
   railway run sqlite3 /app/data/history.db \
     "SELECT COUNT(*) FROM users;" > before.txt
   ```

2. **Trigger Redeploy**
   ```bash
   # Make trivial change (e.g., add comment to server.py)
   echo "# Redeploy test" >> api/server.py
   git add api/server.py
   git commit -m "test: Verify data persistence on redeploy"
   git push origin main
   ```

3. **Wait for Deployment to Complete**
   - Watch Railway dashboard
   - Wait for status: Active

4. **Verify Data Still Exists**
   ```bash
   railway run sqlite3 /app/data/history.db \
     "SELECT COUNT(*) FROM users;" > after.txt

   diff before.txt after.txt
   # Should show NO DIFFERENCE
   ```

5. **Verify Database Integrity**
   ```bash
   railway run sqlite3 /app/data/history.db "PRAGMA integrity_check;"
   # Should return: ok
   ```

**Expected Result**: ✅ User count identical before/after redeploy

**If Data Lost**: ❌ Volume not configured correctly - DO NOT PROCEED

---

## 📋 Deployment Success Criteria

Mark deployment as **successful** only if ALL these are true:

- [ ] Deployment status: Active
- [ ] Health check: Passing
- [ ] Scheduler: Started successfully
- [ ] Volume: Mounted at /app/data
- [ ] Database files: Present and accessible
- [ ] Data persistence: Verified across redeploy
- [ ] Backup script: Executable and working
- [ ] API endpoints: Responding correctly
- [ ] Logs: No critical errors
- [ ] Performance: CPU < 50%, Memory stable

**If any fail**: Investigate and fix before proceeding to production

---

## 🎯 Next Steps After Successful Deployment

### If Soak Test Passes (48 hours, no issues)

**Day 3 (Nov 12-13)**:

1. **Create Deployment Report**
   - Document any issues found
   - Note performance metrics
   - List any optimizations needed

2. **Schedule Production Deployment**
   - Announce maintenance window
   - Backup production database
   - Deploy to production
   - Monitor closely for 24 hours

3. **Phase 2 (Optional)**
   - Implement session invalidation (2h)
   - Add input length limits (1h)
   - Deploy Phase 2 fixes

### If Issues Found During Soak Test

1. **Document Issues**
   - Create GitHub issues for each problem
   - Classify by severity (P0/P1/P2)

2. **Fix Critical Issues**
   - Address P0 issues immediately
   - Re-test after fixes
   - Restart 48-hour soak test

3. **Hold Production Deployment**
   - Do NOT deploy to production with known issues
   - Fix all P0/P1 issues first
   - Re-run full test suite

---

## 🆘 Rollback Procedure

If deployment has critical issues:

### Quick Rollback (via Railway Dashboard)

1. Go to **Deployments** tab
2. Find last known good deployment
3. Click **•••** (three dots) → **Redeploy**
4. Confirm rollback

### Via Railway CLI

```bash
# List recent deployments
railway deployments

# Rollback to specific deployment
railway rollback <deployment-id>
```

### Data Recovery (if data corrupted)

```bash
# List backups
railway run ls -lh /app/data/backups/

# Restore from backup
railway run cp /app/data/backups/history_YYYYMMDD_HHMMSS.db \
  /app/data/history.db

# Verify integrity
railway run sqlite3 /app/data/history.db "PRAGMA integrity_check;"
```

---

## 📞 Emergency Contacts

**If critical issues during deployment**:

- **Railway Support**: support@railway.app
- **Project Owner**: jamsmac@gmail.com
- **GitHub Issues**: https://github.com/jamsmac/AIAssistant/issues

**Before contacting support, collect**:
- Deployment logs (last 500 lines)
- Error messages
- Steps to reproduce
- Expected vs actual behavior

---

## 📈 Expected Deployment Timeline

**Total Time**: 48-72 hours

| Day | Activity | Duration |
|-----|----------|----------|
| **Day 1 (Nov 10)** | Deploy to staging | 30 min |
| | Verify deployment health | 1 hour |
| | Monitor for issues | Rest of day |
| **Day 2 (Nov 11)** | Continue monitoring | All day |
| | Test scheduled workflows | 2 hours |
| | Run backup script | 30 min |
| **Day 3 (Nov 12)** | Final verification | 2 hours |
| | Create deployment report | 1 hour |
| | Go/No-Go decision | 1 hour |
| **Day 4 (Nov 13)** | Deploy to production | 1 hour |
| | Post-prod monitoring | Rest of day |

---

## ✅ Deployment Checklist

Use this checklist during deployment:

### Pre-Deployment
- [x] Code pushed to GitHub
- [x] Git tag created
- [x] Tests passing locally
- [ ] Railway volume configured
- [ ] Environment variables set
- [ ] Backup script tested

### During Deployment
- [ ] Deployment triggered
- [ ] Build successful
- [ ] Health check passing
- [ ] Logs show no errors
- [ ] Scheduler started
- [ ] Volume mounted

### Post-Deployment
- [ ] API endpoints responding
- [ ] Test scheduled workflow created
- [ ] Data persistence verified
- [ ] Backup script executed
- [ ] Performance metrics normal
- [ ] No errors in logs

### Soak Test (48h)
- [ ] Day 1: Stable, no crashes
- [ ] Day 1: Scheduler working
- [ ] Day 2: Still stable
- [ ] Day 2: Performance good
- [ ] Day 3: Ready for production

---

## 🎉 Success!

When deployment is successful:

1. ✅ Mark this as staging deployment complete
2. ✅ Begin 48-hour soak test monitoring
3. ✅ Document any observations
4. ✅ Schedule production deployment

**Status**: Ready for staging deployment via Railway dashboard

---

**Created**: November 9, 2025
**Deployment Tag**: v2.0-phase1-critical-fixes
**Commit**: c5d4d8c

**Next Action**: Deploy via Railway dashboard following steps above

---

END OF DEPLOYMENT GUIDE
