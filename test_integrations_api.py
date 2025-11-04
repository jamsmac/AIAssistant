#!/usr/bin/env python3
"""
Test script for Integrations API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def main():
    # Step 1: Login
    print("\n🔐 Step 1: Authentication")
    login_data = {"email": "test@example.com", "password": "testpassword123"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

    if response.status_code != 200:
        print_response(response, "❌ Login failed")
        return

    print_response(response, "✅ Login successful")
    token = response.json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: List integrations
    print("\n📋 Step 2: List Integrations")
    response = requests.get(f"{BASE_URL}/api/integrations", headers=headers)
    print_response(response, "✅ Integrations List" if response.status_code == 200 else "❌ Failed")

    if response.status_code != 200:
        return

    integrations = response.json()
    print(f"\n✅ Found {len(integrations)} integrations")

    # Step 3: Connect Telegram (with bot token)
    print("\n🔗 Step 3: Connect Telegram Integration")
    telegram_data = {
        "integration_type": "telegram",
        "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz-test-token"
    }
    response = requests.post(
        f"{BASE_URL}/api/integrations/connect",
        json=telegram_data,
        headers=headers
    )
    print_response(response, "✅ Telegram Connected" if response.status_code == 200 else "❌ Failed")

    # Step 4: List integrations again (Telegram should be connected)
    print("\n📋 Step 4: List Integrations (After Connection)")
    response = requests.get(f"{BASE_URL}/api/integrations", headers=headers)
    print_response(response, "✅ Integrations List")

    # Step 5: Test Telegram integration
    print("\n🧪 Step 5: Test Telegram Integration")
    response = requests.post(
        f"{BASE_URL}/api/integrations/test",
        params={"integration_type": "telegram"},
        headers=headers
    )
    print_response(response, "✅ Test Complete" if response.status_code == 200 else "❌ Test Failed")

    # Step 6: Connect Gmail (get OAuth URL)
    print("\n🔗 Step 6: Connect Gmail Integration (OAuth)")
    gmail_data = {
        "integration_type": "gmail"
    }
    response = requests.post(
        f"{BASE_URL}/api/integrations/connect",
        json=gmail_data,
        headers=headers
    )
    print_response(response, "✅ Gmail OAuth URL Generated" if response.status_code == 200 else "❌ Failed")

    # Step 7: Connect Google Drive (get OAuth URL)
    print("\n🔗 Step 7: Connect Google Drive Integration (OAuth)")
    drive_data = {
        "integration_type": "google_drive"
    }
    response = requests.post(
        f"{BASE_URL}/api/integrations/connect",
        json=drive_data,
        headers=headers
    )
    print_response(response, "✅ Drive OAuth URL Generated" if response.status_code == 200 else "❌ Failed")

    # Step 8: Disconnect Telegram
    print("\n🔌 Step 8: Disconnect Telegram Integration")
    response = requests.post(
        f"{BASE_URL}/api/integrations/disconnect",
        params={"integration_type": "telegram"},
        headers=headers
    )
    print_response(response, "✅ Telegram Disconnected" if response.status_code == 200 else "❌ Failed")

    # Step 9: List integrations (Telegram should be disconnected)
    print("\n📋 Step 9: List Integrations (After Disconnection)")
    response = requests.get(f"{BASE_URL}/api/integrations", headers=headers)
    print_response(response, "✅ Integrations List")

    # Step 10: Test error handling - try to test disconnected integration
    print("\n❌ Step 10: Test Error Handling (Disconnected Integration)")
    response = requests.post(
        f"{BASE_URL}/api/integrations/test",
        params={"integration_type": "telegram"},
        headers=headers
    )
    print_response(response, "✅ Error Handled Correctly" if response.status_code == 404 else "⚠️ Unexpected")

    # Step 11: Test error handling - invalid integration type
    print("\n❌ Step 11: Test Error Handling (Invalid Integration)")
    response = requests.post(
        f"{BASE_URL}/api/integrations/connect",
        json={"integration_type": "invalid_service"},
        headers=headers
    )
    print_response(response, "✅ Error Handled Correctly" if response.status_code == 400 else "⚠️ Unexpected")

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
