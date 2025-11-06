# Google OAuth Setup Instructions

## Status: ✅ OAuth Client Created

You have successfully created Google OAuth credentials in Google Cloud Console.

---

## 1. Add Credentials to Railway

Replace `your-client-id` and `your-secret` with actual values from Google Cloud Console:

```bash
# Navigate to project
cd /Users/js/autopilot-core

# Set Google OAuth variables
railway variables set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
railway variables set GOOGLE_CLIENT_SECRET="GOCSPX-your-secret"
railway variables set GOOGLE_REDIRECT_URI="https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback"

# Verify variables
railway variables | grep GOOGLE
```

---

## 2. Add to Local .env for Development

Create or update `.env` file in project root:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/callback

# For development, you might need ngrok tunnel:
# GOOGLE_REDIRECT_URI=https://your-ngrok-id.ngrok.io/api/integrations/callback
```

---

## 3. Enable Required Google APIs

Go to: https://console.cloud.google.com/apis/library?project=aiassistant-os-platform

Enable these APIs:
- ✅ **Gmail API** - for email integration
- ✅ **Google Drive API** - for file storage

---

## 4. Install Python Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or add to `requirements.txt`:
```
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
```

---

## 5. OAuth Configuration Summary

### Authorized Domains:
- ✅ `aiassistant-production-7a4d.up.railway.app`
- ✅ `aiassistant-iq6yfcgll-vendhubs-projects.vercel.app`

### Authorized Redirect URIs:
- ✅ `https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback`
- ✅ `https://aiassistant-iq6yfcgll-vendhubs-projects.vercel.app/api/integrations/callback`

### Scopes Configured:
- ✅ `https://www.googleapis.com/auth/gmail.send`
- ✅ `https://www.googleapis.com/auth/gmail.readonly`
- ✅ `https://www.googleapis.com/auth/drive.file`

---

## 6. Testing OAuth Flow

### Local Testing (with ngrok):

1. Start ngrok:
   ```bash
   ngrok http 8000
   ```

2. Copy ngrok URL (e.g., `https://abc123.ngrok.io`)

3. Add to Google Cloud Console:
   - Go to OAuth client settings
   - Add redirect URI: `https://abc123.ngrok.io/api/integrations/callback`

4. Update local .env:
   ```bash
   GOOGLE_REDIRECT_URI=https://abc123.ngrok.io/api/integrations/callback
   ```

5. Start server:
   ```bash
   python api/server.py
   ```

6. Test OAuth:
   - Navigate to: http://localhost:3000/integrations
   - Click "Connect" on Gmail
   - Should redirect to Google OAuth consent screen

---

## 7. Production Deployment

After adding credentials to Railway:

```bash
# Deploy to Railway
railway up

# Or if using git:
git add .
git commit -m "Add Google OAuth integration"
git push
```

Railway will automatically redeploy with new environment variables.

---

## 8. Verify Integration

### Check Backend:
```bash
# Test OAuth URL generation
curl https://aiassistant-production-7a4d.up.railway.app/api/integrations/connect \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"integration_type": "gmail"}'

# Should return OAuth URL
```

### Check Frontend:
1. Go to: https://aiassistant-iq6yfcgll-vendhubs-projects.vercel.app/integrations
2. Click "Connect" on Gmail
3. Should redirect to Google OAuth
4. After authorization, should redirect back with success

---

## 9. Troubleshooting

### Error: "redirect_uri_mismatch"
- Check that redirect URI exactly matches Google Console
- No trailing slashes
- Correct protocol (http/https)

### Error: "invalid_client"
- Check GOOGLE_CLIENT_ID is correct
- Check GOOGLE_CLIENT_SECRET is correct

### Error: "access_denied"
- User declined authorization
- Check OAuth consent screen is configured

### Error: "Verification status: Unverified app"
- Add test users in Google Console → OAuth consent screen → Test users
- Or publish app for verification

---

## 10. Next Steps

After OAuth is working, implement:

1. **Token Refresh Logic** - Automatically refresh expired tokens
2. **Token Storage** - Securely store tokens in database
3. **Gmail Integration** - Send emails via Gmail API
4. **Drive Integration** - Upload/download files via Drive API

---

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `.env` file to git
- Never expose Client Secret in frontend code
- Always validate state parameter in OAuth callback
- Store tokens encrypted in database
- Implement token refresh before expiry

---

**Generated**: 2025-11-06
**Status**: OAuth Client Created ✅
**Next**: Add credentials to Railway and enable APIs
