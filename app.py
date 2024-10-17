import flask
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
import py_lib.helper_libs.import_helper as ih
from py_lib.user_auth import validate_login
import logging
from typing import Dict, List, Tuple, Union
from werkzeug.middleware.profiler import ProfilerMiddleware

# Import route blueprints
import route_assn_rel as rar
import route_exec_code as rec
import route_user_rel as rur
import route_sec_rel as rsr
#from api import user_api, assignment_api, section_api, exec_code_api

# Type aliases
JsonResponse = Tuple[Dict[str, Union[Dict, str]], int]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    CORS_ORIGIN = "http://localhost:3000"
    SECRET_KEY = "7A{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%"
    JWT_SECRET_KEY = '8B{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%'
    JWT_TOKEN_LOCATION = "cookies"
    

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    jwt = JWTManager(app)
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGIN'])
    jwt = JWTManager(app)
    
    # Register blueprints
    blueprints = [
        rec.bp,
        rar.bp,
        rur.bp,  # Commented out as in original
        rsr.bp,
        #user_api.bp,
        #assignment_api.bp,
        #section_api.bp,
        #exec_code_api.bp
    ]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route('/login', methods=['POST', 'OPTIONS'])
    def login() -> JsonResponse:
        if request.method == 'OPTIONS':
            return handle_preflight_request()
        return handle_login_request()

    return app

def handle_preflight_request() -> JsonResponse:
    """Handle CORS preflight requests."""
    response = make_response()
    response.headers.update({
        'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    })
    return response, 200

def handle_login_request() -> 'JsonResponse':
    """Handle login POST requests."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        # Validate user credentials
        validation_result = validate_login(username, password)

        if validation_result["status"]:
            user_id = validation_result["user_id"]  # Get user ID from validation result
            access_token = create_access_token(identity=user_id)  # Create JWT with user ID

            response = make_response(jsonify({"message": "Login successful"}))
            
            # Set the access token cookie
            response.set_cookie(
                'access_token_cookie',  # Cookie for the JWT token
                access_token,
                httponly=True,          # Prevent access by JavaScript
                secure=False,           # Change to True in production
                samesite='Lax'          # Helps with CSRF protection
            )

            # Set the user ID cookie
            response.set_cookie(
                'user_id_cookie',       # Cookie for the user ID
                str(user_id),           # Ensure user ID is a string
                httponly=True,          # Optional, but can help protect user ID
                secure=False,          
                samesite='Lax'          
            )
            
            return response, 200

        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"message": "An error occurred during login"}), 500

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5050, debug=True)