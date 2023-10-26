import import_helper as ih
import json
from flask import Flask, Blueprint, request, jsonify
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)

# Create an API object
api = Api(app)

bp = Blueprint("sec_rel", __name__, template_folder="templates", static_folder="static")

class SectionList(Resource):
    @ih.handle_login
    def get(self, userid):
        pg_info = {}
        sect_info = None
        ih.libs["form_helper"].add_codes(request, pg_info)
        pg_info["endpoint_section"] = "/api/sections"

        if ih.libs["user_auth"].is_admin(userid):
            sect_info = ih.libs["db_secop"].admin_sectionview()
            pg_info["links"] = {"Create Section": "/api/section/create"}
        else:
            sect_info = ih.libs["db_secop"].get_sectionview(userid)
        pg_info["section_info"] = sect_info
        return jsonify(pg_info)

class Section(Resource):
    @ih.handle_login
    def get(self, userid):
        pg_info = {}
        try:
            secid = request.args["sectionid"]
            if ih.libs["form_helper"].validate_hex_ids(secid):
                request.args["error_id"] = "e04"
                raise ValueError("Invalid Section Id")
            acc_info = ih.libs["db_secop"].user_has_secacc(userid, secid)
            if not acc_info["status"]:
                request.args["error_id"] = "e04"
                raise PermissionError("User doesn't have access to this resource")
            pg_info["sec_id"] = secid
            links = {}
            links["Assignments"] = "/api/assignments"
            links["People"] = "/api/section/users"
            if acc_info["role"] == "student":
                links["Results"] = "/api/user/results"
            else:
                links["Create Assignment"] = "/api/assignments/create"
                links["Results"] = "/api/section/results"
            pg_info["links"] = links
            return jsonify(pg_info)
        except:
            return jsonify({"error": "Invalid Section Id"})

class SectionUsers(Resource):
    @ih.handle_login
    def get(self, userid):
        pg_info = {}
        try:
            secid = request.args["sectionid"]
            if ih.libs["form_helper"].validate_hex_ids(secid):
                request.args["error_id"] = "e04"
                raise ValueError("Invalid Section Id")
            acc_info = ih.libs["db_secop"].user_has_secacc(userid, secid)
            if not acc_info["status"]:
                request.args["error_id"] = "e04"
                raise PermissionError("User doesn't have access to this resource")
            user_info = ih.libs["db_secop"].sec_users_list(secid)
            pg_info["user_info"] = user_info
            if acc_info["role"] != "student":
                links = {"Add People": "/api/section/users/add"}
                pg_info["links"] = links
            return jsonify(pg_info)
        except:
            return jsonify({"error": "Invalid Section Id"})

class CreateSection(Resource):
    @ih.handle_login
    def get(self, userid):
        pg_info = {"endpoint_createsec": "/api/section/create"}
        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.args["error_id"] = "e04"
                raise PermissionError("Only for Admin")
            ih.libs["form_helper"].add_codes(request, pg_info)
            return jsonify(pg_info)
        except:
            return jsonify({"error": "Invalid Section Id"})

    @ih.handle_login
    def post(self, userid):
        try:
            if not ih.libs["user_auth"].is_admin(userid):
                request.args["error_id"] = "e04"
                raise PermissionError("Only for Admin")
            form = request.form
            sec_code = form.get("sec_code")
            sec_name = form.get("sec_name")
            if sec_name == '':
                sec_name = None
            if not ih.libs["form_helper"].validate_section_code(sec_code):
                request.args["error_id"] = "e07"
                raise ValueError("Invalid section code")
            if sec_name != None and not ih.libs["form_helper"].validate_section_name(sec_name):
                request.args["error_id"] = "e07"
                raise ValueError("Invalid section name")
            ih.libs["db_secop"].create_section(section_code=sec_code, section_name=sec_name)
            return jsonify({"message": "Section created successfully"})
        except Exception as e:
            print(e)
            request.args["error_id"] = "e07"
            return jsonify({"error": "Invalid Section Id"})

# Add the resources to the API with their corresponding URLs
api.add_resource(SectionList, '/api/sections')
api.add_resource(Section, '/api/section')
api.add_resource(SectionUsers, '/api/section/users')
api.add_resource(CreateSection, '/api/section/create')

if __name__ == "__main__":
    app.run(debug=True)
