from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    get_jwt_identity, 
    jwt_required
)
import functools
import logging
from datetime import timedelta

from app.services.db.user import UserService
from app.utils.hex import is_admin

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
bp = Blueprint('auth', __name__)

def handle_login(func):
    """Decorator for handling login requirements"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            @jwt_required()
            def decorated_route(*args, **kwargs):
                current_user = get_jwt_identity()
                return func(current_user, *args, **kwargs)
            return decorated_route(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401
    return wrapper

@bp.route('/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user_service = UserService()
        if user_service.validate_login(username, password):
            access_token = create_access_token(
                identity=username,
                expires_delta=timedelta(days=1)
            )
            return jsonify({
                "access_token": access_token,
                "message": "Login successful"
            }), 200
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "An error occurred during login"}), 500

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Handle user logout"""
    # Note: With JWT, traditional logout isn't necessary
    # Client should discard the token
    return jsonify({"message": "Logged out successfully"}), 200

@bp.route('/check-auth', methods=['GET'])
@jwt_required()
def check_auth():
    """Check if user is authenticated"""
    current_user = get_jwt_identity()
    return jsonify({
        "authenticated": True,
        "user": current_user,
        "is_admin": is_admin(current_user)
    }), 200

# Error handlers
@bp.errorhandler(401)
def unauthorized_error(error):
    return jsonify({"error": "Unauthorized"}), 401

@bp.errorhandler(403)
def forbidden_error(error):
    return jsonify({"error": "Forbidden"}), 403

# Optional: Request hooks
@bp.before_request
def before_request():
    # Add any preprocessing here
    pass

@bp.after_request
def after_request(response):
    # Add any postprocessing here
    return response

# Utility functions
def require_admin(f):
    """Decorator to require admin privileges"""
    @functools.wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        if not is_admin(current_user):
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function