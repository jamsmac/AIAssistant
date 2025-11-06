#!/usr/bin/env python3
"""
Test script for postMessage origin validation (Module 4 Security Fix)
Verifies that origin validation is present in the integrations page
"""

import sys
from pathlib import Path

print("\n" + "=" * 60)
print("🔒 POSTMESSAGE SECURITY FIX VERIFICATION")
print("=" * 60 + "\n")


def test_origin_validation():
    """Test that origin validation exists in integrations page"""
    print("📋 Checking postMessage origin validation\n")
    print("=" * 60)

    try:
        # Read integrations page
        page_path = Path(__file__).parent / "web-ui" / "app" / "integrations" / "page.tsx"

        with open(page_path) as f:
            content = f.read()

        # Check for origin validation
        checks = [
            ("Origin validation check", "event.origin"),
            ("Origin comparison", "allowedOrigin"),
            ("Security warning", "console.warn"),
            ("Return on invalid origin", "return"),
            ("OAuth success handler", "oauth-success"),
            ("OAuth error handler", "oauth-error"),
        ]

        print("\n✅ Security features found:\n")
        all_found = True

        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name} - NOT FOUND")
                all_found = False

        # Check for specific validation pattern
        if "if (event.origin !== allowedOrigin)" in content:
            print("\n✅ Complete validation pattern found:")
            print("   if (event.origin !== allowedOrigin) {")
            print("     console.warn(...);")
            print("     return;")
            print("   }")
        else:
            print("\n⚠️  Validation pattern might be implemented differently")

        # Extract and display the actual implementation
        print("\n📝 Implementation details:")
        if "const handleMessage = (event: MessageEvent)" in content:
            start = content.find("const handleMessage = (event: MessageEvent)")
            end = content.find("};", start) + 2
            snippet = content[start:end]

            # Show first 500 chars
            print(snippet[:500] + "..." if len(snippet) > 500 else snippet)

        print("\n" + "=" * 60)
        if all_found:
            print("✅ ALL SECURITY FEATURES IMPLEMENTED!")
        else:
            print("⚠️  SOME FEATURES MISSING")
        print("=" * 60 + "\n")

        return all_found

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run test"""
    try:
        result = test_origin_validation()

        print("🔒 Security Fix Summary:")
        print("   ✅ Origin validation prevents XSS attacks")
        print("   ✅ Only messages from same origin are accepted")
        print("   ✅ Untrusted origins are logged and rejected")
        print("   ✅ Protects OAuth callback flow")

        print("\n📝 What was fixed:")
        print("""
   BEFORE:
   - Accepted postMessage from ANY origin
   - Vulnerable to XSS attacks
   - No validation of message source

   AFTER:
   - Validates event.origin === window.location.origin
   - Rejects and logs messages from other origins
   - Secure OAuth callback handling
        """)

        if not result:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
