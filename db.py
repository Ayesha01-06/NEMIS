"""
Database connection module for NEMIS
FIXED: Corrected database name to match schema
"""
import psycopg2
import os
import sys

def get_connection():
    """
    Create and return a connection to the NEMIS database
    Uses environment variables if available, falls back to defaults
    """
    try:
        return psycopg2.connect(
            dbname=os.environ.get('DB_NAME', 'NEMIS'),  # FIXED: Changed from 'nemis' to 'NEMIS'
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432')
        )
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print("\n" + "="*70)
        print("❌ DATABASE CONNECTION FAILED")
        print("="*70)

        if "password authentication failed" in error_msg:
            print("\n🔐 ISSUE: PostgreSQL password is incorrect!")
            print("\nSOLUTIONS:")
            print("  1. Create a .env file with your password:")
            print("     DB_PASSWORD=your_actual_password")
            print("\n  2. Or edit db.py line 16 with your password")
            print("\n  3. Reset PostgreSQL password in pgAdmin")
            print("\n  Current settings:")
            print(f"     Database: {os.environ.get('DB_NAME', 'NEMIS')}")
            print(f"     User: {os.environ.get('DB_USER', 'postgres')}")
            print(f"     Host: {os.environ.get('DB_HOST', 'localhost')}")
            print(f"     Port: {os.environ.get('DB_PORT', '5432')}")
        elif "database" in error_msg and "does not exist" in error_msg:
            print("\n📊 ISSUE: Database 'NEMIS' does not exist!")
            print("\nSOLUTION:")
            print('  Run: python setup.py')
            print('  Or manually: psql -U postgres -c "CREATE DATABASE \\"NEMIS\\";"')
        elif "could not connect to server" in error_msg:
            print("\n🔴 ISSUE: PostgreSQL server is not running!")
            print("\nSOLUTION:")
            print("  Windows: Start PostgreSQL service in Windows Services")
            print("  Linux: sudo systemctl start postgresql")
            print("  Mac: brew services start postgresql")
        else:
            print(f"\n❓ ERROR: {error_msg}")

        print("\n" + "="*70)
        raise

def test_connection():
    """
    Test the database connection
    Returns True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection when run directly
    if test_connection():
        print("✓ Database connection successful!")
    else:
        print("✗ Database connection failed!")
