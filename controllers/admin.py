"""
Admin Controller for NEMIS (FIXED VERSION)
Handles all admin-related operations including election management,
candidate approval, results viewing, and system administration
FIXED: require_admin() now accepts Election Officer role
"""

from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_connection
from utils import log_audit, get_election_status
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin():
    """
    Middleware to check if user is admin or election officer
    FIXED: Now accepts both Admin and Election Officer roles
    """
    if "user" not in session:
        flash("Please login to access this page", "error")
        return redirect("/login")
    
    # FIXED: Check for both Admin and Election Officer roles
    if session["user"]["role"] not in ["Admin", "Election Officer"]:
        flash("Access denied. Admin privileges required.", "error")
        return redirect("/login")
    
    return None

# Admin Dashboard
@admin_bp.route("/dashboard")
def dashboard():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM User_account WHERE role = 'Voter'")
    result = cur.fetchone()
    total_voters = result[0] if result else 0
    
    cur.execute("SELECT COUNT(*) FROM Election")
    result = cur.fetchone()
    total_elections = result[0] if result else 0
    
    cur.execute("SELECT COUNT(*) FROM Candidate")
    result = cur.fetchone()
    total_candidates = result[0] if result else 0
    
    cur.execute("SELECT COUNT(*) FROM Vote")
    result = cur.fetchone()
    total_votes = result[0] if result else 0
    
    # Get recent elections
    cur.execute("""
        SELECT Election_ID, name, type, start_date, end_date, status 
        FROM Election 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    recent_elections = cur.fetchall()
    
    cur.close()
    conn.close()
    
    log_audit("Viewed admin dashboard")
    
    return render_template("admin_dashboard.html", 
                         total_voters=total_voters,
                         total_elections=total_elections,
                         total_candidates=total_candidates,
                         total_votes=total_votes,
                         recent_elections=recent_elections)

# Election Management
@admin_bp.route("/elections")
def elections():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT e.Election_ID, e.name, e.type, e.start_date, e.end_date, 
               e.status, u.name as admin_name
        FROM Election e
        LEFT JOIN User_account u ON e.Admin_ID = u.User_ID
        ORDER BY e.created_at DESC
    """)
    elections = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_elections.html", elections=elections)

@admin_bp.route("/elections/create", methods=["GET", "POST"])
def create_election():
    check = require_admin()
    if check:
        return check
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        election_type = request.form.get("type", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        region_ids = request.form.getlist("regions")
        
        # Validation (NEW)
        if not name or not election_type or not start_date or not end_date:
            flash("All fields are required", "error")
            return redirect("/admin/elections/create")
        
        if not region_ids:
            flash("Please select at least one region", "error")
            return redirect("/admin/elections/create")
        
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Insert election
            cur.execute("""
                INSERT INTO Election (name, type, start_date, end_date, Admin_ID, status)
                VALUES (%s, %s, %s, %s, %s, 'Planned')
                RETURNING Election_ID
            """, (name, election_type, start_date, end_date, session["user"]["id"]))
            
            result = cur.fetchone()
            election_id = result[0] if result else None
            
            if not election_id:
                raise Exception("Failed to create election")
            
            # Associate regions
            for region_id in region_ids:
                cur.execute("""
                    INSERT INTO Election_Region (Election_ID, Region_ID)
                    VALUES (%s, %s)
                """, (election_id, region_id))
            
            conn.commit()
            log_audit("Created election", "Election", election_id, f"Election: {name}")
            flash(f"Election '{name}' created successfully!", "success")
            
            cur.close()
            conn.close()
            
            return redirect("/admin/elections")
            
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            flash(f"Error creating election: {str(e)}", "error")
            return redirect("/admin/elections/create")
    
    # GET - show form
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT Region_ID, name FROM Region ORDER BY name")
    regions = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("admin_create_election.html", regions=regions)

@admin_bp.route("/elections/<int:election_id>/edit", methods=["GET", "POST"])
def edit_election(election_id):
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        election_type = request.form.get("type", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        status = request.form.get("status")
        
        # Validation (NEW)
        if not name or not election_type or not start_date or not end_date or not status:
            flash("All fields are required", "error")
            return redirect(f"/admin/elections/{election_id}/edit")
        
        try:
            cur.execute("""
                UPDATE Election 
                SET name = %s, type = %s, start_date = %s, end_date = %s, status = %s
                WHERE Election_ID = %s
            """, (name, election_type, start_date, end_date, status, election_id))
            
            conn.commit()
            log_audit("Updated election", "Election", election_id, f"Election: {name}")
            flash(f"Election '{name}' updated successfully!", "success")
            
            cur.close()
            conn.close()
            
            return redirect("/admin/elections")
            
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            flash(f"Error updating election: {str(e)}", "error")
            return redirect(f"/admin/elections/{election_id}/edit")
    
    # GET - show form
    cur.execute("""
        SELECT Election_ID, name, type, start_date, end_date, status
        FROM Election WHERE Election_ID = %s
    """, (election_id,))
    election = cur.fetchone()
    
    if not election:
        cur.close()
        conn.close()
        flash("Election not found", "error")
        return redirect("/admin/elections")
    
    cur.close()
    conn.close()
    
    return render_template("admin_edit_election.html", election=election)

# Candidate Management
@admin_bp.route("/candidates")
def candidates():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.Candidate_ID, u.name, u.CNIE, c.party_name, 
               r.name as region, e.name as election, c.is_approved
        FROM Candidate c
        JOIN User_account u ON c.User_ID = u.User_ID
        JOIN Region r ON c.Region_ID = r.Region_ID
        JOIN Election e ON c.Election_ID = e.Election_ID
        ORDER BY c.registration_date DESC
    """)
    candidates = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_candidates.html", candidates=candidates)

@admin_bp.route("/candidates/<int:candidate_id>/approve", methods=["POST"])
def approve_candidate(candidate_id):
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE Candidate 
            SET is_approved = TRUE 
            WHERE Candidate_ID = %s
        """, (candidate_id,))
        
        conn.commit()
        log_audit("Approved candidate", "Candidate", candidate_id)
        flash("Candidate approved successfully!", "success")
        
    except Exception as e:
        conn.rollback()
        flash(f"Error approving candidate: {str(e)}", "error")
    
    cur.close()
    conn.close()
    
    return redirect("/admin/candidates")

@admin_bp.route("/candidates/<int:candidate_id>/reject", methods=["POST"])
def reject_candidate(candidate_id):
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE Candidate 
            SET is_approved = FALSE 
            WHERE Candidate_ID = %s
        """, (candidate_id,))
        
        conn.commit()
        log_audit("Rejected candidate", "Candidate", candidate_id)
        flash("Candidate rejected", "info")
        
    except Exception as e:
        conn.rollback()
        flash(f"Error rejecting candidate: {str(e)}", "error")
    
    cur.close()
    conn.close()
    
    return redirect("/admin/candidates")

# Results and Reporting
@admin_bp.route("/results")
def results():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all elections
    cur.execute("SELECT Election_ID, name FROM Election ORDER BY created_at DESC")
    elections = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_results.html", elections=elections)

@admin_bp.route("/results/<int:election_id>")
def election_results(election_id):
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get election info
    cur.execute("SELECT name, type, status FROM Election WHERE Election_ID = %s", (election_id,))
    election = cur.fetchone()
    
    if not election:
        cur.close()
        conn.close()
        flash("Election not found", "error")
        return redirect("/admin/results")
    
    # Get results using the view
    cur.execute("""
        SELECT candidate_name, party_name, region_name, vote_count, vote_percentage
        FROM Election_Results
        WHERE Election_ID = %s
        ORDER BY vote_count DESC
    """, (election_id,))
    results = cur.fetchall()
    
    # Get voter statistics by region
    cur.execute("""
        SELECT r.name, COUNT(DISTINCT v.Voter_ID) as voted,
               COUNT(DISTINCT vo.Voter_ID) as total
        FROM Region r
        LEFT JOIN Voter vo ON r.Region_ID = vo.Region_ID
        LEFT JOIN Vote v ON vo.Voter_ID = v.Voter_ID AND v.Election_ID = %s
        GROUP BY r.name
        ORDER BY r.name
    """, (election_id,))
    turnout = cur.fetchall()
    
    cur.close()
    conn.close()
    
    log_audit("Viewed election results", "Election", election_id)
    
    return render_template("admin_election_results.html", 
                         election=election, 
                         results=results,
                         turnout=turnout,
                         election_id=election_id)

# User Management
@admin_bp.route("/users")
def users():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT User_ID, CNIE, name, role, created_at
        FROM User_account
        ORDER BY created_at DESC
    """)
    users = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_users.html", users=users)

@admin_bp.route("/users/create", methods=["GET", "POST"])
def create_user():
    check = require_admin()
    if check:
        return check
    
    if request.method == "POST":
        cnie = request.form.get("cnie", "").strip().upper()
        name = request.form.get("name", "").strip()
        role = request.form.get("role")
        region_id = request.form.get("region_id")
        
        # Validation (ENHANCED)
        from utils import validate_cnie, validate_name
        
        if not validate_cnie(cnie):
            flash("Invalid CNIE format. Expected: AA123456", "error")
            return redirect("/admin/users/create")
        
        if not validate_name(name):
            flash("Invalid name. Must be 2-100 characters.", "error")
            return redirect("/admin/users/create")
        
        if not role:
            flash("Please select a role", "error")
            return redirect("/admin/users/create")
        
        if role == "Voter" and not region_id:
            flash("Region is required for voters", "error")
            return redirect("/admin/users/create")
        
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Check if CNIE already exists
            cur.execute("SELECT User_ID FROM User_account WHERE CNIE = %s", (cnie,))
            if cur.fetchone():
                flash(f"CNIE {cnie} already exists", "error")
                cur.close()
                conn.close()
                return redirect("/admin/users/create")
            
            # Insert user
            cur.execute("""
                INSERT INTO User_account (CNIE, name, role)
                VALUES (%s, %s, %s)
                RETURNING User_ID
            """, (cnie, name, role))
            
            result = cur.fetchone()
            user_id = result[0] if result else None
            
            if not user_id:
                raise Exception("Failed to create user")
            
            # If voter, create voter record
            if role == "Voter" and region_id:
                cur.execute("""
                    INSERT INTO Voter (User_ID, Region_ID)
                    VALUES (%s, %s)
                """, (user_id, region_id))
            
            conn.commit()
            log_audit("Created user", "User_account", user_id, f"User: {name}, Role: {role}")
            flash(f"User '{name}' created successfully with CNIE: {cnie}", "success")
            
            cur.close()
            conn.close()
            
            return redirect("/admin/users")
            
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            flash(f"Error creating user: {str(e)}", "error")
            return redirect("/admin/users/create")
    
    # GET - show form
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT Region_ID, name FROM Region ORDER BY name")
    regions = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("admin_create_user.html", regions=regions)

# Audit Log
@admin_bp.route("/audit")
def audit_log():
    check = require_admin()
    if check:
        return check
    
    # Pagination (NEW)
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get total count
    cur.execute("SELECT COUNT(*) FROM Audit_log")
    total_logs = cur.fetchone()[0]
    total_pages = (total_logs + per_page - 1) // per_page
    
    # Get paginated logs
    cur.execute("""
        SELECT a.Log_ID, u.name, u.role, a.action, a.table_name, 
               a.timestamp, a.ip_address
        FROM Audit_log a
        LEFT JOIN User_account u ON a.User_ID = u.User_ID
        ORDER BY a.timestamp DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    logs = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_audit.html", 
                         logs=logs,
                         page=page,
                         total_pages=total_pages)

# Regions Management
@admin_bp.route("/regions")
def regions():
    check = require_admin()
    if check:
        return check
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.Region_ID, r.name,
               COUNT(DISTINCT v.Voter_ID) as voter_count,
               COUNT(DISTINCT c.Candidate_ID) as candidate_count
        FROM Region r
        LEFT JOIN Voter v ON r.Region_ID = v.Region_ID
        LEFT JOIN Candidate c ON r.Region_ID = c.Region_ID
        GROUP BY r.Region_ID, r.name
        ORDER BY r.name
    """)
    regions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("admin_regions.html", regions=regions)
