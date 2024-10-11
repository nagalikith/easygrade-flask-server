import flask
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
import import_helper as ih
from py_lib.user_auth import validate_login
import logging
from typing import Dict, List, Tuple, Union

# Import route blueprints
import route_assn_rel as rar
import route_exec_code as rec
import route_user_rel as rur
import route_sec_rel as rsr
from api import user_api, assignment_api, section_api, exec_code_api

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
    

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGIN'])
    jwt = JWTManager(app)
    
    # Register blueprints
    blueprints = [
        rec.bp,
        rar.bp,
        # rur.bp,  # Commented out as in original
        rsr.bp,
        user_api.bp,
        assignment_api.bp,
        section_api.bp,
        exec_code_api.bp
    ]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route('/login', methods=['POST', 'OPTIONS'])
    def login() -> JsonResponse:
        if request.method == 'OPTIONS':
            return handle_preflight_request()
        return handle_login_request()

    @app.route("/")
    @ih.handle_login
    def get_home_page() -> JsonResponse:
        return handle_home_page()

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

def handle_login_request() -> JsonResponse:
    """Handle login POST requests."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        if validate_login(username, password):
            access_token = create_access_token(identity=username)
            response = make_response(jsonify({"message": "Login successful"}))
            response.set_cookie(
                'access_token', 
                access_token, 
                secure=False,  # Set to True in production
                samesite='Lax'
            )
            return response, 200
        return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"message": "An error occurred during login"}), 500

def handle_home_page() -> JsonResponse:
    """Handle home page requests."""
    try:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({"error": "User identity not found"}), 401

        pg_info = build_page_info(current_user)
        return jsonify({"pg_info": pg_info}), 200
    except Exception as e:
        logger.error(f"Home page error: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

def build_page_info(current_user: str) -> Dict:
    """Build the page information dictionary."""
    pg_info = {}
    ih.libs["form_helper"].add_codes(flask.session, pg_info)
    
    link_data = [
        ("My Account", "user_rel.get_account_page"),
        ("Sections", "sec_rel.get_section_list_page")
    ]
    
    if ih.libs["user_auth"].is_admin(current_user):
        link_data.append(("Users", "user_rel.get_users_page"))
    
    pg_info["links"] = [
        {"name": name, "src": flask.url_for(endpoint)}
        for name, endpoint in link_data
    ]
    
    return pg_info

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5050, debug=True)