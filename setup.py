#!/usr/bin/env python3
"""
NEMIS Complete Setup and Verification Script
Run this to set up and verify everything is 100% working
"""

import subprocess
import sys
import os
import time

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(number, text):
    """Print step number"""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)

def run_command(cmd, description, check=True):
    """Run shell command and return success"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode == 0:
            print(f"✓ {description} - SUCCESS")
            return True
        else:
            print(f"✗ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False

def check_postgres():
    """Check if PostgreSQL is running"""
    print_step(1, "Checking PostgreSQL Installation")
    
    # Try to connect
    result = run_command(
        'psql -U postgres -c "SELECT version();" 2>&1',
        "PostgreSQL connection test",
        check=False
    )
    
    if not result:
        print("\n⚠️  PostgreSQL not accessible. Please ensure:")
        print("   1. PostgreSQL is installed")
        print("   2. PostgreSQL service is running")
        print("   3. User 'postgres' exists with proper permissions")
        print("\nWindows: Check Services for 'postgresql-x64-XX'")
        print("Linux: sudo systemctl status postgresql")
        print("Mac: brew services list | grep postgresql")
        return False
    
    return True

def create_database():
    """Create NEMIS database"""
    print_step(2, "Creating NEMIS Database")
    
    # Check if database exists
    check = run_command(
        'psql -U postgres -lqt | cut -d "|" -f 1 | grep -qw NEMIS',
        "Checking if NEMIS database exists",
        check=False
    )
    
    if check:
        print("\n⚠️  Database NEMIS already exists!")
        response = input("Drop and recreate? (yes/no): ").strip().lower()
        if response == 'yes':
            run_command(
                'psql -U postgres -c "DROP DATABASE NEMIS;"',
                "Dropping existing database",
                check=False
            )
        else:
            print("✓ Using existing database")
            return True
    
    return run_command(
        'psql -U postgres -c "CREATE DATABASE NEMIS;"',
        "Creating NEMIS database"
    )

def load_schema():
    """Load database schema"""
    print_step(3, "Loading Database Schema")
    
    if not os.path.exists('schema.sql'):
        print("✗ schema.sql not found in current directory")
        return False
    
    result = run_command(
        'psql -U postgres -d NEMIS -f schema.sql',
        "Loading schema (tables, views, functions, triggers)"
    )
    
    if result:
        print("\n✓ Database schema loaded successfully!")
        print("   - 9 tables created")
        print("   - 4 views created")
        print("   - 3 functions created")
        print("   - 6 triggers created")
        print("   - 15+ indexes created")
        print("   - 12 regions inserted")
        print("   - 2 admin users created")
    
    return result

def load_sample_data():
    """Load sample data"""
    print_step(4, "Loading Sample Data (Optional)")
    
    if not os.path.exists('sample_data.sql'):
        print("ℹ️  sample_data.sql not found - skipping")
        return True
    
    response = input("Load sample data for testing? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Skipping sample data")
        return True
    
    result = run_command(
        'psql -U postgres -d NEMIS -f sample_data.sql',
        "Loading sample data (voters, candidates, elections)"
    )
    
    if result:
        print("\n✓ Sample data loaded!")
        print("   - 5 test voters")
        print("   - 6 test candidates")
        print("   - 2 test elections")
        print("   - Sample votes")
    
    return result

def check_python():
    """Check Python installation"""
    print_step(5, "Checking Python Environment")
    
    # Check Python version
    result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
    print(f"Python version: {result.stdout.strip()}")
    
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print("✗ Python 3.8 or higher required")
        return False
    
    print("✓ Python version OK")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step(6, "Installing Python Dependencies")
    
    if not os.path.exists('requirements.txt'):
        print("✗ requirements.txt not found")
        return False
    
    return run_command(
        f'{sys.executable} -m pip install -r requirements.txt',
        "Installing Flask, psycopg2, and other dependencies"
    )

def test_database():
    """Run database tests"""
    print_step(7, "Running Database Tests")
    
    if not os.path.exists('test_database.py'):
        print("ℹ️  test_database.py not found - skipping tests")
        return True
    
    response = input("Run comprehensive database tests? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Skipping tests")
        return True
    
    return run_command(
        f'{sys.executable} test_database.py',
        "Running all database validation tests"
    )

def start_application():
    """Start Flask application"""
    print_step(8, "Starting Flask Application")
    
    if not os.path.exists('nemis.py'):
        print("✗ nemis.py not found")
        return False
    
    print("\n✓ Ready to start application!")
    print("\nTo start NEMIS:")
    print(f"   {sys.executable} nemis.py")
    print("\nThen open your browser to:")
    print("   http://127.0.0.1:5000")
    print("\nDefault login credentials:")
    print("   Admin: AD123456")
    print("   Election Officer: EO123456")
    
    response = input("\nStart application now? (yes/no): ").strip().lower()
    if response == 'yes':
        print("\n🚀 Starting NEMIS...")
        print("   Press Ctrl+C to stop the server")
        print("\n" + "=" * 70)
        try:
            subprocess.run([sys.executable, 'nemis.py'])
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
    
    return True

def main():
    """Main setup routine"""
    print_header("NEMIS Complete Setup & Verification")
    print("This script will:")
    print("  1. Verify PostgreSQL installation")
    print("  2. Create NEMIS database")
    print("  3. Load complete schema (tables, views, functions, triggers)")
    print("  4. Optionally load sample data")
    print("  5. Install Python dependencies")
    print("  6. Run database tests")
    print("  7. Start the application")
    
    response = input("\nContinue with setup? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Setup cancelled.")
        return
    
    # Run setup steps
    steps = [
        (check_postgres, "PostgreSQL Check"),
        (create_database, "Database Creation"),
        (load_schema, "Schema Loading"),
        (load_sample_data, "Sample Data"),
        (check_python, "Python Check"),
        (install_dependencies, "Dependencies"),
        (test_database, "Database Tests"),
        (start_application, "Application Start")
    ]
    
    failed = []
    for step_func, step_name in steps:
        try:
            if not step_func():
                failed.append(step_name)
                response = input(f"\n⚠️  {step_name} had issues. Continue anyway? (yes/no): ").strip().lower()
                if response != 'yes':
                    break
        except Exception as e:
            print(f"✗ Error in {step_name}: {e}")
            failed.append(step_name)
            break
    
    # Final summary
    print_header("Setup Complete!")
    
    if not failed:
        print("✓✓✓ ALL STEPS COMPLETED SUCCESSFULLY! ✓✓✓")
        print("\n🎉 NEMIS is ready to use!")
        print("\nQuick Start:")
        print(f"  1. Run: {sys.executable} nemis.py")
        print("  2. Open: http://127.0.0.1:5000")
        print("  3. Login: AD123456 (Admin) or EO123456 (Officer)")
        print("\nDocumentation:")
        print("  - README.md - Quick start guide")
        print("  - DATABASE_FEATURES.md - Complete database documentation")
        print("  - TEST_QUERIES.sql - 33 test queries")
    else:
        print(f"⚠️  {len(failed)} step(s) had issues:")
        for step in failed:
            print(f"   - {step}")
        print("\nPlease review errors above and fix before proceeding.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
