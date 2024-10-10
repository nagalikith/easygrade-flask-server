import flask
import json

from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, verify_jwt_in_request
import import_helper as ih
from py_lib.user_auth import validate_login

import route_assn_rel as rar
import route_exec_code as rec
import route_user_rel as rur
import route_sec_rel as rsr
from api import user_api,assignment_api,section_api, exec_code_api

def create_app():
  app = flask.Flask(__name__)
  CORS(app, supports_credentials=True, origins="http://localhost:3000")
  app.secret_key = "7A{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%"
  app.register_blueprint(rec.bp)
  app.register_blueprint(rar.bp)
  #app.register_blueprint(rur.bp)
  app.register_blueprint(rsr.bp)
  app.register_blueprint(user_api.bp)
  app.register_blueprint(assignment_api.bp)
  app.register_blueprint(section_api.bp)
  app.register_blueprint(exec_code_api.bp)
  # Configure JWT
  app.config['JWT_SECRET_KEY'] = '8B{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%'
  jwt = JWTManager(app)

  @app.route('/login', methods=['POST', 'OPTIONS'])
  def login():
    if flask.request.method == 'OPTIONS':  # Handle preflight request
            response = flask.make_response()
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response, 200
    
    #Post Request
    data = flask.request.get_json()
    username = data.get('username')
    password = data.get('password')

    if validate_login(username, password):
      access_token = create_access_token(identity=username)
            
      # Create the response object
      response = flask.make_response({"message": "Login successful"})
      # Set the JWT as an HttpOnly cookie
      response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax')  
      # For production, use `secure=True` to only send the cookie over HTTPS
      response.headers.add('Access-Control-Allow-Credentials', 'true')

      return response, 200
    else:
        return flask.jsonify({"message": "Invalid credentials"}), 401
  @app.route("/")
  @ih.handle_login
  def get_home_page():
    try:
        current_user = get_jwt_identity()
        pg_info = {}
        ih.libs["form_helper"].add_codes(flask.session, pg_info)

        link_names = ["My Account", "Sections"]
        links_flask = ["user_rel.get_account_page", "sec_rel.get_section_list_page"]

        if ih.libs["user_auth"].is_admin(current_user):
            link_names.append("Users")
            links_flask.append("user_rel.get_users_page")

        pg_info["links"] = []

        for i in range(len(link_names)):
            name = link_names[i]
            src = flask.url_for(links_flask[i])
            pg_info["links"].append({"name": name, "src": src})

        return flask.jsonify({"pg_info": pg_info}), 200
    except Exception as e:
        return flask.jsonify({"error": "Unauthorized"}), 401

  return app

if __name__ == "__main__":
  app = create_app()
  app.run(host='0.0.0.0',port=5050, debug=True)
