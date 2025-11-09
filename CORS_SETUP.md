# CORS Configuration Guide

## Overview

This guide explains how to configure CORS (Cross-Origin Resource Sharing) for the AI Assistant Platform in both development and production environments.

## Security Features

The CORS configuration includes:

- ✅ **Origin Validation**: All origins are validated against security best practices
- ✅ **Production Safety**: HTTP origins are blocked in production (except localhost)
- ✅ **Dangerous Pattern Detection**: Rejects origins with XSS/injection patterns
- ✅ **Comprehensive Headers**: Supports all necessary headers for modern web apps
- ✅ **Preflight Caching**: Caches OPTIONS requests for 1 hour to improve performance

## Development Setup

### Default Origins

The following origins are allowed by default in development:

- `http://localhost:3000` (Next.js default)
- `http://localhost:3001` (Alternative port)
- `http://localhost:3002` (Alternative port)
- `http://localhost:5173` (Vite dev server)

No configuration needed for local development!

## Production Setup

### Environment Variable

Set the `CORS_ORIGINS` environment variable with your production domains:

```bash
# Single domain
CORS_ORIGINS=https://app.example.com

# Multiple domains (comma-separated)
CORS_ORIGINS=https://app.example.com,https://www.example.com,https://admin.example.com
```

### Railway Configuration

1. Go to your Railway project settings
2. Navigate to "Variables"
3. Add new variable:
   - **Name**: `CORS_ORIGINS`
   - **Value**: `https://your-app.vercel.app,https://your-custom-domain.com`
4. Save and redeploy

### Vercel Configuration

If your frontend is on Vercel, add the backend URL to CORS_ORIGINS:

```bash
CORS_ORIGINS=https://your-frontend.vercel.app
```

## Validation Rules

The CORS validator enforces:

1. **URL Format**: Must start with `http://` or `https://`
2. **Production HTTPS**: In production, only HTTPS origins are allowed (except localhost)
3. **No Dangerous Patterns**: Rejects origins containing:
   - `<`, `>`, `'`, `"`
   - `javascript:`, `data:`, `vbscript:`

## Allowed Headers

The following headers are allowed in CORS requests:

- `Content-Type`
- `Authorization`
- `X-Requested-With`
- `X-CSRF-Token`
- `X-Request-ID`

## Exposed Headers

The following headers are exposed to the frontend:

- `Content-Length`
- `X-Request-ID`
- `X-Response-Time`
- `X-API-Version`

## Testing CORS

### Test from Browser Console

```javascript
// Test CORS from your frontend domain
fetch('https://your-api.railway.app/api/health', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

### Test with cURL

```bash
# Test preflight request
curl -X OPTIONS https://your-api.railway.app/api/health \
  -H "Origin: https://your-app.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test actual request
curl -X GET https://your-api.railway.app/api/health \
  -H "Origin: https://your-app.vercel.app" \
  -v
```

### Expected Response Headers

You should see these headers in successful CORS responses:

```
Access-Control-Allow-Origin: https://your-app.vercel.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With, X-CSRF-Token, X-Request-ID
Access-Control-Expose-Headers: Content-Length, X-Request-ID, X-Response-Time, X-API-Version
Access-Control-Max-Age: 3600
```

## Troubleshooting

### Issue: CORS Error in Browser

**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solutions**:

1. **Check Environment Variable**: Ensure `CORS_ORIGINS` includes your frontend domain
2. **Verify HTTPS**: In production, ensure both frontend and backend use HTTPS
3. **Check Origin Format**: Origin must be exact match (no trailing slashes)
4. **Check Logs**: Look for CORS validation warnings in server logs

### Issue: Preflight Request Fails

**Error**: `CORS preflight request failed`

**Solutions**:

1. **Check Methods**: Ensure your request method is in allowed methods
2. **Check Headers**: Ensure all custom headers are in `allow_headers` list
3. **Check Credentials**: If using cookies, ensure `credentials: 'include'` in fetch

### Issue: Cookies Not Sent

**Error**: Cookies are not being sent with requests

**Solutions**:

1. **Frontend**: Ensure `credentials: 'include'` in fetch options
2. **Backend**: Ensure `allow_credentials=True` in CORS middleware (already set)
3. **SameSite**: Check cookie SameSite attribute (should be 'lax' or 'strict')

## Security Best Practices

1. ✅ **Never use wildcard origins** (`*`) in production
2. ✅ **Always use HTTPS** in production
3. ✅ **Validate all origins** before adding to CORS_ORIGINS
4. ✅ **Use specific domains** instead of wildcard subdomains when possible
5. ✅ **Monitor CORS logs** for rejected origins

## Example Configurations

### Single Frontend Domain

```bash
CORS_ORIGINS=https://app.example.com
```

### Multiple Environments

```bash
CORS_ORIGINS=https://app.example.com,https://staging.example.com,https://admin.example.com
```

### Vercel Preview Deployments

For Vercel preview URLs (dynamic), you may need to add them manually or use a pattern matching approach (not currently supported, but can be added if needed).

## Related Documentation

- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Security Hardening](./SECURITY.md)
- [API Documentation](./API_DOCUMENTATION.md)

