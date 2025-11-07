#!/usr/bin/env python3
"""
Database Migration Script: Credit System
Creates tables and initial data for credit-based business model
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database import DB_PATH

def migrate_credit_system():
    """Run credit system migration"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("=" * 60)
    print("CREDIT SYSTEM MIGRATION")
    print("=" * 60)

    try:
        # 1. Add role column to users table
        print("\n[1/6] Adding role column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            print("✓ Added role column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠ Role column already exists, skipping")
            else:
                raise

        # 2. Create user_credits table
        print("\n[2/6] Creating user_credits table...")
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
        print("✓ Created user_credits table")

        # 3. Create credit_transactions table
        print("\n[3/6] Creating credit_transactions table...")
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
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id
            ON credit_transactions(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at
            ON credit_transactions(created_at DESC)
        """)
        print("✓ Created credit_transactions table with indexes")

        # 4. Create credit_packages table
        print("\n[4/6] Creating credit_packages table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                credits INTEGER NOT NULL,
                price_usd REAL NOT NULL,
                bonus_credits INTEGER DEFAULT 0,
                discount_percentage REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created credit_packages table")

        # 5. Create model_credit_costs table
        print("\n[5/6] Creating model_credit_costs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_credit_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                credits_per_1k_tokens INTEGER NOT NULL,
                base_cost_usd REAL NOT NULL,
                markup_percentage REAL NOT NULL DEFAULT 15.0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, model)
            )
        """)
        print("✓ Created model_credit_costs table")

        # 6. Extend ai_model_rankings table
        print("\n[6/6] Extending ai_model_rankings table...")
        try:
            cursor.execute("ALTER TABLE ai_model_rankings ADD COLUMN use_case TEXT DEFAULT 'general'")
            print("✓ Added use_case column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠ use_case column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE ai_model_rankings ADD COLUMN complexity TEXT DEFAULT 'medium'")
            print("✓ Added complexity column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠ complexity column already exists")
            else:
                raise

        try:
            cursor.execute("ALTER TABLE ai_model_rankings ADD COLUMN cost_tier TEXT DEFAULT 'medium'")
            print("✓ Added cost_tier column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠ cost_tier column already exists")
            else:
                raise

        conn.commit()
        print("\n✅ All tables created successfully!")

        # Populate initial data
        populate_initial_data(cursor, conn)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def populate_initial_data(cursor, conn):
    """Populate credit packages and model costs with initial data"""

    print("\n" + "=" * 60)
    print("POPULATING INITIAL DATA")
    print("=" * 60)

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM credit_packages")
    if cursor.fetchone()[0] > 0:
        print("\n⚠ Credit packages already exist, skipping initial data")
        return

    # 1. Populate credit packages
    print("\n[1/3] Populating credit packages...")
    packages = [
        # (name, credits, price_usd, bonus_credits, discount_percentage, display_order, description)
        ("Starter", 1000, 10.0, 0, 0, 1, "Perfect for trying out the platform"),
        ("Basic", 5000, 45.0, 500, 10, 2, "Most popular for regular users"),
        ("Pro", 12000, 100.0, 1500, 12.5, 3, "Great value for power users"),
        ("Business", 30000, 225.0, 5000, 16.7, 4, "Best for teams and businesses"),
        ("Enterprise", 100000, 700.0, 20000, 20, 5, "Maximum value for large-scale usage"),
    ]

    cursor.executemany("""
        INSERT INTO credit_packages
        (name, credits, price_usd, bonus_credits, discount_percentage, display_order, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, packages)
    print(f"✓ Added {len(packages)} credit packages")

    # 2. Populate model credit costs
    print("\n[2/3] Populating model credit costs...")
    # Based on actual pricing from providers (as of 2025)
    # Credits calculated: (base_cost_usd * 100000) / 10 to convert to integer credits
    # Then multiply by (1 + markup_percentage/100)
    model_costs = [
        # OpenAI Models
        ("openai", "gpt-4o", 25, 0.0025, 15.0),  # $2.50 per 1M input tokens
        ("openai", "gpt-4o-mini", 2, 0.00015, 15.0),  # $0.15 per 1M input tokens
        ("openai", "gpt-4-turbo", 100, 0.01, 15.0),  # $10 per 1M input tokens
        ("openai", "gpt-3.5-turbo", 5, 0.0005, 15.0),  # $0.50 per 1M input tokens

        # Anthropic Models (Claude)
        ("anthropic", "claude-3-5-sonnet-20241022", 30, 0.003, 15.0),  # $3 per 1M input tokens
        ("anthropic", "claude-3-5-haiku-20241022", 10, 0.001, 15.0),  # $1 per 1M input tokens
        ("anthropic", "claude-3-opus-20240229", 150, 0.015, 15.0),  # $15 per 1M input tokens
        ("anthropic", "claude-sonnet-4-5-20250929", 30, 0.003, 15.0),  # Latest Sonnet

        # Google Models (Gemini)
        ("google", "gemini-1.5-pro", 35, 0.00125, 15.0),  # $1.25 per 1M input tokens
        ("google", "gemini-1.5-flash", 1, 0.000075, 15.0),  # $0.075 per 1M input tokens
        ("google", "gemini-2.0-flash-exp", 1, 0.000075, 15.0),  # Experimental

        # Mistral Models
        ("mistral", "mistral-large-latest", 40, 0.004, 15.0),  # $4 per 1M input tokens
        ("mistral", "mistral-medium-latest", 27, 0.0027, 15.0),  # $2.7 per 1M input tokens
        ("mistral", "mistral-small-latest", 10, 0.001, 15.0),  # $1 per 1M input tokens

        # Cohere Models
        ("cohere", "command-r-plus", 30, 0.003, 15.0),  # $3 per 1M input tokens
        ("cohere", "command-r", 5, 0.0005, 15.0),  # $0.50 per 1M input tokens

        # Meta Models (via providers)
        ("meta", "llama-3.3-70b", 6, 0.0006, 15.0),  # $0.60 per 1M tokens
        ("meta", "llama-3.1-405b", 50, 0.005, 15.0),  # $5 per 1M tokens

        # DeepSeek Models
        ("deepseek", "deepseek-chat", 1, 0.0001, 15.0),  # $0.10 per 1M tokens
        ("deepseek", "deepseek-coder", 1, 0.0001, 15.0),  # $0.10 per 1M tokens

        # xAI Models
        ("xai", "grok-2", 100, 0.01, 15.0),  # $10 per 1M tokens
        ("xai", "grok-2-mini", 10, 0.001, 15.0),  # $1 per 1M tokens
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO model_credit_costs
        (provider, model, credits_per_1k_tokens, base_cost_usd, markup_percentage)
        VALUES (?, ?, ?, ?, ?)
    """, model_costs)
    print(f"✓ Added {len(model_costs)} model pricing entries")

    # 3. Assign superadmin role
    print("\n[3/3] Assigning superadmin role...")
    cursor.execute("SELECT id, email FROM users WHERE email = ?", ("demo@example.com",))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", ("superadmin", user[0]))
        print(f"✓ Assigned superadmin role to {user[1]}")

        # Give superadmin 10,000 credits to start
        cursor.execute("""
            INSERT INTO user_credits (user_id, balance, total_purchased)
            VALUES (?, ?, ?)
        """, (user[0], 10000, 10000))

        cursor.execute("""
            INSERT INTO credit_transactions
            (user_id, type, amount, balance_before, balance_after, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user[0], "bonus", 10000, 0, 10000, "Initial superadmin credits"))

        print(f"✓ Granted 10,000 credits to superadmin account")
    else:
        print("⚠ demo@example.com user not found, skipping superadmin assignment")

    conn.commit()
    print("\n✅ Initial data populated successfully!")

def show_summary():
    """Show summary of created tables"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)

    # Count records in each table
    tables = [
        "users",
        "user_credits",
        "credit_transactions",
        "credit_packages",
        "model_credit_costs"
    ]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:30} {count:>5} records")
        except sqlite3.OperationalError:
            print(f"{table:30} NOT FOUND")

    conn.close()

if __name__ == "__main__":
    try:
        migrate_credit_system()
        show_summary()
        print("\n✅ Credit system migration completed successfully!")
        print("\n🚀 Next steps:")
        print("   1. Implement CreditManager class")
        print("   2. Implement ModelSelector class")
        print("   3. Create credit purchase endpoints")
        print("   4. Build frontend credit UI")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
