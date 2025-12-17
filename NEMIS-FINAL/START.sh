#!/bin/bash
# NEMIS Quick Start Script for Linux/Mac

echo "===================================="
echo "NEMIS Quick Start"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if PostgreSQL is accessible
if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL not accessible!"
    echo "Please ensure PostgreSQL is installed and running."
    exit 1
fi

echo "[1/5] Checking database..."
if ! psql -U postgres -lqt | cut -d \| -f 1 | grep -qw NEMIS; then
    echo "Creating NEMIS database..."
    psql -U postgres -c "CREATE DATABASE NEMIS;" || exit 1
    
    echo "Loading schema..."
    psql -U postgres -d NEMIS -f schema.sql || exit 1
    echo "Database created successfully!"
else
    echo "Database already exists."
fi

echo
echo "[2/5] Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo
echo "[3/5] Activating virtual environment..."
source .venv/bin/activate

echo
echo "[4/5] Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo
echo "[5/5] Starting NEMIS..."
echo
echo "===================================="
echo "NEMIS is starting!"
echo "===================================="
echo
echo "Access at: http://127.0.0.1:5000"
echo
echo "Default Logins:"
echo "  Admin: AD123456"
echo "  Officer: EO123456"
echo
echo "Press Ctrl+C to stop the server"
echo "===================================="
echo

python3 nemis.py
