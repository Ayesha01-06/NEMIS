# NEMIS Installation Verification Checklist

## ✅ Pre-Installation Checks

### System Requirements
- [ ] Python 3.8+ installed (`python --version`)
- [ ] PostgreSQL 12+ installed and running
- [ ] pip installed (`pip --version`)
- [ ] Git installed (optional, for cloning)

## ✅ Installation Steps

### Step 1: Database Setup
- [ ] PostgreSQL is running
- [ ] Created NEMIS database
- [ ] Loaded schema.sql without errors
- [ ] Verified 12 regions were inserted
- [ ] Verified 2 default users were created
- [ ] All 5 triggers created successfully

### Step 2: Python Environment
- [ ] Created virtual environment (.venv)
- [ ] Activated virtual environment
- [ ] Installed all requirements without errors
- [ ] flask-wtf installed (for CSRF)
- [ ] psycopg2-binary installed
- [ ] No dependency conflicts

### Step 3: Configuration
- [ ] Copied .env.example to .env (optional)
- [ ] Updated SECRET_KEY if using .env
- [ ] Verified database credentials
- [ ] Checked DB_NAME is "NEMIS" (uppercase)

### Step 4: File Structure
- [ ] static/css/style.css exists
- [ ] static/js/main.js exists
- [ ] static/images/ directory exists
- [ ] All templates present (no vote.html)
- [ ] controllers/ directory has 3 files
- [ ] No admin_dashborad.html (typo file removed)

## ✅ Application Startup

### Starting the Application
- [ ] Run `python nemis.py`
- [ ] No error messages
- [ ] Server starts on http://127.0.0.1:5000
- [ ] See startup banner with "NEMIS" title

## ✅ Functional Testing

### Test 1: Login Page
- [ ] Navigate to http://127.0.0.1:5000
- [ ] Login page displays correctly
- [ ] CSS styling is visible
- [ ] NEMIS logo appears
- [ ] Default users mentioned (AD123456, EO123456)

### Test 2: Admin Login
- [ ] Enter CNIE: AD123456
- [ ] Click Login
- [ ] Redirects to /admin/dashboard
- [ ] Dashboard shows statistics
- [ ] Navigation menu appears
- [ ] No error messages

### Test 3: Election Officer Login
- [ ] Logout
- [ ] Enter CNIE: EO123456
- [ ] Click Login
- [ ] Redirects to /admin/dashboard (FIXED!)
- [ ] Can access all admin functions
- [ ] No "Access Denied" errors

### Test 4: CSRF Protection
- [ ] View page source on any form
- [ ] Find `<input type="hidden" name="csrf_token"`
- [ ] Token value is present
- [ ] Try submitting form without CSRF = 400 error

### Test 5: Create Election
- [ ] Login as Admin
- [ ] Navigate to Elections → Create New Election
- [ ] Fill in all fields:
  - [ ] Name
  - [ ] Type
  - [ ] Start date
  - [ ] End date
  - [ ] Select at least one region
- [ ] Submit form
- [ ] Success flash message appears
- [ ] Election appears in elections list

### Test 6: Create User
- [ ] Navigate to Users → Create New User
- [ ] Enter CNIE (e.g., VT123456)
- [ ] Enter name
- [ ] Select role: Voter
- [ ] Select region
- [ ] Submit
- [ ] Success flash message
- [ ] User appears in users list

### Test 7: Voter Login
- [ ] Logout
- [ ] Login with created voter CNIE
- [ ] Redirects to /voter/dashboard
- [ ] Shows elections in voter's region
- [ ] Voter navigation menu appears

### Test 8: View Candidates
- [ ] As voter, click on an election
- [ ] Candidates page loads
- [ ] No errors if no candidates yet
- [ ] Back button works

### Test 9: Database Triggers
- [ ] Try to update audit log (should fail)
  ```sql
  UPDATE Audit_log SET action = 'test' WHERE Log_ID = 1;
  ```
- [ ] Should get error: "cannot be modified or deleted"

### Test 10: Error Pages
- [ ] Navigate to http://127.0.0.1:5000/nonexistent
- [ ] Should show 404 page with styling
- [ ] "Go to Home" button works

### Test 11: Flash Messages
- [ ] Perform any action (create user, etc.)
- [ ] Flash message appears
- [ ] Message auto-dismisses after 5 seconds
- [ ] Close button (×) works

### Test 12: Confirmation Dialogs
- [ ] Go to admin/candidates
- [ ] Click "Approve" or "Reject"
- [ ] Confirmation dialog appears
- [ ] Can cancel or confirm

### Test 13: Input Validation
- [ ] Try creating user with invalid CNIE (e.g., "123")
- [ ] Should show error: "Invalid CNIE format"
- [ ] Form does not submit

### Test 14: Session Timeout
- [ ] Login
- [ ] Wait 2+ hours (or change timeout in nemis.py to 1 minute for testing)
- [ ] Try to access page
- [ ] Should redirect to login

## ✅ Security Checks

### CSRF Protection
- [ ] All forms have CSRF tokens
- [ ] Cannot submit without valid token
- [ ] Token changes on each page load

### Session Security
- [ ] Sessions expire after timeout
- [ ] Logout clears session
- [ ] Cannot access protected pages without login

### Input Validation
- [ ] CNIE format validated (2 letters + 6 digits)
- [ ] Names validated (2-100 characters)
- [ ] Dates validated (end after start)
- [ ] SQL injection prevented (parameterized queries)

### Authorization
- [ ] Voters cannot access admin pages
- [ ] Election Officers CAN access admin pages (FIXED!)
- [ ] Admins can access all pages

## ✅ Database Integrity

### Tables Created
- [ ] User_account
- [ ] Region (with 12 regions)
- [ ] Voter
- [ ] Election
- [ ] Election_Phase
- [ ] Election_Region
- [ ] Candidate
- [ ] Vote
- [ ] Audit_log

### Triggers Active
- [ ] validate_candidate_region
- [ ] validate_phase_overlap
- [ ] validate_vote_timing
- [ ] protect_audit_log (UPDATE)
- [ ] protect_audit_log (DELETE)
- [ ] auto_update_election_status

### Views Created
- [ ] Election_Results
- [ ] Voter_Statistics

### Indexes Created
- [ ] All 9 indexes present
- [ ] Query performance is good

## ✅ Performance Checks

### Page Load Times
- [ ] Login page < 1 second
- [ ] Dashboard < 2 seconds
- [ ] Lists (elections, users) < 3 seconds

### Database Queries
- [ ] No N+1 query problems
- [ ] Indexes being used
- [ ] Audit log paginated (50 per page)

## ✅ Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if Mac)
- [ ] Mobile browser

## ✅ Responsive Design

Test at different screen sizes:
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768px)
- [ ] Mobile (375px)

## ✅ Code Quality

### Python Code
- [ ] No syntax errors
- [ ] All imports work
- [ ] No deprecated functions
- [ ] Follows PEP 8 style

### Templates
- [ ] Valid HTML
- [ ] No broken links
- [ ] All images load
- [ ] Forms properly structured

### Static Files
- [ ] CSS loads without errors
- [ ] JavaScript executes without errors
- [ ] No console errors in browser

## ✅ Documentation

- [ ] README.md is clear and complete
- [ ] CHANGELOG.md documents all changes
- [ ] .env.example shows all config options
- [ ] Code comments are helpful

## 🎉 Final Verification

### All Systems Go!
- [ ] Application starts without errors
- [ ] All 4 user roles work
- [ ] All forms have CSRF protection
- [ ] All security features active
- [ ] Database triggers enforcing rules
- [ ] Professional styling applied
- [ ] Flash messages working
- [ ] Error pages display correctly
- [ ] Confirmations on critical actions
- [ ] Input validation active
- [ ] Session management working
- [ ] Audit logging operational

---

## ✅ Production Readiness (Optional)

For production deployment:
- [ ] Changed SECRET_KEY to random value
- [ ] Set FLASK_DEBUG=False
- [ ] Using strong database password
- [ ] Configured HTTPS
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Configured firewall
- [ ] Set up database backups
- [ ] Monitoring configured
- [ ] Error tracking set up
- [ ] Load testing completed

---

## 🐛 Common Issues

### Issue: "Module 'flask_wtf' not found"
**Fix:** `pip install flask-wtf`

### Issue: "Database NEMIS does not exist"
**Fix:** `psql -U postgres -c "CREATE DATABASE NEMIS;"`

### Issue: "CSRF token missing"
**Fix:** Check templates have `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`

### Issue: "Static files not loading"
**Fix:** Verify static/css/ and static/js/ directories exist with files

### Issue: "Election Officer can't access admin"
**Fix:** Verify using fixed admin.py (not original)

---

## 📊 Verification Summary

After completing this checklist, you should have:
- ✅ Fully functional NEMIS system
- ✅ All security features active
- ✅ Professional appearance
- ✅ All bugs fixed
- ✅ Ready for use or further development

**Congratulations! Your NEMIS installation is complete!** 🎉
