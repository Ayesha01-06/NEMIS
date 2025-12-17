"""
Authentication Controller for NEMIS (FIXED VERSION)
Handles login, logout, and user authentication
FIXED: Added flash messages, better error handling, input validation
"""

from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_connection
from utils import log_audit, validate_cnie

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
def index():
    """Redirect to login page"""
    return redirect("/login")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login
    Business Rule #1: Each user has a unique ID and CNIE
    Business Rule #2: Every user has exactly one role
    """
    if request.method == "POST":
        cnie = request.form.get("CNIE", "").strip().upper()
        
        if not cnie:
            flash("CNIE is required", "error")
            return render_template("login.html")
        
        if not validate_cnie(cnie):
            flash("Invalid CNIE format. Expected: AA123456", "error")
            return render_template("login.html")
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Business Rule #26: CNIE must be unique for all users
        cur.execute("SELECT User_ID, CNIE, name, role FROM User_account WHERE CNIE = %s", (cnie,))
        user = cur.fetchone()
        
        if user is None:
            cur.close()
            conn.close()
            log_audit(f"Failed login attempt", details=f"CNIE: {cnie}")
            flash("User not found. Please check your CNIE.", "error")
            return render_template("login.html")
        
        # Save user in session
        session["user"] = {
            "id": user[0],
            "cnie": user[1],
            "name": user[2],
            "role": user[3]
        }
        
        # Business Rule #3-5: Auto-register voter in Voter table if role = Voter
        if session["user"]["role"] == "Voter":
            cur.execute("SELECT Voter_ID, Region_ID FROM Voter WHERE User_ID = %s", (user[0],))
            voter = cur.fetchone()
            
            if voter is None:
                # New voter - needs to be assigned a region by admin
                # For now, assign default region (1)
                try:
                    cur.execute("""
                        INSERT INTO Voter (User_ID, Region_ID)
                        VALUES (%s, %s)
                    """, (user[0], 1))
                    conn.commit()
                    log_audit("Auto-registered new voter", "Voter", user[0])
                except Exception as e:
                    conn.rollback()
                    cur.close()
                    conn.close()
                    flash(f"Error registering voter: {str(e)}", "error")
                    return render_template("login.html")
        
        cur.close()
        conn.close()
        
        log_audit(f"Successful login", details=f"Role: {session['user']['role']}")
        
        # Redirect based on role
        if session["user"]["role"] == "Voter":
            return redirect("/voter/dashboard")
        elif session["user"]["role"] == "Admin":
            return redirect("/admin/dashboard")
        elif session["user"]["role"] == "Election Officer":
            return redirect("/admin/dashboard")  # Officers use admin interface
        else:
            flash("Unsupported role", "error")
            return render_template("login.html")
    
    # GET request - show login form
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """Handle user logout"""
    if "user" in session:
        log_audit(f"User logged out", details=f"User: {session['user']['name']}")
        session.pop("user", None)
    
    return redirect("/login")

@auth_bp.route("/profile")
def profile():
    """View user profile"""
    if "user" not in session:
        return redirect("/login")
    
    user_id = session["user"]["id"]
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT User_ID, CNIE, name, role, created_at
        FROM User_account WHERE User_ID = %s
    """, (user_id,))
    user_info = cur.fetchone()
    
    # If voter, get additional info
    voter_info = None
    if session["user"]["role"] == "Voter":
        cur.execute("""
            SELECT v.Voter_ID, r.name as region_name, v.registration_date, v.is_eligible
            FROM Voter v
            JOIN Region r ON v.Region_ID = r.Region_ID
            WHERE v.User_ID = %s
        """, (user_id,))
        voter_info = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return render_template("profile.html", user=user_info, voter=voter_info)
