# JWT Token Storage Migration Guide

## Overview

This document describes the migration from localStorage-based JWT token storage to httpOnly cookie-based storage for improved security.

## Security Benefits

✅ **XSS Protection**: httpOnly cookies cannot be accessed via JavaScript, preventing XSS attacks  
✅ **Automatic Transmission**: Cookies are automatically sent with requests (no manual header management)  
✅ **Secure Flag**: Cookies use `secure` flag in production (HTTPS only)  
✅ **SameSite Protection**: CSRF protection via SameSite attribute  

## Backend Changes

### Cookie Configuration

The backend now sets JWT tokens in httpOnly cookies:

```python
response.set_cookie(
    key="auth_token",
    value=token,
    httponly=True,  # XSS protection
    secure=secure_cookie,  # HTTPS only in production
    samesite="lax",  # CSRF protection
    max_age=86400,  # 24 hours
    path="/"
)
```

### Token Reading

Backend endpoints now read tokens from both sources (for backward compatibility):

1. **Authorization header** (for API clients)
2. **Cookie** (for web browsers - preferred)

```python
# Try header first
if authorization and authorization.startswith("Bearer "):
    token = authorization.replace("Bearer ", "")

# Fallback to cookie
if not token:
    token = request.cookies.get("auth_token")
```

## Frontend Changes

### API Client Updates

The `APIClient` class has been updated:

- ✅ Removed localStorage token management
- ✅ All requests use `credentials: 'include'` to send cookies
- ✅ No Authorization header needed (cookies are automatic)

### Before (localStorage)

```typescript
// ❌ OLD WAY - INSECURE
const token = localStorage.getItem('token');
fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### After (Cookies)

```typescript
// ✅ NEW WAY - SECURE
fetch('/api/endpoint', {
  credentials: 'include'  // Cookies sent automatically
  // No Authorization header needed!
});
```

## Migration Steps

### Step 1: Update API Client

The main API client (`web-ui/lib/api.ts`) has been updated. All requests now use:

```typescript
fetch(url, {
  credentials: 'include',  // ✅ Always include cookies
  // Authorization header removed
});
```

### Step 2: Remove localStorage Token Usage

Search for and remove all instances of:

```typescript
// ❌ Remove these:
localStorage.getItem('token')
localStorage.setItem('token', token)
localStorage.removeItem('token')
```

### Step 3: Update Components

Components that check authentication should use the API client's `checkAuth()` method:

```typescript
// ✅ Use API client
const { isAuthenticated, user } = await apiClient.checkAuth();
```

## Components to Update

The following components still use localStorage for tokens and should be updated:

1. `web-ui/components/Navigation.tsx` - Line 54
2. `web-ui/app/page.tsx` - Lines 84, 144
3. `web-ui/app/integrations/page.tsx` - Multiple lines
4. `web-ui/app/auth/callback/page.tsx` - Lines 72, 76

### Example Fix

**Before:**
```typescript
const token = localStorage.getItem('token');
if (!token) {
  redirect('/login');
}
```

**After:**
```typescript
const { isAuthenticated } = await apiClient.checkAuth();
if (!isAuthenticated) {
  redirect('/login');
}
```

## Testing

### Test Login Flow

1. Login via `/api/auth/login`
2. Check DevTools → Application → Cookies
3. Verify `auth_token` cookie is set with:
   - ✅ `HttpOnly` flag
   - ✅ `Secure` flag (in production)
   - ✅ `SameSite=Lax`

### Test API Requests

1. Make authenticated request
2. Check Network tab → Request Headers
3. Verify cookie is sent automatically
4. Verify no `Authorization` header needed

### Test Logout

1. Call `/api/auth/logout`
2. Verify cookie is deleted
3. Verify subsequent requests return 401

## Backward Compatibility

The system maintains backward compatibility:

- ✅ API clients can still use Authorization header
- ✅ Old localStorage tokens are ignored (not used)
- ✅ Both methods work during transition period

## Security Checklist

- [x] Backend sets httpOnly cookies
- [x] Backend reads from cookies
- [x] Frontend uses `credentials: 'include'`
- [x] Frontend removed localStorage token storage
- [x] Logout clears cookies
- [x] Secure flag set in production
- [x] SameSite protection enabled

## Troubleshooting

### Issue: Cookies Not Sent

**Problem**: Requests return 401 even after login

**Solution**:
1. Check that `credentials: 'include'` is set in fetch
2. Verify CORS allows credentials (`allow_credentials=True`)
3. Check browser console for CORS errors

### Issue: Cookie Not Set

**Problem**: Login succeeds but cookie not visible

**Solution**:
1. Check backend logs for cookie setting
2. Verify `secure` flag matches HTTPS (production)
3. Check domain/path settings

### Issue: CORS Errors

**Problem**: Preflight requests fail

**Solution**:
1. Verify `CORS_ORIGINS` includes your frontend domain
2. Check that `allow_credentials=True` in CORS config
3. Verify origin validation passes

## Related Documentation

- [CORS Setup Guide](./CORS_SETUP.md)
- [Security Hardening](./SECURITY.md)
- [API Documentation](./API_DOCUMENTATION.md)

