from hashlib import sha256
from flask import Blueprint, jsonify, request, make_response, current_app
import import_helper as ih
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token,
    get_jwt,
    set_access_cookies,
    unset_jwt_cookies
)
from functools import wraps
import logging
from datetime import timedelta
from typing import Dict, Tuple, Any, Optional
import passlib.hash as ph
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sha256 = ph.pbkdf2_sha256
bp = Blueprint('auth', __name__)

class Config:
    """Configuration class for authentication settings."""
    CORS_ORIGIN = "http://localhost:3000"  # Replace with your frontend URL
    JWT_ACCESS_EXPIRES = timedelta(hours=1)
    COOKIE_SECURE = False  # Set to True in production
    COOKIE_SAMESITE = 'Lax'
    
def error_handler(f):
    """Decorator for handling errors in routes."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"message": "An internal error occurred"}), 500
    return wrapped

def validate_login(username: str, password: str) -> Dict[str, Any]:
    """
    Validate user login credentials.
    Returns dict with status and user_id if successful.
    """
    try:
        hashed_passwd = ih.libs["db_userop"].get_hashed_password(username=username)
        is_valid = sha256.verify(password, hashed_passwd)

        if is_valid:
          user_id = ih.libs["db_userop"].get_user_id(username)
          return {"status": True, "user_id": user_id}
        else:
          return {"status": False}
    except Exception as e:
        logger.error(f"Login validation error: {str(e)}")
        return {"status": False}

@bp.route('/login', methods=['OPTIONS'])
def handle_preflight_request():
    """Handle CORS preflight requests."""
    response = make_response()
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Credentials': 'true'
    })
    return response, 200

@bp.route('/login', methods=['POST'])
@error_handler
def handle_login_request():
    """Handle login POST requests."""
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "No data provided"}), 400
        
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    # Validate user credentials
    validation_result = validate_login(username, password)

    if validation_result["status"]:
        user_id = validation_result["user_id"]
        
        # Create access token with user data
        access_token = create_access_token(
            identity=user_id,
            expires_delta=Config.JWT_ACCESS_EXPIRES
        )

        # Create response
        response = make_response(jsonify({
            "message": "Login successful",
            "user": username,
            "accessToken": access_token
        }))
        
        
        # Set CORS headers
        response.headers.update({
            'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
            'Access-Control-Allow-Credentials': 'true'
        })
        
        return response, 200

    return jsonify({"message": "Invalid credentials"}), 401

@bp.route('/logout', methods=['POST'])
@jwt_required()
@error_handler
def handle_logout_request():
    """Handle logout requests."""
    response = make_response(jsonify({"message": "Logout successful"}))
    
    # Remove cookies
    unset_jwt_cookies(response)
    response.delete_cookie('user_id_cookie')
    
    # Set CORS headers
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Credentials': 'true'
    })
    
    return response, 200

@bp.route('/api/user/profile', methods=['GET'])
@jwt_required()
@error_handler
def get_user_profile():
    """Get the current user's profile."""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Get user from database
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    response = jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "roles": user.roles
    })
    
    # Set CORS headers
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Credentials': 'true'
    })
    
    return response, 200

# Register error handlers
@bp.errorhandler(400)
def bad_request(error):
    response = jsonify({"message": "Bad request"})
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Credentials': 'true'
    })
    return response, 400

@bp.errorhandler(401)
def unauthorized(error):
    response = jsonify({"message": "Unauthorized"})
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Credentials': 'true'
    })
    return response, 401

@bp.errorhandler(500)
def internal_server_error(error):
    response = jsonify({"message": "Internal server error"})
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Credentials': 'true'
    })
    return response, 500

def is_admin(userid):
  return (
    userid == '0' * ih.get_env_val("HEX_ID_LENGTH")
  ) 