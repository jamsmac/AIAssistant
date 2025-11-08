#!/usr/bin/env python3
"""
Test Supabase database connection
"""
import asyncio
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Try different connection formats
formats = [
    # Format 1: Pooler with project ref in username
    "postgresql://postgres.hbtaablzueprzuwbapyj:YFHJYF7tkQKBSPfA@aws-0-us-east-1.pooler.supabase.com:6543/postgres",

    # Format 2: Direct connection
    "postgresql://postgres:YFHJYF7tkQKBSPfA@db.hbtaablzueprzuwbapyj.supabase.co:5432/postgres",

    # Format 3: Transaction pooler
    "postgresql://postgres.hbtaablzueprzuwbapyj:YFHJYF7tkQKBSPfA@aws-0-us-east-1.pooler.supabase.com:5432/postgres",

    # Format 4: Direct with different host
    "postgresql://postgres:YFHJYF7tkQKBSPfA@aws-0-us-east-1.pooler.supabase.com:5432/postgres",
]

async def test_connection(url, index):
    """Test a connection URL"""
    try:
        import asyncpg
        print(f"\n[{index}] Testing: {url[:60]}...")
        conn = await asyncpg.connect(url, timeout=10)

        # Test query
        result = await conn.fetchval("SELECT version()")
        print(f"  ✅ SUCCESS! PostgreSQL version: {result[:50]}...")

        # Get table count
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        print(f"  ✅ Found {table_count} tables")

        await conn.close()
        return url

    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
        return None

async def main():
    print("=" * 70)
    print("Testing Supabase Connection Formats")
    print("=" * 70)

    working_url = None
    for i, url in enumerate(formats, 1):
        result = await test_connection(url, i)
        if result:
            working_url = result
            break

    if working_url:
        print("\n" + "=" * 70)
        print("✅ WORKING CONNECTION STRING:")
        print("=" * 70)
        print(working_url)
        print("\nUpdate your .env file with this URL!")
    else:
        print("\n" + "=" * 70)
        print("❌ None of the formats worked")
        print("=" * 70)
        print("\nPlease check:")
        print("1. Password is correct")
        print("2. Project ref is: hbtaablzueprzuwbapyj")
        print("3. Database is accessible")

if __name__ == "__main__":
    asyncio.run(main())
