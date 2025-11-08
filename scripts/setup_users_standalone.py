#!/usr/bin/env python3
"""
Standalone User Setup Script
Creates superadmin and test users without requiring full app dependencies
"""

import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"

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

def hash_password_simple(password: str) -> str:
    """
    Simple password hashing (for setup only)
    In production, bcrypt is used - this is just for initial setup
    """
    # Use bcrypt if available, otherwise fall back to simple hash for setup
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    except ImportError:
        # Fallback to SHA256 for initial setup only
        # User should change password after first login which will use bcrypt
        print("  ⚠️  bcrypt not available, using fallback hashing")
        print("  ⚠️  PLEASE CHANGE PASSWORD AFTER FIRST LOGIN!")
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"pbkdf2:sha256:100000${salt}${hashed.hex()}"

def ensure_tables_exist(cursor):
    """Ensure required tables exist"""
    print("[1/6] Ensuring database tables exist...")

    # Create users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login_at TEXT,
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'user'
        )
    """)
    print("✓ Users table ready")

def ensure_role_column_exists(cursor):
    """Ensure users table has role column"""
    print("\n[2/6] Checking users table schema...")

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
    print("\n[3/6] Setting up credit system tables...")

    # Create user_credits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            balance INTEGER NOT NULL DEFAULT 0,
            total_purchased INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create credit_transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            description TEXT,
            request_id INTEGER,
            payment_id INTEGER,
            metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id
        ON credit_transactions(user_id)
    """)

    print("✓ Credit system tables ready")

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
    password_hash = hash_password_simple(password)
    cursor.execute("""
        INSERT INTO users (email, password_hash, role, created_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (email, password_hash, role, datetime.now().isoformat()))

    user_id = cursor.lastrowid
    print(f"✓ Created user: {email} (ID: {user_id}, Role: {role})")
    print(f"  Description: {description}")

    return user_id

def setup_user_credits(cursor, user_id, email, credits):
    """Set up credits for a user"""

    # Check if user already has credits
    cursor.execute("SELECT balance FROM user_credits WHERE user_id = ?", (user_id,))
    existing_credits = cursor.fetchone()

    if existing_credits:
        current_balance = existing_credits[0]
        print(f"  ℹ️  User already has {current_balance} credits")

        # Add more credits
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

    print("═" * 70)
    print("USER SETUP - AI Assistant Platform")
    print("═" * 70)
    print(f"\nDatabase: {DB_PATH}")
    print()

    # Create data directory if it doesn't exist
    DB_PATH.parent.mkdir(exist_ok=True)

    # Create or open database
    if not DB_PATH.exists():
        print("Creating new database...")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Ensure schema is ready
        ensure_tables_exist(cursor)
        ensure_role_column_exists(cursor)
        ensure_credit_tables_exist(cursor)

        # Create superadmin
        print(f"\n[4/6] Creating superadmin user...")
        superadmin_id = create_user(
            cursor,
            SUPERADMIN_EMAIL,
            SUPERADMIN_PASSWORD,
            "superadmin",
            10000,
            "Platform superadmin with full access"
        )
        setup_user_credits(cursor, superadmin_id, SUPERADMIN_EMAIL, 10000)

        # Create test users
        print(f"\n[5/6] Creating test users...")
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
                user_config["credits"]
            )

        # Commit changes
        conn.commit()

        # Show summary
        print("\n[6/6] Setup Summary")
        print("═" * 70)

        cursor.execute("""
            SELECT u.id, u.email, u.role, u.created_at,
                   COALESCE(uc.balance, 0) as credits
            FROM users u
            LEFT JOIN user_credits uc ON u.id = uc.user_id
            ORDER BY u.id
        """)

        users = cursor.fetchall()

        print(f"\n{'ID':<5} {'Email':<35} {'Role':<15} {'Credits':<10}")
        print("-" * 70)
        for user_id, email, role, created_at, credits in users:
            print(f"{user_id:<5} {email:<35} {role:<15} {credits:<10}")

        print("\n" + "═" * 70)
        print("✅ USER SETUP COMPLETE!")
        print("═" * 70)

        # Print credentials
        print("\n📋 USER CREDENTIALS")
        print("═" * 70)

        print(f"\n🔐 SUPERADMIN:")
        print(f"   Email:    {SUPERADMIN_EMAIL}")
        print(f"   Password: {SUPERADMIN_PASSWORD}")
        print(f"   Role:     superadmin")
        print(f"   Credits:  10,000")
        print(f"   ⚠️  CHANGE PASSWORD AFTER FIRST LOGIN!")

        for user in TEST_USERS:
            print(f"\n👤 TEST USER ({user['role'].upper()}):")
            print(f"   Email:    {user['email']}")
            print(f"   Password: {user['password']}")
            print(f"   Role:     {user['role']}")
            print(f"   Credits:  {user['credits']}")

        print("\n" + "═" * 70)
        print("🚀 NEXT STEPS")
        print("═" * 70)
        print("\n1. Save these credentials in a secure password manager")
        print("\n2. Start the backend server:")
        print("   python -m uvicorn api.server:app --reload")
        print("\n3. Test login with curl:")
        print("   curl -X POST http://localhost:8000/api/auth/login \\")
        print("     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"email\":\"{SUPERADMIN_EMAIL}\",\"password\":\"{SUPERADMIN_PASSWORD}\"}}'")
        print("\n4. Change the superadmin password immediately!")
        print("\n5. For production deployment:")
        print("   - Run: bash scripts/setup_production_cors.sh")
        print("   - Set environment variables from PASSWORD_ROTATION_GUIDE.md")
        print("   - Enable 2FA for superadmin account")

        print("\n" + "═" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(setup_users())
