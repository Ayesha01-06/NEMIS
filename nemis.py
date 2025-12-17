"""
NEMIS - National Election Management Information System
Main application entry point
FIXED: Removed duplicate app.run(), added security configs, CSRF protection, error handlers
"""

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os

# Import blueprints
from controllers.auth import auth_bp
from controllers.admin import admin_bp
from controllers.voter import voter_bp

# Initialize Flask app
app = Flask(__name__)

# ============================================================
# SECURITY CONFIGURATIONS (FIXED & ENHANCED)
# ============================================================

# Generate secure secret key from environment or create random one
# NEVER use hardcoded keys in production!
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout

# CSRF Protection
csrf = CSRFProtect(app)

# Database configuration (optional - for reference)
app.config['DATABASE'] = {
    'NAME': 'NEMIS',
    'USER': 'postgres',
    'PASSWORD': 'postgres',
    'HOST': 'localhost',
    'PORT': '5432'
}

# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(voter_bp)

# ============================================================
# ERROR HANDLERS (NEW)
# ============================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('403.html'), 403

# ============================================================
# CONTEXT PROCESSORS (NEW)
# ============================================================

@app.context_processor
def inject_year():
    """Inject current year into all templates"""
    from datetime import datetime
    return {'current_year': datetime.now().year}

# ============================================================
# APPLICATION STARTUP
# ============================================================

if __name__ == "__main__":
    # FIXED: Removed duplicate app.run()
    # Run in debug mode for development only
    # In production, use: gunicorn -w 4 -b 0.0.0.0:5000 nemis:app
    
    debug_mode = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("NEMIS - National Election Management Information System")
    print("=" * 60)
    print(f"Running in {'DEBUG' if debug_mode else 'PRODUCTION'} mode")
    print(f"Server: http://127.0.0.1:{port}")
    print("=" * 60)
    
    app.run(debug=debug_mode, port=port, host='127.0.0.1')
