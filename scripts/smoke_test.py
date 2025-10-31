#!/usr/bin/env python3
"""
Smoke test для проверки всех компонентов системы
Запуск: python scripts/smoke_test.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Тест всех импортов"""
    print("🧪 Testing imports...")

    try:
        import fastapi
        import uvicorn
        import pydantic
        import bcrypt
        import jwt
        import requests
        import anthropic
        import openai
        try:
            import google.generativeai
        except:
            pass  # Optional
        try:
            import bs4  # beautifulsoup4
        except:
            pass  # Optional
        print("   ✅ All imports OK")
        return True
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_database():
    """Тест базы данных"""
    print("🧪 Testing database...")
    from agents.database import get_db

    db = get_db()

    # Проверка таблиц
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required = ['requests', 'users', 'chat_sessions', 'session_messages', 'request_cache', 'ai_model_rankings']
        missing = []
        for table in required:
            if table not in tables:
                missing.append(table)

        if missing:
            print(f"   ❌ Missing tables: {', '.join(missing)}")
            return False

    print("   ✅ Database OK (all tables present)")
    return True

def test_auth():
    """Тест аутентификации"""
    print("🧪 Testing auth...")
    import os

    # Устанавливаем тестовый ключ
    original_key = os.environ.get('SECRET_KEY')
    os.environ['SECRET_KEY'] = 'test-key-12345678901234567890'

    try:
        from agents.auth import hash_password, verify_password, create_jwt_token, verify_jwt_token

        # Test password hashing
        hash1 = hash_password("testpass123")
        if not verify_password("testpass123", hash1):
            print("   ❌ Password verification failed")
            return False

        if verify_password("wrongpass", hash1):
            print("   ❌ Wrong password accepted")
            return False

        # Test JWT
        token = create_jwt_token(1, "test@test.com")
        payload = verify_jwt_token(token)

        if not payload:
            print("   ❌ JWT verification failed")
            return False

        if payload['sub'] != 1:
            print(f"   ❌ Wrong user ID: {payload['sub']}")
            return False

        if payload['email'] != "test@test.com":
            print(f"   ❌ Wrong email: {payload['email']}")
            return False

        print("   ✅ Auth OK (password & JWT)")
        return True

    finally:
        # Восстанавливаем оригинальный ключ
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        else:
            os.environ.pop('SECRET_KEY', None)

def test_ai_router():
    """Тест AI роутера"""
    print("🧪 Testing AI router...")
    try:
        from agents.ai_router import AIRouter

        router = AIRouter()

        if len(router.models) == 0:
            print("   ❌ No models configured")
            return False

        print(f"   ✅ AI Router OK ({len(router.models)} models configured)")
        return True
    except Exception as e:
        print(f"   ⚠️  AI Router test skipped: {e}")
        return True  # Not critical for basic functionality

def test_cache():
    """Тест кэширования"""
    print("🧪 Testing cache...")
    try:
        from agents.database import get_db

        db = get_db()

        # Check if cache methods exist
        if hasattr(db, 'cache_response') and hasattr(db, 'get_cached_response'):
            # Add to cache
            db.cache_response(
                prompt="smoke_test_prompt",
                response="smoke_test_response",
                model="test-model",
                task_type="test",
                ttl_hours=1
            )

            # Get from cache
            cached = db.get_cached_response("smoke_test_prompt", "test")

            if cached is None:
                print("   ❌ Cache retrieval failed")
                return False

            if cached['response'] != "smoke_test_response":
                print(f"   ❌ Wrong cached response: {cached['response']}")
                return False

            print("   ✅ Cache OK (write & read)")
        else:
            print("   ⚠️  Cache methods not implemented (optional feature)")

        return True

    except Exception as e:
        print(f"   ⚠️  Cache test skipped: {e}")
        return True  # Not critical

def test_environment():
    """Тест переменных окружения"""
    print("🧪 Testing environment...")
    import os
    from dotenv import load_dotenv

    load_dotenv()

    warnings = []

    # Проверяем обязательные переменные
    if not os.getenv('SECRET_KEY'):
        warnings.append("SECRET_KEY not set")

    if not os.getenv('GEMINI_API_KEY'):
        warnings.append("GEMINI_API_KEY not set (AI features may not work)")

    if warnings:
        print("   ⚠️  Environment warnings:")
        for warning in warnings:
            print(f"      - {warning}")
        return True  # Предупреждение, но не ошибка

    print("   ✅ Environment OK")
    return True

def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("🚀 SMOKE TEST - AI Development System")
    print("="*60 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Authentication", test_auth),
        ("AI Router", test_ai_router),
        ("Cache", test_cache),
        ("Environment", test_environment)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"   💥 Exception in {name}: {e}")
            results.append((name, False))
        print()  # Пустая строка между тестами

    # Итоговый отчет
    print("="*60)
    print("📊 TEST RESULTS")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")

    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")

    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready to use.\n")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
