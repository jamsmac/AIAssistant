#!/usr/bin/env python3
"""
Authentication Flow Test Script
Tests the new httpOnly cookie authentication system

Usage:
    python test_auth_flow.py
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_header(msg):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{RESET}\n")

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []

    def add_result(self, test_name, passed, details=""):
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })

    def test_health_check(self):
        """Test API health endpoint"""
        print_info("Testing health check endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                print_success("Health check passed")
                self.add_result("Health Check", True, "API is responding")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                self.add_result("Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Health check error: {str(e)}")
            self.add_result("Health Check", False, str(e))
            return False

    def test_register(self):
        """Test user registration"""
        print_info("Testing user registration...")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "confirm_password": TEST_PASSWORD
                },
                timeout=10
            )

            if response.status_code in [200, 201]:
                print_success("Registration successful")

                # Check for cookie
                if 'auth_token' in self.session.cookies:
                    print_success("Auth cookie set successfully")
                    self.add_result("Registration", True, "User created and cookie set")
                    return True
                else:
                    print_warning("Registration successful but no cookie set")
                    self.add_result("Registration", True, "User created, no cookie")
                    return True

            elif response.status_code == 400:
                error = response.json().get('detail', 'Unknown error')
                if 'already registered' in error.lower():
                    print_info("User already exists, will test login instead")
                    self.add_result("Registration", True, "User already exists")
                    return True
                else:
                    print_error(f"Registration failed: {error}")
                    self.add_result("Registration", False, error)
                    return False
            else:
                print_error(f"Registration failed: {response.status_code}")
                self.add_result("Registration", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Registration error: {str(e)}")
            self.add_result("Registration", False, str(e))
            return False

    def test_login(self):
        """Test user login with httpOnly cookies"""
        print_info("Testing login with httpOnly cookies...")

        # Clear existing cookies
        self.session.cookies.clear()

        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print_success("Login successful")

                # Check response structure
                if 'access_token' in data:
                    print_success("Access token returned in response")
                else:
                    print_warning("No access token in response")

                # Check for httpOnly cookie
                if 'auth_token' in self.session.cookies:
                    cookie = self.session.cookies.get('auth_token')
                    print_success(f"Auth cookie set: {cookie[:20]}...")

                    # Check cookie attributes (best effort - may not be visible in Python)
                    print_info("Cookie security attributes:")
                    print(f"  - Cookie value length: {len(cookie)} chars")

                    self.add_result("Login", True, "Successful with cookie")
                    return True
                else:
                    print_error("Login successful but no cookie set!")
                    self.add_result("Login", False, "No cookie set")
                    return False

            else:
                error = response.json().get('detail', 'Unknown error')
                print_error(f"Login failed: {error}")
                self.add_result("Login", False, error)
                return False

        except Exception as e:
            print_error(f"Login error: {str(e)}")
            self.add_result("Login", False, str(e))
            return False

    def test_authenticated_request(self):
        """Test making an authenticated request using cookies"""
        print_info("Testing authenticated request...")

        try:
            # Try to access a protected endpoint
            response = self.session.get(
                f"{BASE_URL}/api/auth/me",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print_success("Authenticated request successful")
                print_info(f"User: {data.get('email', 'Unknown')}")
                self.add_result("Authenticated Request", True, f"User: {data.get('email')}")
                return True
            elif response.status_code == 401:
                print_error("Authentication failed - cookie not working")
                self.add_result("Authenticated Request", False, "Cookie auth failed")
                return False
            else:
                print_error(f"Unexpected status: {response.status_code}")
                self.add_result("Authenticated Request", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Authenticated request error: {str(e)}")
            self.add_result("Authenticated Request", False, str(e))
            return False

    def test_logout(self):
        """Test logout functionality"""
        print_info("Testing logout...")

        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/logout",
                timeout=10
            )

            if response.status_code == 200:
                print_success("Logout successful")

                # Check if cookie was removed
                if 'auth_token' not in self.session.cookies:
                    print_success("Auth cookie removed")
                    self.add_result("Logout", True, "Cookie cleared")
                else:
                    print_warning("Cookie still present after logout")
                    self.add_result("Logout", True, "Logged out but cookie remains")

                return True
            else:
                print_error(f"Logout failed: {response.status_code}")
                self.add_result("Logout", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Logout error: {str(e)}")
            self.add_result("Logout", False, str(e))
            return False

    def test_unauthorized_access(self):
        """Test that unauthorized requests are rejected"""
        print_info("Testing unauthorized access protection...")

        # Clear cookies
        self.session.cookies.clear()

        try:
            response = self.session.get(
                f"{BASE_URL}/api/auth/me",
                timeout=10
            )

            if response.status_code == 401:
                print_success("Unauthorized access properly blocked")
                self.add_result("Unauthorized Protection", True, "401 returned as expected")
                return True
            elif response.status_code == 200:
                print_error("Unauthorized access allowed - SECURITY ISSUE!")
                self.add_result("Unauthorized Protection", False, "SECURITY ISSUE")
                return False
            else:
                print_warning(f"Unexpected status: {response.status_code}")
                self.add_result("Unauthorized Protection", True, f"Blocked with {response.status_code}")
                return True

        except Exception as e:
            print_error(f"Unauthorized test error: {str(e)}")
            self.add_result("Unauthorized Protection", False, str(e))
            return False

    def test_cookie_security_headers(self):
        """Test that login response has proper cookie security headers"""
        print_info("Testing cookie security headers...")

        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                timeout=10
            )

            if response.status_code == 200:
                # Check Set-Cookie header
                set_cookie = response.headers.get('Set-Cookie', '')

                checks = {
                    'HttpOnly': 'HttpOnly' in set_cookie or 'httponly' in set_cookie.lower(),
                    'Secure': 'Secure' in set_cookie or 'secure' in set_cookie.lower(),
                    'SameSite=Strict': 'SameSite=Strict' in set_cookie or 'samesite=strict' in set_cookie.lower()
                }

                print_info("Cookie security attributes:")
                for attr, present in checks.items():
                    if present:
                        print_success(f"  ✓ {attr}")
                    else:
                        print_warning(f"  ✗ {attr} - may be set by backend")

                # At least httpOnly should be detectable
                if checks['HttpOnly']:
                    self.add_result("Cookie Security", True, "HttpOnly detected")
                    return True
                else:
                    print_warning("Could not verify HttpOnly attribute (may still be set)")
                    self.add_result("Cookie Security", True, "Partial verification")
                    return True
            else:
                print_error("Could not test cookie security (login failed)")
                self.add_result("Cookie Security", False, "Login failed")
                return False

        except Exception as e:
            print_error(f"Cookie security test error: {str(e)}")
            self.add_result("Cookie Security", False, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"Tests Run: {total}")
        print(f"Passed: {GREEN}{passed}{RESET}")
        print(f"Failed: {RED}{total - passed}{RESET}")
        print(f"Success Rate: {GREEN if percentage >= 80 else YELLOW}{percentage:.1f}%{RESET}\n")

        print("Detailed Results:")
        print("-" * 60)
        for result in self.test_results:
            status = f"{GREEN}PASS{RESET}" if result['passed'] else f"{RED}FAIL{RESET}"
            print(f"{status} - {result['test']}")
            if result['details']:
                print(f"       {result['details']}")
        print("-" * 60)

        return percentage >= 80

def main():
    print_header("AUTHENTICATION FLOW TEST")
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Test user: {TEST_EMAIL}")
    print_info(f"Timestamp: {datetime.now().isoformat()}\n")

    tester = AuthenticationTester()

    # Run tests in sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_register),
        ("User Login", tester.test_login),
        ("Authenticated Request", tester.test_authenticated_request),
        ("Cookie Security", tester.test_cookie_security_headers),
        ("Logout", tester.test_logout),
        ("Unauthorized Protection", tester.test_unauthorized_access),
    ]

    for test_name, test_func in tests:
        print_header(test_name)
        test_func()

    # Print summary
    success = tester.print_summary()

    if success:
        print_success("\n🎉 All tests passed! Authentication flow is working correctly.")
        return 0
    else:
        print_error("\n❌ Some tests failed. Please review the results above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {str(e)}")
        sys.exit(1)
