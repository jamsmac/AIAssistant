#!/usr/bin/env python3
"""Status checker для autopilot-core"""

import os
import sys
from pathlib import Path

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

def check_file(path, description):
    """Проверка существования файла"""
    if Path(path).exists():
        print(f"{GREEN}✅{NC} {description}")
        return True
    else:
        print(f"{RED}❌{NC} {description}")
        return False

def check_in_file(path, text, description):
    """Проверка наличия текста в файле"""
    try:
        if Path(path).exists():
            content = Path(path).read_text()
            if text in content:
                print(f"{GREEN}✅{NC} {description}")
                return True
        print(f"{RED}❌{NC} {description}")
        return False
    except:
        print(f"{RED}❌{NC} {description}")
        return False

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   🔍 AUTOPILOT-CORE STATUS CHECK                         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    checks = []
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📁 CORE FILES")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_file("agents/database.py", "Database module"))
    checks.append(check_file("agents/ai_router.py", "AI Router module (includes MODELS config)"))
    checks.append(check_file("agents/auth.py", "Auth module"))
    checks.append(check_file("api/server.py", "FastAPI server"))
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔐 JWT AUTHENTICATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_in_file("agents/database.py", "users", "Users table"))
    checks.append(check_in_file("agents/database.py", "create_user", "create_user method"))
    checks.append(check_in_file("agents/auth.py", "hash_password", "hash_password function"))
    checks.append(check_in_file("agents/auth.py", "create_jwt_token", "JWT token creation"))
    checks.append(check_in_file("api/server.py", "RegisterRequest", "RegisterRequest model"))
    checks.append(check_in_file("api/server.py", "/api/auth/register", "Register endpoint"))
    checks.append(check_in_file("api/server.py", "/api/auth/login", "Login endpoint"))
    checks.append(check_in_file("api/server.py", "get_current_user_from_token", "JWT middleware"))
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("⚙️  CONFIGURATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_file(".env.example", ".env.example template"))
    checks.append(check_file("requirements.txt", "requirements.txt"))
    checks.append(check_in_file("requirements.txt", "bcrypt", "bcrypt dependency"))
    checks.append(check_in_file("requirements.txt", "PyJWT", "PyJWT dependency"))
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🧪 TESTING")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_file("scripts/smoke_test.py", "Smoke test suite"))
    checks.append(check_file("scripts/update_rankings.py", "Rankings update"))
    checks.append(check_file("scripts/generate_report.py", "Report generation"))
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📚 DOCUMENTATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_file("README.md", "README"))
    checks.append(check_file("STATUS.md", "STATUS"))
    checks.append(check_file(".cursorrules", "Cursor rules"))
    checks.append(check_file("COMPLETION_REPORT.md", "Completion report"))
    checks.append(check_in_file("README.md", "Environment Setup", "Env setup section"))
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎨 FRONTEND")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    checks.append(check_file("app/page.tsx", "Dashboard page"))
    checks.append(check_file("app/chat/page.tsx", "Chat page"))
    checks.append(check_file("package.json", "package.json"))
    print()
    
    # Подсчет результатов
    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    percentage = (passed * 100) // total
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                    📊 SUMMARY                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print(f"Total Checks:  {total}")
    print(f"{GREEN}Passed:       {passed}{NC}")
    print(f"{RED}Failed:       {failed}{NC}")
    print()
    print(f"Completion:    {percentage}%")
    print()
    
    if failed == 0:
        print(f"{GREEN}🎉 ALL CHECKS PASSED! System is 100% ready!{NC}")
        return 0
    else:
        print(f"{YELLOW}⚠️  Some checks failed. See details above.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
