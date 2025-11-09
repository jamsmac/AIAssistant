# 🔐 Authentication Testing Guide

**Purpose**: Verify the new httpOnly cookie authentication system
**Date**: 2025-11-09
**Security Level**: Critical

---

## 📋 Quick Summary

**What Changed**:
- ❌ **OLD**: Tokens stored in localStorage (XSS vulnerable)
- ✅ **NEW**: Tokens in httpOnly cookies (XSS protected)

**Security Improvements**:
- httpOnly cookies (JavaScript cannot access)
- Secure flag (HTTPS only in production)
- SameSite=Strict (CSRF protection)

---

## 🚀 Quick Start Testing

### Option 1: Automated Test Script

```bash
# Start the backend server first
python api/server.py

# In another terminal, run the test script
python3 test_auth_flow.py
```

### Option 2: Manual Browser Testing

**Steps**:
1. Start backend: `python api/server.py`
2. Start frontend: `cd web-ui && npm run dev`
3. Open browser to `http://localhost:3000`
4. Follow manual tests below

### Option 3: cURL Testing

See "cURL Test Commands" section below

---

## 🧪 Manual Browser Testing

### Test 1: Login Flow

**Steps**:
1. Open DevTools (F12)
2. Go to Application tab → Cookies
3. Navigate to login page
4. Enter credentials and submit
5. **Verify**:
   - ✅ Cookie named `auth_token` appears
   - ✅ `HttpOnly` flag is ✓ (checked)
   - ✅ `Secure` flag is ✓ (checked)
   - ✅ `SameSite` is `Strict`
   - ✅ NO `token` in localStorage

**Expected Behavior**:
- Cookie appears immediately after login
- Cookie is marked as HttpOnly
- No JavaScript can read the token value

**Screenshot Verification**:
```
Application → Cookies → localhost:3000

Name        | Value          | HttpOnly | Secure | SameSite
------------|----------------|----------|--------|----------
auth_token  | eyJhbGc...     | ✓        | ✓      | Strict
```

---

### Test 2: localStorage Check

**Steps**:
1. After logging in, open Console tab
2. Run: `localStorage.getItem('token')`
3. **Verify**: Returns `null` (not a token string)

**Expected Output**:
```javascript
> localStorage.getItem('token')
< null
```

**❌ If you see a token string**: SECURITY ISSUE - token still in localStorage

---

### Test 3: Authenticated Requests

**Steps**:
1. After login, go to Dashboard
2. Open Network tab in DevTools
3. Filter by "Fetch/XHR"
4. Navigate to different pages
5. **Verify** each request:
   - ✅ Cookie header sent automatically
   - ✅ No Authorization header with Bearer token
   - ✅ Requests succeed (200 OK)

**Expected Network Headers**:
```
Request Headers:
Cookie: auth_token=eyJhbGc...
# NO "Authorization: Bearer ..." header
```

---

### Test 4: Logout Flow

**Steps**:
1. While logged in, check cookies exist
2. Click Logout
3. Check cookies again
4. Try to access protected page

**Verify**:
- ✅ `auth_token` cookie is deleted
- ✅ Redirected to login page
- ✅ Protected pages redirect to login

---

### Test 5: Session Persistence

**Steps**:
1. Login successfully
2. Close browser tab (not entire browser)
3. Reopen same URL
4. **Verify**: Still logged in (don't need to login again)

**Note**: If you close entire browser, session may end (depending on cookie max-age)

---

### Test 6: XSS Protection Verification

**Steps**:
1. Login successfully
2. Open Console
3. Try to read cookie: `document.cookie`
4. **Verify**: `auth_token` is **NOT** visible in output

**Expected Output**:
```javascript
> document.cookie
< "" // Or other cookies, but NOT auth_token
```

**Why**: HttpOnly flag prevents JavaScript from reading the cookie

---

## 💻 cURL Test Commands

### Test Login
```bash
# Login and save cookies
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }' \
  -v

# Look for Set-Cookie header in output:
# Set-Cookie: auth_token=...; HttpOnly; Secure; SameSite=Strict
```

### Test Authenticated Request
```bash
# Use saved cookies
curl -b cookies.txt http://localhost:8000/api/auth/me \
  -v

# Should return user info (200 OK)
```

### Test Logout
```bash
curl -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/auth/logout \
  -v

# Cookie should be deleted from cookies.txt
```

### Test Unauthorized Access
```bash
# Without cookies
curl http://localhost:8000/api/auth/me \
  -v

# Should return 401 Unauthorized
```

---

## 🐍 Python Test Script

The automated test script `test_auth_flow.py` runs 7 comprehensive tests:

### Tests Performed:
1. **Health Check** - Verify API is running
2. **User Registration** - Create test user
3. **User Login** - Login with httpOnly cookies
4. **Authenticated Request** - Access protected endpoint
5. **Cookie Security** - Verify security headers
6. **Logout** - Test cookie removal
7. **Unauthorized Protection** - Verify 401 without cookie

### Running the Script:
```bash
# Make sure server is running
python api/server.py &

# Run tests
python3 test_auth_flow.py

# Expected output:
# ✓ All tests passed! Authentication flow is working correctly.
```

### Test Output Example:
```
============================================================
  TEST SUMMARY
============================================================

Tests Run: 7
Passed: 7
Failed: 0
Success Rate: 100.0%

Detailed Results:
------------------------------------------------------------
PASS - Health Check
       API is responding
PASS - Registration
       User created and cookie set
PASS - Login
       Successful with cookie
PASS - Authenticated Request
       User: test@example.com
PASS - Cookie Security
       HttpOnly detected
PASS - Logout
       Cookie cleared
PASS - Unauthorized Protection
       401 returned as expected
------------------------------------------------------------

🎉 All tests passed! Authentication flow is working correctly.
```

---

## 🔍 Troubleshooting

### Issue: Cookie Not Set After Login

**Symptoms**:
- Login succeeds but no cookie appears
- Subsequent requests return 401

**Check**:
1. Verify `response.set_cookie()` in [api/routers/auth_router.py:175](api/routers/auth_router.py#L175)
2. Check server logs for errors
3. Verify CORS settings allow credentials

**Solution**:
```python
# Should have in auth_router.py:
response.set_cookie(
    key="auth_token",
    value=access_token,
    httponly=True,    # ✓
    secure=True,      # ✓
    samesite="strict", # ✓
    max_age=86400,
    path="/"
)
```

---

### Issue: Token Still in localStorage

**Symptoms**:
- `localStorage.getItem('token')` returns a token string
- Security vulnerability still present

**Check**:
1. Hard refresh page (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache and localStorage
3. Check frontend code for remaining `localStorage.setItem('token')`

**Solution**:
```bash
# Search for remaining localStorage usage
grep -r "localStorage.setItem.*token" web-ui/app web-ui/lib

# Should return: (nothing) or only .bak files
```

---

### Issue: Requests Not Including Cookies

**Symptoms**:
- Logged in but API returns 401
- Network tab shows no Cookie header

**Check Frontend Code**:
```javascript
// All fetch calls should have:
fetch(url, {
  credentials: 'include'  // ← REQUIRED for cookies
})
```

**Fixed Files**:
- ✅ web-ui/lib/api.ts
- ✅ web-ui/app/admin/credits/users/page.tsx
- ✅ web-ui/app/admin/credits/page.tsx
- ✅ web-ui/app/credits/success/page.tsx
- ✅ web-ui/app/integrations/page.tsx (5 places)
- ✅ web-ui/app/page.tsx (2 places)

---

### Issue: CORS Errors

**Symptoms**:
- Cookies not sent
- CORS error in console
- "Access to fetch... has been blocked by CORS policy"

**Check**:
1. Backend allows credentials:
```python
# api/server.py
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,  # ← Must be True
    # ...
)
```

2. Frontend includes credentials:
```javascript
fetch(url, {
  credentials: 'include'
})
```

3. Origin is in ALLOWED_ORIGINS

---

### Issue: Cookie Not Visible in DevTools

**Expected**: This is **NORMAL** for httpOnly cookies!

**Why**: HttpOnly cookies are hidden from JavaScript and DevTools Console

**How to Verify**:
- Use Application tab → Cookies (not Console)
- Use Network tab → Headers → Request Headers → Cookie
- Check "Show httpOnly cookies" in DevTools settings

---

## ✅ Success Criteria

### Backend Verification:
- ✅ Login endpoint sets `auth_token` cookie
- ✅ Cookie has `httponly=True`
- ✅ Cookie has `secure=True`
- ✅ Cookie has `samesite="strict"`
- ✅ Middleware reads token from cookie
- ✅ Logout deletes cookie

### Frontend Verification:
- ✅ NO `localStorage.setItem('token')` in code
- ✅ NO `localStorage.getItem('token')` in code
- ✅ ALL fetch calls have `credentials: 'include'`
- ✅ Auth flow works without localStorage
- ✅ Users can login, access pages, logout

### Security Verification:
- ✅ JavaScript CANNOT access `auth_token` cookie
- ✅ XSS attacks CANNOT steal tokens
- ✅ CSRF protection via SameSite=Strict
- ✅ Tokens only sent over HTTPS (in production)

---

## 📊 Test Checklist

Use this checklist when testing:

### Pre-Deployment Tests:
- [ ] Server starts without errors
- [ ] Login page loads
- [ ] Registration works
- [ ] Login sets httpOnly cookie
- [ ] Dashboard loads after login
- [ ] No token in localStorage
- [ ] Protected pages accessible
- [ ] Logout clears cookie
- [ ] Unauthorized requests blocked

### Post-Deployment Tests:
- [ ] Production HTTPS works
- [ ] Cookie Secure flag enforced
- [ ] No CORS errors
- [ ] Session persistence works
- [ ] Mobile browsers work
- [ ] All API endpoints functional

### Security Tests:
- [ ] XSS cannot steal tokens
- [ ] CSRF protection active
- [ ] No tokens in JavaScript scope
- [ ] HTTPOnly enforced
- [ ] SameSite=Strict enforced

---

## 🎯 Expected Test Results

### ✅ PASS Criteria:

**Login Test**:
- Returns 200 OK
- Sets `auth_token` cookie
- Cookie has security flags
- User redirected to dashboard

**Protected Endpoint Test**:
- Returns 200 OK with cookie
- Returns 401 without cookie
- Cookie sent automatically

**Logout Test**:
- Returns 200 OK
- Deletes `auth_token` cookie
- User redirected to login

**Security Test**:
- `document.cookie` does NOT show `auth_token`
- localStorage is empty (no tokens)
- All requests include `credentials: 'include'`

---

## 📞 Support

### If Tests Fail:

1. **Check server logs** for errors
2. **Review browser console** for JavaScript errors
3. **Check Network tab** for failed requests
4. **Verify code changes** were saved and built
5. **Clear cache** and try again

### Resources:
- [P0_CRITICAL_FIXES_COMPLETED.md](P0_CRITICAL_FIXES_COMPLETED.md) - Detailed fix documentation
- [FIXES_VERIFICATION_PASSED.md](FIXES_VERIFICATION_PASSED.md) - Verification procedures
- [USER_GUIDE.md](USER_GUIDE.md) - User documentation
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference

---

## 🚀 Ready to Deploy?

Once all tests pass:

1. ✅ All automated tests passing
2. ✅ Manual browser tests successful
3. ✅ Security verification complete
4. ✅ No localStorage tokens found
5. ✅ Cookies working correctly

**Then**: Proceed with deployment!

See [FIXES_VERIFICATION_PASSED.md](FIXES_VERIFICATION_PASSED.md) for deployment checklist.

---

**Created**: 2025-11-09
**Purpose**: Verify httpOnly cookie authentication
**Status**: Ready for Testing

---

END OF TESTING GUIDE
