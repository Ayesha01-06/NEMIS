"""
Utility functions for NEMIS (ENHANCED VERSION)
Including audit logging, validation, and helper functions
"""

from db import get_connection
from datetime import datetime
from flask import request, session
import re

# ============================================================
# AUDIT LOGGING
# ============================================================

def log_audit(action, table_name=None, record_id=None, details=None):
    """
    Log an audit entry for significant actions
    Business Rule #23-25: All significant actions must be recorded and immutable
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        user_id = session.get("user", {}).get("id") if "user" in session else None
        ip_address = request.remote_addr if request else None
        
        cur.execute("""
            INSERT INTO Audit_log (User_ID, action, table_name, record_id, ip_address, details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, action, table_name, record_id, ip_address, details))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

# ============================================================
# VALIDATION FUNCTIONS (NEW)
# ============================================================

def validate_cnie(cnie):
    """
    Validate CNIE format
    Expected format: 2 uppercase letters followed by 6 digits (e.g., AD123456)
    """
    if not cnie or not isinstance(cnie, str):
        return False
    
    pattern = r'^[A-Z]{2}\d{6}$'
    return bool(re.match(pattern, cnie.strip()))

def validate_name(name):
    """
    Validate name format
    Must be 2-100 characters, containing letters and spaces
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    if len(name) < 2 or len(name) > 100:
        return False
    
    # Allow letters (including accented), spaces, hyphens, and apostrophes
    pattern = r'^[a-zA-ZÀ-ÿ\s\'-]+$'
    return bool(re.match(pattern, name))

def validate_email(email):
    """
    Validate email format
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_date_range(start_date, end_date):
    """
    Validate that start_date is before end_date
    """
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        return start_date < end_date
    except:
        return False

def sanitize_input(text, max_length=None):
    """
    Sanitize user input by removing potentially dangerous characters
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Apply max length if specified
    if max_length:
        text = text[:max_length]
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    return text

# ============================================================
# USER & REGION HELPERS
# ============================================================

def get_user_region(user_id):
    """
    Get the region of a voter
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT Region_ID FROM Voter WHERE User_ID = %s", (user_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result[0] if result else None

def get_user_info(user_id):
    """
    Get complete user information
    Returns: (user_id, cnie, name, role, created_at) or None
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT User_ID, CNIE, name, role, created_at
        FROM User_account
        WHERE User_ID = %s
    """, (user_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result

def get_region_name(region_id):
    """
    Get region name by ID
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM Region WHERE Region_ID = %s", (region_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result[0] if result else None

# ============================================================
# VOTER ELIGIBILITY
# ============================================================

def check_voter_eligibility(voter_id, election_id):
    """
    Check if a voter is eligible to vote in an election
    Business Rule #27: Voters cannot vote in elections outside their region
    Returns: (is_eligible: bool, message: str)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get voter's region
    cur.execute("SELECT Region_ID, is_eligible FROM Voter WHERE Voter_ID = %s", (voter_id,))
    voter_info = cur.fetchone()
    
    if not voter_info:
        cur.close()
        conn.close()
        return False, "Voter not found"
    
    voter_region, is_eligible_status = voter_info
    
    # Check if voter is marked as eligible
    if not is_eligible_status:
        cur.close()
        conn.close()
        return False, "Voter account is not eligible"
    
    # Check if election is available in voter's region
    cur.execute("""
        SELECT COUNT(*) FROM Election_Region 
        WHERE Election_ID = %s AND Region_ID = %s
    """, (election_id, voter_region))
    
    result = cur.fetchone()
    is_in_region = result[0] > 0 if result else False
    
    # Check if voter already voted
    cur.execute("""
        SELECT COUNT(*) FROM Vote 
        WHERE Voter_ID = %s AND Election_ID = %s
    """, (voter_id, election_id))
    
    result = cur.fetchone()
    already_voted = result[0] > 0 if result else False
    
    cur.close()
    conn.close()
    
    if already_voted:
        return False, "You have already voted in this election"
    
    if not is_in_region:
        return False, "This election is not available in your region"
    
    return True, "Eligible to vote"

# ============================================================
# ELECTION STATUS
# ============================================================

def get_election_status(election_id):
    """
    Get the current status of an election
    Auto-updates status based on current date/time
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT status, start_date, end_date 
        FROM Election 
        WHERE Election_ID = %s
    """, (election_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result:
        return None
    
    status, start_date, end_date = result
    now = datetime.now()
    
    # Auto-determine status based on dates if status is Planned or Active
    if status in ['Planned', 'Active']:
        if now < start_date:
            return "Planned"
        elif start_date <= now <= end_date:
            return "Active"
        elif now > end_date:
            return "Completed"
    
    # Return status as-is for Cancelled or already Completed
    return status

def is_election_active(election_id):
    """
    Check if an election is currently active
    """
    return get_election_status(election_id) == "Active"

# ============================================================
# FORMATTING HELPERS
# ============================================================

def format_percentage(value, total):
    """
    Format a percentage value
    """
    if total == 0:
        return "0.00%"
    return f"{(value / total * 100):.2f}%"

def format_datetime(dt, format_str="%Y-%m-%d %H:%M"):
    """
    Format a datetime object or string
    """
    if dt is None:
        return "N/A"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    
    return dt.strftime(format_str)

def format_date(dt, format_str="%Y-%m-%d"):
    """
    Format a date object or string
    """
    return format_datetime(dt, format_str)

# ============================================================
# STATISTICS & REPORTING
# ============================================================

def get_election_statistics(election_id):
    """
    Get comprehensive statistics for an election
    Returns: dict with total_votes, total_voters, turnout_percentage, etc.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get total votes
    cur.execute("SELECT COUNT(*) FROM Vote WHERE Election_ID = %s", (election_id,))
    total_votes = cur.fetchone()[0]
    
    # Get number of eligible voters for this election (voters in election regions)
    cur.execute("""
        SELECT COUNT(DISTINCT v.Voter_ID)
        FROM Voter v
        JOIN Election_Region er ON v.Region_ID = er.Region_ID
        WHERE er.Election_ID = %s AND v.is_eligible = TRUE
    """, (election_id,))
    total_eligible_voters = cur.fetchone()[0]
    
    # Get number of candidates
    cur.execute("""
        SELECT COUNT(*) FROM Candidate 
        WHERE Election_ID = %s AND is_approved = TRUE
    """, (election_id,))
    total_candidates = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    turnout_percentage = format_percentage(total_votes, total_eligible_voters) if total_eligible_voters > 0 else "0.00%"
    
    return {
        'total_votes': total_votes,
        'total_eligible_voters': total_eligible_voters,
        'total_candidates': total_candidates,
        'turnout_percentage': turnout_percentage
    }

# ============================================================
# ERROR MESSAGES
# ============================================================

ERROR_MESSAGES = {
    'invalid_cnie': 'Invalid CNIE format. Expected: 2 letters + 6 digits (e.g., AD123456)',
    'invalid_name': 'Name must be 2-100 characters and contain only letters',
    'invalid_email': 'Invalid email format',
    'invalid_dates': 'End date must be after start date',
    'already_voted': 'You have already voted in this election',
    'not_eligible': 'You are not eligible to vote in this election',
    'election_not_active': 'This election is not currently active',
    'region_mismatch': 'Election not available in your region',
    'unauthorized': 'You do not have permission to perform this action',
    'not_authenticated': 'Please login to continue'
}

def get_error_message(error_key, default="An error occurred"):
    """
    Get a user-friendly error message by key
    """
    return ERROR_MESSAGES.get(error_key, default)
