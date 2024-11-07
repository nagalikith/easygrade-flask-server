from datetime import timedelta
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
import import_helper as ih
import py_lib.user_auth as user_auth
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
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    jwt = JWTManager(app)
    # Initialize extensions
    CORS(app, supports_credentials=True ,origins=app.config['CORS_ORIGIN'])
    jwt = JWTManager(app)
    
    # Register blueprints
    blueprints = [
        rec.bp,
        rar.bp,
        rur.bp,  # Commented out as in original
        rsr.bp,
        user_auth.bp,
        #assignment_api.bp,
        #section_api.bp,
        #exec_code_api.bp
    ]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    


    return app
if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5050, debug=True)