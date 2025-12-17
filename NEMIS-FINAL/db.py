"""
Database connection module for NEMIS
FIXED: Corrected database name to match schema
"""
import psycopg2
import os

def get_connection():
    """
    Create and return a connection to the NEMIS database
    Uses environment variables if available, falls back to defaults
    """
    return psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'NEMIS'),  # FIXED: Changed from 'nemis' to 'NEMIS'
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )

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
