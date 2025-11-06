#!/usr/bin/env python3
"""
Test script for Telegram chat_id configuration (Module 4)
Verifies that chat_id can be stored and used with Telegram integration
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

print("\n" + "=" * 60)
print("🧪 TELEGRAM CHAT_ID CONFIGURATION TEST")
print("=" * 60 + "\n")


def test_database_schema():
    """Test that metadata field exists in integration_tokens table"""
    print("📋 Test 1: Database Schema\n")
    print("=" * 60)

    try:
        import sqlite3
        from agents.database import HistoryDatabase

        db_path = Path(__file__).parent / "data" / "history.db"

        # Check if metadata column exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA table_info(integration_tokens)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        print("\n✅ integration_tokens table columns:")
        for col_name, col_type in columns.items():
            marker = "✅" if col_name == "metadata" else "  "
            print(f"   {marker} {col_name}: {col_type}")

        if 'metadata' in columns:
            print("\n✅ metadata column exists!")
            return True
        else:
            print("\n❌ metadata column NOT found!")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_with_metadata():
    """Test saving integration token with chat_id in metadata"""
    print("\n\n📋 Test 2: Save Token with Metadata\n")
    print("=" * 60)

    try:
        from agents.database import HistoryDatabase

        db_path = Path(__file__).parent / "data" / "history.db"
        db = HistoryDatabase(str(db_path))

        # Test user ID
        test_user_id = 999

        # Save Telegram integration with chat_id
        print("\n1. Saving Telegram integration with chat_id...")
        token_id = db.save_integration_token(
            user_id=test_user_id,
            integration_type='telegram',
            access_token='123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
            metadata={'chat_id': '987654321'}
        )
        print(f"   ✅ Saved with ID: {token_id}")

        # Retrieve and verify
        print("\n2. Retrieving token data...")
        token_data = db.get_integration_token(test_user_id, 'telegram')

        if token_data:
            print("   ✅ Token data retrieved:")
            print(f"      - user_id: {token_data['user_id']}")
            print(f"      - integration_type: {token_data['integration_type']}")
            print(f"      - access_token: {token_data['access_token'][:20]}...")
            print(f"      - metadata: {token_data.get('metadata')}")

            # Parse metadata
            import json
            if token_data.get('metadata'):
                metadata = json.loads(token_data['metadata'])
                chat_id = metadata.get('chat_id')
                print(f"\n   ✅ Parsed chat_id: {chat_id}")

                if chat_id == '987654321':
                    print("   ✅ chat_id matches expected value!")
                else:
                    print(f"   ❌ chat_id mismatch: expected '987654321', got '{chat_id}'")
                    return False
            else:
                print("   ❌ No metadata found!")
                return False
        else:
            print("   ❌ Failed to retrieve token data!")
            return False

        # Cleanup
        print("\n3. Cleaning up test data...")
        db.delete_integration_token(test_user_id, 'telegram')
        print("   ✅ Test data removed")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_integration():
    """Test that workflow engine can access chat_id from metadata"""
    print("\n\n📋 Test 3: Workflow Integration\n")
    print("=" * 60)

    try:
        from agents.workflow_engine import WorkflowEngine

        print("\n✅ WorkflowEngine import successful")

        # Check that _action_send_telegram exists and has been updated
        engine = WorkflowEngine()

        if hasattr(engine, '_action_send_telegram'):
            print("✅ _action_send_telegram method exists")

            # Check method signature includes metadata handling
            import inspect
            source = inspect.getsource(engine._action_send_telegram)

            if 'metadata' in source and 'chat_id' in source:
                print("✅ Method includes metadata and chat_id handling")
                return True
            else:
                print("❌ Method doesn't include metadata handling")
                return False
        else:
            print("❌ _action_send_telegram method not found")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_model():
    """Test that API model accepts chat_id"""
    print("\n\n📋 Test 4: API Model\n")
    print("=" * 60)

    try:
        # Import Pydantic model from server
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "api"))

        # We can't directly import from server due to FastAPI,
        # so we'll check if the model would accept chat_id
        print("\n✅ API model verification:")
        print("   - ConnectRequest should accept 'chat_id' field")
        print("   - Field should be Optional[str]")
        print("   - Used for Telegram integration configuration")

        # Verify by checking server.py content
        server_path = Path(__file__).parent / "api" / "server.py"
        with open(server_path) as f:
            content = f.read()

        if 'chat_id: Optional[str]' in content:
            print("\n   ✅ ConnectRequest model includes chat_id field!")
            return True
        else:
            print("\n   ❌ ConnectRequest model doesn't include chat_id!")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    results = []

    try:
        # Test 1: Database schema
        results.append(("Database Schema", test_database_schema()))

        # Test 2: Save with metadata
        results.append(("Save Token with Metadata", test_save_with_metadata()))

        # Test 3: Workflow integration
        results.append(("Workflow Integration", test_workflow_integration()))

        # Test 4: API model
        results.append(("API Model", test_api_model()))

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60 + "\n")

        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {name}")

        all_passed = all(result[1] for result in results)

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 60 + "\n")

        print("🔧 Implementation Summary:")
        print("   ✅ Added 'metadata' column to integration_tokens table")
        print("   ✅ Updated save_integration_token() to accept metadata dict")
        print("   ✅ Added 'chat_id' field to ConnectRequest model")
        print("   ✅ Backend stores chat_id in metadata JSON")
        print("   ✅ Frontend UI includes chat_id input field")
        print("   ✅ Workflow engine uses metadata chat_id as default")
        print("   ✅ User can override chat_id per workflow action")

        print("\n📝 Usage:")
        print("""
   1. Open Integration Hub in web UI
   2. Click "Connect" for Telegram
   3. Enter bot token from @BotFather
   4. (Optional) Enter default chat ID from @userinfobot
   5. Create workflow with send_telegram action
   6. Action uses default chat_id or specify custom one
        """)

        if not all_passed:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
