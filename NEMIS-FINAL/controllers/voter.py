"""
Voter Controller for NEMIS
Handles voter-related operations including dashboard, voting, and candidate viewing
"""

from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_connection
from utils import log_audit, check_voter_eligibility, get_election_status

voter_bp = Blueprint('voter', __name__, url_prefix='/voter')

def require_voter():
    """Middleware to check if user is voter"""
    if "user" not in session or session["user"]["role"] != "Voter":
        flash("Please login as a voter to access this page", "error")
        return redirect("/login")
    return None

# Voter Dashboard
@voter_bp.route("/dashboard")
def dashboard():
    check = require_voter()
    if check:
        return check
    
    user_id = session["user"]["id"]
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get voter info including region
    cur.execute("""
        SELECT v.Voter_ID, v.Region_ID, r.name as region_name, v.is_eligible
        FROM Voter v
        JOIN Region r ON v.Region_ID = r.Region_ID
        WHERE v.User_ID = %s
    """, (user_id,))
    voter_info = cur.fetchone()
    
    if not voter_info:
        cur.close()
        conn.close()
        return "Voter registration not found. Please contact admin."
    
    voter_id, region_id, region_name, is_eligible = voter_info
    
    # Get active elections in voter's region
    cur.execute("""
        SELECT DISTINCT e.Election_ID, e.name, e.type, e.start_date, e.end_date, e.status
        FROM Election e
        JOIN Election_Region er ON e.Election_ID = er.Election_ID
        WHERE er.Region_ID = %s 
        AND e.status IN ('Active', 'Planned')
        ORDER BY e.start_date
    """, (region_id,))
    elections = cur.fetchall()
    
    # Check which elections voter has voted in
    cur.execute("""
        SELECT Election_ID FROM Vote WHERE Voter_ID = %s
    """, (voter_id,))
    voted_elections = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    log_audit("Viewed voter dashboard")
    
    return render_template("voter_dashboard.html", 
                         voter_id=voter_id,
                         region_name=region_name,
                         is_eligible=is_eligible,
                         elections=elections,
                         voted_elections=voted_elections)

# View Candidates for an Election
@voter_bp.route("/election/<int:election_id>/candidates")
def view_candidates(election_id):
    check = require_voter()
    if check:
        return check
    
    user_id = session["user"]["id"]
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get voter info
    cur.execute("SELECT Voter_ID, Region_ID FROM Voter WHERE User_ID = %s", (user_id,))
    voter_info = cur.fetchone()
    
    if not voter_info:
        cur.close()
        conn.close()
        return "Voter not found"
    
    voter_id, voter_region_id = voter_info
    
    # Check eligibility
    eligible, message = check_voter_eligibility(voter_id, election_id)
    
    # Get election info
    cur.execute("""
        SELECT name, type, start_date, end_date, status
        FROM Election WHERE Election_ID = %s
    """, (election_id,))
    election = cur.fetchone()
    
    # Get candidates for this election in voter's region
    # Business Rule #28: Candidates may only run in elections matching their region
    cur.execute("""
        SELECT c.Candidate_ID, u.name, c.party_name, c.manifesto, r.name as region
        FROM Candidate c
        JOIN User_account u ON c.User_ID = u.User_ID
        JOIN Region r ON c.Region_ID = r.Region_ID
        WHERE c.Election_ID = %s 
        AND c.Region_ID = %s
        AND c.is_approved = TRUE
        ORDER BY u.name
    """, (election_id, voter_region_id))
    candidates = cur.fetchall()
    
    # Check if already voted
    cur.execute("""
        SELECT Candidate_ID FROM Vote 
        WHERE Voter_ID = %s AND Election_ID = %s
    """, (voter_id, election_id))
    voted_for = cur.fetchone()
    
    cur.close()
    conn.close()
    
    log_audit("Viewed candidates", "Election", election_id)
    
    return render_template("voter_candidates.html",
                         election=election,
                         election_id=election_id,
                         candidates=candidates,
                         eligible=eligible,
                         message=message,
                         voted_for=voted_for[0] if voted_for else None)

# Cast Vote
@voter_bp.route("/vote", methods=["POST"])
def vote():
    check = require_voter()
    if check:
        return check
    
    candidate_id = request.form.get("candidate_id")
    election_id = request.form.get("election_id")
    user_id = session["user"]["id"]
    
    if not candidate_id or not election_id:
        return "Missing required fields"
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get voter ID
    cur.execute("SELECT Voter_ID, Region_ID FROM Voter WHERE User_ID = %s", (user_id,))
    voter_info = cur.fetchone()
    
    if not voter_info:
        cur.close()
        conn.close()
        return "Voter not found"
    
    voter_id, voter_region = voter_info
    
    # Check eligibility
    eligible, message = check_voter_eligibility(voter_id, election_id)
    
    if not eligible:
        cur.close()
        conn.close()
        return message
    
    # Verify candidate is in same region and election
    cur.execute("""
        SELECT Region_ID, Election_ID 
        FROM Candidate 
        WHERE Candidate_ID = %s AND is_approved = TRUE
    """, (candidate_id,))
    candidate_info = cur.fetchone()
    
    if not candidate_info:
        cur.close()
        conn.close()
        return "Invalid candidate"
    
    candidate_region, candidate_election = candidate_info
    
    # Business Rule #27 & #28: Region validation
    if candidate_region != voter_region:
        cur.close()
        conn.close()
        return "Cannot vote for candidate from different region"
    
    if candidate_election != int(election_id):
        cur.close()
        conn.close()
        return "Candidate not in this election"
    
    # Check election status
    election_status = get_election_status(election_id)
    if election_status != "Active":
        cur.close()
        conn.close()
        return f"Election is not active (Status: {election_status})"
    
    try:
        # Business Rule #17 & #18: Cast vote (immutable)
        cur.execute("""
            INSERT INTO Vote (Voter_ID, Election_ID, Candidate_ID)
            VALUES (%s, %s, %s)
        """, (voter_id, election_id, candidate_id))
        
        conn.commit()
        
        log_audit("Cast vote", "Vote", None, f"Election: {election_id}, Candidate: {candidate_id}")
        
        cur.close()
        conn.close()
        
        return redirect(f"/voter/vote/success?election_id={election_id}")
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return f"Error casting vote: {str(e)}"

# Vote Success Page
@voter_bp.route("/vote/success")
def vote_success():
    check = require_voter()
    if check:
        return check
    
    election_id = request.args.get("election_id")
    
    return render_template("voter_vote_success.html", election_id=election_id)

# View Voting History
@voter_bp.route("/history")
def voting_history():
    check = require_voter()
    if check:
        return check
    
    user_id = session["user"]["id"]
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get voter ID
    cur.execute("SELECT Voter_ID FROM Voter WHERE User_ID = %s", (user_id,))
    voter = cur.fetchone()
    
    if not voter:
        cur.close()
        conn.close()
        return "Voter not found"
    
    voter_id = voter[0]
    
    # Get voting history
    cur.execute("""
        SELECT e.name as election_name, e.type, v.vote_timestamp,
               u.name as candidate_name, c.party_name
        FROM Vote v
        JOIN Election e ON v.Election_ID = e.Election_ID
        JOIN Candidate c ON v.Candidate_ID = c.Candidate_ID
        JOIN User_account u ON c.User_ID = u.User_ID
        WHERE v.Voter_ID = %s
        ORDER BY v.vote_timestamp DESC
    """, (voter_id,))
    history = cur.fetchall()
    
    cur.close()
    conn.close()
    
    log_audit("Viewed voting history")
    
    return render_template("voter_history.html", history=history)
