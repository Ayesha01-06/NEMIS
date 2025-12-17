#!/usr/bin/env python3
"""
Quick database setup script for Windows troubleshooting
Loads schema directly through psycopg2 instead of psql command
"""

import psycopg2
import sys
import os

def load_schema_direct():
    """Load schema directly using psycopg2"""
    print("=" * 60)
    print("NEMIS Database Setup - Direct Method")
    print("=" * 60)
    print()

    # Check if schema.sql exists
    if not os.path.exists('schema.sql'):
        print("✗ schema.sql not found!")
        print("  Make sure you're in the NEMIS directory")
        return False

    # Read schema file
    print("[1/3] Reading schema.sql...")
    try:
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        print(f"✓ Schema file loaded ({len(schema_sql)} characters)")
    except Exception as e:
        print(f"✗ Error reading schema.sql: {e}")
        return False

    # Connect to PostgreSQL
    print()
    print("[2/3] Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            dbname='NEMIS',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        print("✓ Connected to NEMIS database")
    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Create the database: psql -U postgres -c \"CREATE DATABASE NEMIS;\"")
        print("  3. Check if password is correct (default: postgres)")
        return False

    # Execute schema
    print()
    print("[3/3] Loading schema into database...")
    try:
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Schema loaded successfully!")
        print()
        print("Database setup complete! You should now have:")
        print("  ✓ 9 tables created")
        print("  ✓ 12 regions inserted")
        print("  ✓ 2 admin users created (AD123456, EO123456)")
        print("  ✓ 4 views created")
        print("  ✓ 9 functions created")
        print("  ✓ 7 triggers created")
        print()
        print("Next step: python nemis.py")
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"✗ Error loading schema: {e}")
        print()
        print("This usually means:")
        print("  1. Database already has tables (drop and recreate NEMIS database)")
        print("  2. SQL syntax error (check schema.sql)")
        return False

if __name__ == "__main__":
    success = load_schema_direct()
    sys.exit(0 if success else 1)
