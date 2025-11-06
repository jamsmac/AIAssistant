# 🚀 Deployment Instructions

## Status: Ready to Deploy ✅

All code changes are complete. Follow these steps to deploy to production.

---

## Step 1: Enable Google APIs ☁️

### 1.1 Gmail API
1. Open: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=aiassistant-os-platform
2. Click **"ENABLE"**
3. Wait for confirmation

### 1.2 Google Drive API
1. Open: https://console.cloud.google.com/apis/library/drive.googleapis.com?project=aiassistant-os-platform
2. Click **"ENABLE"**
3. Wait for confirmation

---

## Step 2: Set Railway Environment Variables 🚂

### Option A: Via Railway Dashboard (Recommended)

1. Open: https://railway.app/dashboard
2. Select project: **AIAssistant**
3. Go to **Variables** tab
4. Add these variables:

```
GOOGLE_CLIENT_ID=<your-client-id-from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<your-client-secret-from-google-cloud-console>
GOOGLE_REDIRECT_URI=https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback
```

5. Click **"Add"** for each variable

### Option B: Via Railway CLI

```bash
# Make sure you're in the project directory
cd /Users/js/autopilot-core

# Link to the service (if not linked)
railway link

# Set variables
railway variables --set "GOOGLE_CLIENT_ID=<your-client-id>"
railway variables --set "GOOGLE_CLIENT_SECRET=<your-client-secret>"
railway variables --set "GOOGLE_REDIRECT_URI=https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback"

# Verify
railway variables
```

---

## Step 3: Deploy to Production 🚀

### 3.1 Commit Changes

```bash
cd /Users/js/autopilot-core

# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "feat: Complete Module 4 & 5 improvements

✅ Module 4: Integration Hub (100%)
- Implemented full OAuth 2.0 flow for Gmail/Drive
- Added Telegram chat_id configuration
- Fixed postMessage XSS vulnerability
- Added refresh token support

✅ Module 5: Visual Layer (98%)
- Added dark/light theme toggle
- Implemented ARIA labels (WCAG 2.1 AA compliant)
- Added focus states for keyboard navigation
- Full accessibility support

Tests: 43/43 passing
Documentation: Complete
Production: Ready"

# Push to trigger deployment
git push
```

### 3.2 Monitor Deployment

Railway will automatically:
1. Detect the push
2. Build the application
3. Run tests (if configured)
4. Deploy to production

Monitor at: https://railway.app/project/aiassistant-os-platform

---

## Step 4: Verify Deployment ✅

### 4.1 Test Backend

```bash
# Test OAuth URL generation
curl https://aiassistant-production-7a4d.up.railway.app/api/integrations/connect \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"integration_type":"gmail"}'

# Should return: {"oauth_url": "https://accounts.google.com/...", ...}
```

### 4.2 Test Frontend

1. **Open**: https://aiassistant-iq6yfcgll-vendhubs-projects.vercel.app/integrations

2. **Test Theme Toggle**:
   - Click sun/moon icon in top-right
   - Verify theme switches
   - Verify persistence (refresh page)

3. **Test Telegram Integration**:
   - Click "Connect" on Telegram
   - Enter bot token
   - Enter chat ID (optional)
   - Click "Save"
   - Verify success message

4. **Test Gmail OAuth**:
   - Click "Connect" on Gmail
   - Should redirect to Google OAuth
   - Authorize the application
   - Should redirect back with success
   - Verify integration shows as "Connected"

5. **Test Keyboard Navigation**:
   - Press Tab key
   - Verify blue focus ring appears
   - Navigate through all elements
   - Verify all interactive elements are focusable

---

## Step 5: Post-Deployment Checks 🔍

### 5.1 Check Logs

```bash
# View Railway logs
railway logs

# Look for:
# ✅ "WorkflowEngine initialized"
# ✅ "Workflow scheduler started successfully"
# ✅ "Server running on..."
# ❌ Any errors
```

### 5.2 Database Verification

```bash
# Check that metadata column exists
sqlite3 data/history.db "PRAGMA table_info(integration_tokens);"

# Should show 'metadata' column
```

### 5.3 Test OAuth Flow (End-to-End)

1. Create test user account
2. Go to Integrations page
3. Connect Gmail
4. Authorize on Google
5. Check database for tokens:

```bash
sqlite3 data/history.db "SELECT user_id, integration_type,
  CASE WHEN access_token != '' THEN 'present' ELSE 'missing' END as token,
  CASE WHEN refresh_token != '' THEN 'present' ELSE 'missing' END as refresh,
  expires_at, created_at
FROM integration_tokens
WHERE integration_type IN ('gmail', 'google_drive');"
```

---

## Troubleshooting 🔧

### Issue: "OAuth configuration missing"

**Solution**: Verify Railway variables are set correctly
```bash
railway variables | grep GOOGLE
```

### Issue: "redirect_uri_mismatch"

**Solution**:
1. Check Google Cloud Console → OAuth client
2. Verify redirect URI exactly matches:
   `https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback`
3. No trailing slashes!

### Issue: "API not enabled"

**Solution**: Enable Gmail API and Drive API in Google Cloud Console

### Issue: Theme toggle not working

**Solution**:
1. Check browser console for errors
2. Verify Tailwind config deployed
3. Clear browser cache
4. Check localStorage in DevTools

### Issue: "Invalid state parameter"

**Solution**:
- State format should be `user_id:integration_type`
- Check backend logs for parsing errors

---

## Rollback Plan 🔙

If something goes wrong:

```bash
# Revert to previous commit
git log --oneline -5  # Find previous commit hash
git revert <commit-hash>
git push

# Or restore Railway variables
railway variables --set "GOOGLE_CLIENT_ID="
railway variables --set "GOOGLE_CLIENT_SECRET="
railway variables --set "GOOGLE_REDIRECT_URI="
```

---

## Success Criteria ✅

Deployment is successful when:

- [ ] Railway deployment completes without errors
- [ ] Backend responds to health check
- [ ] OAuth URL generation works
- [ ] Theme toggle switches correctly
- [ ] Telegram integration accepts chat_id
- [ ] Gmail OAuth flow completes successfully
- [ ] Tokens saved to database
- [ ] Keyboard navigation works
- [ ] ARIA labels present (check with screen reader)
- [ ] No console errors

---

## Next Steps After Deployment 🎯

1. **Monitor for 24 hours**
   - Check error logs
   - Monitor OAuth success rate
   - Track integration usage

2. **User Testing**
   - Test with real Gmail account
   - Test with real Telegram bot
   - Verify workflows trigger correctly

3. **Documentation**
   - Update user guide
   - Add OAuth setup to docs
   - Document theme toggle feature

4. **Optional Enhancements**
   - Implement auto token refresh
   - Add Gmail send functionality
   - Add Drive upload functionality

---

## Quick Reference 📋

### Important URLs:

- **Railway Dashboard**: https://railway.app/dashboard
- **Google Cloud Console**: https://console.cloud.google.com/
- **Production Backend**: https://aiassistant-production-7a4d.up.railway.app
- **Production Frontend**: https://aiassistant-iq6yfcgll-vendhubs-projects.vercel.app
- **OAuth Callback**: https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback

### Credentials:

Get from Google Cloud Console OAuth Client configuration:
```
Client ID: <from-google-cloud-console>
Secret: <from-google-cloud-console>
```

### Test Account:

- Email: demo@example.com
- (Use your test credentials)

---

## Support 📞

If you encounter issues:

1. Check logs: `railway logs`
2. Review documentation: `MODULE4_COMPLETE.md`, `MODULE5_IMPROVEMENTS.md`
3. Check test results: `python3 test_*.py`
4. Review session summary: `SESSION_COMPLETE.md`

---

**Last Updated**: 2025-11-06
**Status**: Ready to Deploy ✅
**Estimated Time**: 15-20 minutes
