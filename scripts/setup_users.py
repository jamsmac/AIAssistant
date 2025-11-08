#!/usr/bin/env python3
"""
User Setup Script
Creates superadmin and test users for the AI Assistant platform
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import secrets

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database import DB_PATH
from agents.auth import hash_password

# User configurations
SUPERADMIN_EMAIL = "jamshidsmail@icloud.com"
SUPERADMIN_PASSWORD = "SuperAdmin2025!"  # Change this after first login!

TEST_USERS = [
    {
        "email": "user@test.com",
        "password": "TestUser2025!",
        "role": "user",
        "credits": 1000,
        "description": "Regular test user"
    }
]

def ensure_role_column_exists(cursor):
    """Ensure users table has role column"""
    print("[1/5] Checking users table schema...")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        print("✓ Added role column to users table")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("✓ Role column already exists")
        else:
            raise

def ensure_credit_tables_exist(cursor):
    """Ensure credit system tables exist"""
    print("\n[2/5] Checking credit system tables...")

    # Check if credit tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='user_credits'
    """)

    if cursor.fetchone() is None:
        print("⚠️  Credit tables not found. Please run: python scripts/migrate_credit_system.py")
        print("   Continuing without credits setup...")
        return False
    else:
        print("✓ Credit system tables exist")
        return True

def create_user(cursor, email, password, role, credits, description):
    """Create a user with specified role and credits"""

    # Check if user already exists
    cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        user_id, existing_email, existing_role = existing_user
        print(f"⚠️  User {email} already exists (ID: {user_id}, Role: {existing_role})")

        # Update role if different
        if existing_role != role:
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            print(f"   ✓ Updated role from '{existing_role}' to '{role}'")

        return user_id

    # Create new user
    password_hash = hash_password(password)
    cursor.execute("""
        INSERT INTO users (email, password_hash, role, created_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (email, password_hash, role, datetime.now().isoformat()))

    user_id = cursor.lastrowid
    print(f"✓ Created user: {email} (ID: {user_id}, Role: {role})")
    print(f"  Description: {description}")

    return user_id

def setup_user_credits(cursor, user_id, email, credits, has_credit_system):
    """Set up credits for a user"""

    if not has_credit_system:
        return

    # Check if user already has credits
    cursor.execute("SELECT balance FROM user_credits WHERE user_id = ?", (user_id,))
    existing_credits = cursor.fetchone()

    if existing_credits:
        current_balance = existing_credits[0]
        print(f"  ℹ️  User already has {current_balance} credits")

        # Ask if we should add more
        if credits > 0:
            cursor.execute("""
                UPDATE user_credits
                SET balance = balance + ?,
                    total_purchased = total_purchased + ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (credits, credits, datetime.now().isoformat(), user_id))

            # Log transaction
            cursor.execute("""
                INSERT INTO credit_transactions
                (user_id, type, amount, balance_before, balance_after, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "bonus",
                credits,
                current_balance,
                current_balance + credits,
                "Setup bonus credits",
                datetime.now().isoformat()
            ))

            print(f"  ✓ Added {credits} credits (New balance: {current_balance + credits})")
    else:
        # Create new credit account
        cursor.execute("""
            INSERT INTO user_credits (user_id, balance, total_purchased, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, credits, credits, datetime.now().isoformat(), datetime.now().isoformat()))

        # Log transaction
        cursor.execute("""
            INSERT INTO credit_transactions
            (user_id, type, amount, balance_before, balance_after, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "bonus",
            credits,
            0,
            credits,
            "Initial credits",
            datetime.now().isoformat()
        ))

        print(f"  ✓ Granted {credits} credits")

def setup_users():
    """Main setup function"""

    print("=" * 70)
    print("USER SETUP - AI Assistant Platform")
    print("=" * 70)
    print(f"\nDatabase: {DB_PATH}")
    print()

    # Check if database exists
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("\nPlease run the application first to initialize the database:")
        print("   python -m uvicorn api.server:app --reload")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Ensure schema is ready
        ensure_role_column_exists(cursor)
        has_credit_system = ensure_credit_tables_exist(cursor)

        # Create superadmin
        print(f"\n[3/5] Creating superadmin user...")
        superadmin_id = create_user(
            cursor,
            SUPERADMIN_EMAIL,
            SUPERADMIN_PASSWORD,
            "superadmin",
            10000,
            "Platform superadmin with full access"
        )
        setup_user_credits(cursor, superadmin_id, SUPERADMIN_EMAIL, 10000, has_credit_system)

        # Create test users
        print(f"\n[4/5] Creating test users...")
        for user_config in TEST_USERS:
            user_id = create_user(
                cursor,
                user_config["email"],
                user_config["password"],
                user_config["role"],
                user_config["credits"],
                user_config["description"]
            )
            setup_user_credits(
                cursor,
                user_id,
                user_config["email"],
                user_config["credits"],
                has_credit_system
            )

        # Commit changes
        conn.commit()

        # Show summary
        print("\n[5/5] Setup Summary")
        print("=" * 70)

        cursor.execute("""
            SELECT u.id, u.email, u.role, u.created_at,
                   COALESCE(uc.balance, 0) as credits
            FROM users u
            LEFT JOIN user_credits uc ON u.id = uc.user_id
            WHERE u.email IN (?, ?)
        """, (SUPERADMIN_EMAIL, *[u["email"] for u in TEST_USERS]))

        users = cursor.fetchall()

        print(f"\n{'ID':<5} {'Email':<30} {'Role':<15} {'Credits':<10}")
        print("-" * 70)
        for user_id, email, role, created_at, credits in users:
            print(f"{user_id:<5} {email:<30} {role:<15} {credits:<10}")

        print("\n" + "=" * 70)
        print("✅ USER SETUP COMPLETE!")
        print("=" * 70)

        # Print credentials
        print("\n📋 USER CREDENTIALS")
        print("=" * 70)

        print(f"\n🔐 SUPERADMIN:")
        print(f"   Email:    {SUPERADMIN_EMAIL}")
        print(f"   Password: {SUPERADMIN_PASSWORD}")
        print(f"   Role:     superadmin")
        print(f"   ⚠️  CHANGE PASSWORD AFTER FIRST LOGIN!")

        for user in TEST_USERS:
            print(f"\n👤 TEST USER ({user['role'].upper()}):")
            print(f"   Email:    {user['email']}")
            print(f"   Password: {user['password']}")
            print(f"   Role:     {user['role']}")

        print("\n" + "=" * 70)
        print("🚀 NEXT STEPS")
        print("=" * 70)
        print("\n1. Save these credentials in a secure password manager")
        print("2. Start the backend server:")
        print("   python -m uvicorn api.server:app --reload")
        print("\n3. Login at: http://localhost:8000/api/auth/login")
        print("   POST request with JSON body:")
        print("   {\"email\": \"jamshidsmail@icloud.com\", \"password\": \"SuperAdmin2025!\"}")
        print("\n4. Change the superadmin password immediately!")
        print("\n5. For production deployment:")
        print("   - Set CORS_ORIGINS in Railway")
        print("   - Use the PASSWORD_ROTATION_GUIDE.md")
        print("   - Enable 2FA for superadmin account")

        print("\n" + "=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    setup_users()
