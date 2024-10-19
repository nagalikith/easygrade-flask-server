import import_helper as ih
from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource

bp = Blueprint("user_rel", __name__, template_folder="templates", static_folder="static")

# Create an API object
api = Api(bp)

class UserLogoff(Resource):
    
    def get(self, userid):
        del request.session["userid"]
        del request.session["eph_pass"]
        return jsonify({"message": "Logged off successfully"})

class UserInfo(Resource):
    
    def get(self, userid):
        pg_info = {}
        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.session["error_id"] = "e04"
                raise PermissionError("Only for admin")

            req_userid = request.args.get("userid")

            user_info = ih.libs["db_userop"].admin_userview(req_userid)

            pg_info["user_info"] = user_info
            pg_info["endpoint_users"] = "/api/users"

            return jsonify(pg_info)
        except ValueError:
            request.session["error_id"] = "e06"
            return jsonify({"error": "Invalid Section Id"})
        except Exception as e:
            print(e)
            return jsonify({"error": "Invalid request"})

class AddUser(Resource):
    
    def post(self, userid):
        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.session["error_id"] = "e04"
                raise PermissionError("Only for admin")

            form = request.form
            username = form.get("username")
            email = form.get("email")
            password = form.get("password")

            if email == '':
                email = None

            ih.libs["db_userop"].reg_user(username, password, email)
            return jsonify({"message": "User added successfully"})
        except ValueError:
            request.session["error_id"] = "e05"
            return jsonify({"error": "Invalid Section Id"})
        except Exception as e:
            print(e)
            return jsonify({"error": "Invalid request"})

class AddUserPage(Resource):
    
    def get(self, userid):
        pg_info = {"endpoint_useradd": "/api/user/add"}
        ih.libs["form_helper"].add_codes(request.session, pg_info)
        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.session["error_id"] = "e04"
                raise PermissionError("Only for admin")
            return jsonify(pg_info)
        except:
            return jsonify({"error": "Invalid request"})

class Users(Resource):
    
    def get(self, userid):
        pg_info = {}
        pg_info["endpoint_user_v"] = "/api/user/view"
        pg_info["endpoint_adduser"] = "/api/user/add";

        ih.libs["form_helper"].add_codes(request.session, pg_info)

        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.session["error_id"] = "e04"
                raise PermissionError("Only for admin")

            user_info = ih.libs["db_userop"].get_all_users()
            pg_info["user_info"] = user_info
            return jsonify(pg_info)
        except Exception as e:
            print(e)
            return jsonify({"error": "Invalid request"})

# Add the resources to the API with their corresponding URLs
api.add_resource(UserLogoff, '/api/user/logoff')
api.add_resource(UserInfo, '/api/user/view')
api.add_resource(AddUser, '/api/user/add')
api.add_resource(AddUserPage, '/api/user/addpage')
api.add_resource(Users, '/api/users')
