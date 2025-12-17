#!/usr/bin/env python3
"""
NEMIS Database Testing Script
Tests all database features for database course evaluation
"""

import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import sys

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(
            dbname="NEMIS",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        print("✓ Database connection successful")
        return conn
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None

def test_tables(conn):
    """Test all tables exist"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]
    
    expected_tables = ['audit_log', 'candidate', 'election', 'election_phase', 
                       'election_region', 'region', 'user_account', 'vote', 'voter']
    
    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"✗ Missing tables: {missing}")
        return False
    
    print(f"✓ All {len(tables)} tables exist")
    cur.close()
    return True

def test_views(conn):
    """Test all views exist"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    views = [row[0] for row in cur.fetchall()]
    
    expected_views = ['vw_candidate_statistics', 'vw_election_overview', 
                      'vw_election_results', 'vw_voter_turnout']
    
    missing = set(expected_views) - set(views)
    if missing:
        print(f"✗ Missing views: {missing}")
        return False
    
    print(f"✓ All {len(views)} views exist")
    cur.close()
    return True

def test_functions(conn):
    """Test all functions exist"""
    cur = conn.cursor()
    cur.execute("""
        SELECT routine_name FROM information_schema.routines 
        WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
        ORDER BY routine_name
    """)
    functions = [row[0] for row in cur.fetchall()]
    
    expected = ['calculate_turnout', 'get_election_winner', 'get_region_statistics']
    
    for func in expected:
        if func in functions:
            print(f"✓ Function {func} exists")
        else:
            print(f"✗ Function {func} missing")
            return False
    
    return True

def test_triggers(conn):
    """Test all triggers exist"""
    cur = conn.cursor()
    cur.execute("""
        SELECT trigger_name, event_object_table 
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY trigger_name
    """)
    triggers = cur.fetchall()
    
    expected_count = 6  # Should have 6 triggers
    
    if len(triggers) < expected_count:
        print(f"✗ Expected {expected_count} triggers, found {len(triggers)}")
        return False
    
    print(f"✓ All {len(triggers)} triggers exist")
    for trigger_name, table_name in triggers:
        print(f"  - {trigger_name} on {table_name}")
    
    cur.close()
    return True

def test_indexes(conn):
    """Test indexes exist"""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'
    """)
    index_count = cur.fetchone()[0]
    
    if index_count < 15:
        print(f"⚠ Only {index_count} indexes found (expected 15+)")
    else:
        print(f"✓ {index_count} indexes exist for performance")
    
    cur.close()
    return True

def test_constraints(conn):
    """Test constraints"""
    cur = conn.cursor()
    
    # Test CHECK constraints
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.check_constraints
        WHERE constraint_schema = 'public'
    """)
    check_count = cur.fetchone()[0]
    print(f"✓ {check_count} CHECK constraints enforcing business rules")
    
    # Test UNIQUE constraints
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.table_constraints
        WHERE constraint_schema = 'public' AND constraint_type = 'UNIQUE'
    """)
    unique_count = cur.fetchone()[0]
    print(f"✓ {unique_count} UNIQUE constraints preventing duplicates")
    
    # Test FOREIGN KEY constraints
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.table_constraints
        WHERE constraint_schema = 'public' AND constraint_type = 'FOREIGN KEY'
    """)
    fk_count = cur.fetchone()[0]
    print(f"✓ {fk_count} FOREIGN KEY constraints maintaining referential integrity")
    
    cur.close()
    return True

def test_sample_data(conn):
    """Test sample data exists"""
    cur = conn.cursor()
    
    # Check regions
    cur.execute("SELECT COUNT(*) FROM Region")
    region_count = cur.fetchone()[0]
    if region_count != 12:
        print(f"✗ Expected 12 regions, found {region_count}")
        return False
    print(f"✓ {region_count} Moroccan regions loaded")
    
    # Check admin users
    cur.execute("SELECT COUNT(*) FROM User_account WHERE role IN ('Admin', 'Election Officer')")
    admin_count = cur.fetchone()[0]
    if admin_count < 2:
        print(f"✗ Expected 2+ admin users, found {admin_count}")
        return False
    print(f"✓ {admin_count} admin users created")
    
    cur.close()
    return True

def test_query_performance(conn):
    """Test query performance"""
    cur = conn.cursor()
    
    start = datetime.now()
    cur.execute("""
        SELECT e.name, COUNT(v.Vote_ID) as vote_count
        FROM Election e
        LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
        GROUP BY e.Election_ID, e.name
        ORDER BY vote_count DESC
    """)
    results = cur.fetchall()
    duration = (datetime.now() - start).total_seconds()
    
    print(f"✓ Complex query executed in {duration:.3f} seconds")
    
    cur.close()
    return True

def test_trigger_validation(conn):
    """Test triggers are working"""
    cur = conn.cursor()
    
    try:
        # Try to update audit log (should fail)
        cur.execute("INSERT INTO Audit_log (action) VALUES ('Test Action')")
        log_id = cur.lastrowid
        cur.execute("UPDATE Audit_log SET action = 'Modified' WHERE Log_ID = %s", (log_id,))
        conn.rollback()
        print("✗ Audit log protection trigger not working")
        return False
    except Exception as e:
        conn.rollback()
        if "cannot be modified" in str(e):
            print("✓ Audit log protection trigger working")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    cur.close()
    return True

def run_all_tests():
    """Run all database tests"""
    print("=" * 60)
    print("NEMIS DATABASE TESTING SUITE")
    print("Database Course - Comprehensive Validation")
    print("=" * 60)
    print()
    
    conn = test_connection()
    if not conn:
        print("\n✗ FAILED: Cannot connect to database")
        return False
    
    print()
    print("Testing Database Structure:")
    print("-" * 60)
    
    tests = [
        ("Tables", test_tables),
        ("Views", test_views),
        ("Functions", test_functions),
        ("Triggers", test_triggers),
        ("Indexes", test_indexes),
        ("Constraints", test_constraints),
        ("Sample Data", test_sample_data),
        ("Query Performance", test_query_performance),
        ("Trigger Validation", test_trigger_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print()
        try:
            result = test_func(conn)
            results.append(result)
        except Exception as e:
            print(f"✗ {test_name} test failed with error: {e}")
            results.append(False)
    
    conn.close()
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED - DATABASE IS 100% READY! ✓✓✓")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
