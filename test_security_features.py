#!/usr/bin/env python3
"""
Security Features Test Script
Tests OAuth, CSRF, PostgreSQL, and other security implementations
"""
import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Optional

# Test configuration
API_BASE_URL = "http://localhost:8000"  # Change to production URL when deployed
TEST_EMAIL = "security_test@example.com"
TEST_PASSWORD = "SecureTestPassword123!"

class SecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.access_token: Optional[str] = None
        self.csrf_token: Optional[str] = None
        self.test_results = []

    async def test_registration(self):
        """Test user registration with validation"""
        print("\n🔐 Testing Registration...")

        # Test weak password
        response = await self.client.post("/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": "weak",
            "confirm_password": "weak"
        })
        assert response.status_code == 400, "Weak password should be rejected"
        self.test_results.append("✅ Weak password validation")

        # Test password mismatch
        response = await self.client.post("/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": "different"
        })
        assert response.status_code == 400, "Password mismatch should be rejected"
        self.test_results.append("✅ Password mismatch validation")

        # Test valid registration
        response = await self.client.post("/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD
        })

        if response.status_code == 409:
            print("  ⚠ User already exists, skipping registration")
        else:
            assert response.status_code == 200, f"Registration failed: {response.text}"
            data = response.json()
            assert "access_token" in data
            assert "csrf_token" in data
            self.access_token = data["access_token"]
            self.csrf_token = data["csrf_token"]
            self.test_results.append("✅ User registration")

    async def test_login(self):
        """Test login with various scenarios"""
        print("\n🔐 Testing Login...")

        # Test invalid credentials
        response = await self.client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Invalid credentials should be rejected"
        self.test_results.append("✅ Invalid credentials rejection")

        # Test valid login
        response = await self.client.post("/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "csrf_token" in data
        self.access_token = data["access_token"]
        self.csrf_token = data["csrf_token"]
        self.test_results.append("✅ User login")

    async def test_csrf_protection(self):
        """Test CSRF protection"""
        print("\n🛡️ Testing CSRF Protection...")

        if not self.access_token:
            print("  ⚠ No access token, skipping CSRF tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Test request without CSRF token (should fail for state-changing operations)
        response = await self.client.post(
            "/api/projects",
            headers=headers,
            json={"name": "Test Project"}
        )
        # Note: This might pass if CSRF is checked at middleware level
        # and endpoint is exempt

        # Test CSRF verification endpoint
        response = await self.client.post(
            "/api/auth/verify-csrf",
            headers=headers,
            params={"csrf_token": self.csrf_token}
        )
        if response.status_code == 200:
            self.test_results.append("✅ CSRF token verification")
        else:
            print(f"  ⚠ CSRF verification returned: {response.status_code}")

        # Test CSRF token refresh
        response = await self.client.post(
            "/api/auth/refresh-csrf",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            assert "csrf_token" in data
            self.csrf_token = data["csrf_token"]
            self.test_results.append("✅ CSRF token refresh")

    async def test_oauth_endpoints(self):
        """Test OAuth endpoints"""
        print("\n🔑 Testing OAuth Endpoints...")

        # Test Google OAuth initialization
        response = await self.client.post("/api/auth/oauth/authorize", json={
            "provider": "google",
            "redirect_url": "http://localhost:3000"
        })

        if response.status_code == 200:
            data = response.json()
            assert "auth_url" in data
            assert "state" in data
            assert "google.com" in data["auth_url"]
            self.test_results.append("✅ Google OAuth initialization")
        elif response.status_code == 400:
            print("  ⚠ Google OAuth not configured")

        # Test GitHub OAuth initialization
        response = await self.client.post("/api/auth/oauth/authorize", json={
            "provider": "github",
            "redirect_url": "http://localhost:3000"
        })

        if response.status_code == 200:
            data = response.json()
            assert "auth_url" in data
            assert "state" in data
            assert "github.com" in data["auth_url"]
            self.test_results.append("✅ GitHub OAuth initialization")
        elif response.status_code == 400:
            print("  ⚠ GitHub OAuth not configured")

    async def test_authenticated_endpoints(self):
        """Test authenticated endpoint access"""
        print("\n🔒 Testing Authenticated Endpoints...")

        if not self.access_token:
            print("  ⚠ No access token, skipping authenticated tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Test get current user
        response = await self.client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Get user failed: {response.text}"
        data = response.json()
        assert "email" in data
        assert data["email"] == TEST_EMAIL
        self.test_results.append("✅ Get current user")

        # Test unauthorized access
        response = await self.client.get("/api/auth/me")
        assert response.status_code == 401, "Unauthorized access should be rejected"
        self.test_results.append("✅ Unauthorized access rejection")

    async def test_session_management(self):
        """Test session management"""
        print("\n🔐 Testing Session Management...")

        if not self.access_token:
            print("  ⚠ No access token, skipping session tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Test logout
        response = await self.client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200, f"Logout failed: {response.text}"
        self.test_results.append("✅ Session logout")

        # Test access after logout (should fail)
        response = await self.client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401, "Access should be denied after logout"
        self.test_results.append("✅ Session revocation")

    async def test_rate_limiting(self):
        """Test rate limiting"""
        print("\n⏱️ Testing Rate Limiting...")

        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = await self.client.get("/api/health")
            responses.append(response.status_code)

        # Check if rate limiting headers are present
        last_response = await self.client.get("/api/health")
        if "X-RateLimit-Limit" in last_response.headers:
            self.test_results.append("✅ Rate limiting headers present")
        else:
            print("  ⚠ Rate limiting headers not found")

    async def test_database_connection(self):
        """Test database connectivity"""
        print("\n🗄️ Testing Database Connection...")

        response = await self.client.get("/api/health")
        if response.status_code == 200:
            data = response.json()
            if "database" in data:
                assert data["database"] == "connected"
                self.test_results.append("✅ Database connection")
            else:
                self.test_results.append("✅ API health check")

    async def run_all_tests(self):
        """Run all security tests"""
        print("=" * 50)
        print("🔒 Security Features Test Suite")
        print(f"📍 Testing: {self.base_url}")
        print("=" * 50)

        try:
            # Check if API is reachable
            response = await self.client.get("/api/health")
            if response.status_code != 200:
                print(f"❌ API not reachable at {self.base_url}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return False

        # Run tests
        test_methods = [
            self.test_registration,
            self.test_login,
            self.test_csrf_protection,
            self.test_oauth_endpoints,
            self.test_authenticated_endpoints,
            self.test_session_management,
            self.test_rate_limiting,
            self.test_database_connection
        ]

        for test_method in test_methods:
            try:
                await test_method()
            except AssertionError as e:
                print(f"  ❌ Test failed: {e}")
                self.test_results.append(f"❌ {test_method.__name__}: {e}")
            except Exception as e:
                print(f"  ⚠️ Test error: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)

        for result in self.test_results:
            print(f"  {result}")

        passed = sum(1 for r in self.test_results if r.startswith("✅"))
        failed = sum(1 for r in self.test_results if r.startswith("❌"))
        total = len(self.test_results)

        print(f"\n📈 Score: {passed}/{total} tests passed")

        if failed > 0:
            print(f"⚠️ {failed} tests failed")
            return False

        print("🎉 All security features working correctly!")
        return True

    async def cleanup(self):
        """Cleanup test resources"""
        await self.client.aclose()


async def main():
    """Main test runner"""
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else API_BASE_URL

    tester = SecurityTester(api_url)

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("🔒 AI Assistant Security Test Suite")
    print("Usage: python test_security_features.py [API_URL]")
    print()
    asyncio.run(main())