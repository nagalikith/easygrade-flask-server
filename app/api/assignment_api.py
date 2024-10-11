import json
import utils.import_helper as ih
from flask import Flask, Blueprint
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
bp = Blueprint("assignment_api", __name__)
# Create an API object
api = Api(bp)

SUPP_LANG = ih.get_env_val("SUPP_LANG")

class CreateAssignment(Resource):
    def get(self):
        pg_info = {
            "supp_lang": ih.get_env_val("SUPP_LANG"),
            "endpoint_create": "/api/assignment/create",
            "endpoint_list": "/api/assignments",
        }
        return {"pg_info": pg_info}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('data', type=dict)
        args = parser.parse_args()
        
        assn_dict = ih.libs["form_helper"].create_assn_formdict(args['data'])
        ih.libs["assn_fileop"].create_assignment(assn_dict)
        return {"operation": "successful"}

class EditAssignment(Resource):
    def get(self):
        assn_id = request.args.get("assignment_id")
        pg_info = {
            "assn_id": assn_id,
            "supp_lang": ih.get_env_val("SUPP_LANG"),
            "assn": ih.libs["assn_fileop"].get_assn_dict_nosys(assn_id),
            "endpoint_edit": "/api/assignment/edit",
            "endpoint_list": "/api/assignments"
        }
        return {"pg_info": pg_info}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('assn_id', type=str)
        parser.add_argument('data', type=dict)
        args = parser.parse_args()

        assn_id = args['assn_id']
        assn_dict = ih.libs["form_helper"].create_assn_formdict(args['data'])
        ih.libs["assn_fileop"].edit_assignment(assn_id, assn_dict)
        return {"Operation": "successful"}

class CopyAssignment(Resource):
    def get(self):
        assn_id = request.args.get("assignment_id")
        pg_info = {
            "assn_id": assn_id,
            "supp_lang": ih.get_env_val("SUPP_LANG"),
            "assn": ih.libs["assn_fileop"].get_assn_dict_nosys(assn_id),
            "endpoint_create": "/api/assignment/create",
            "endpoint_list": "/api/assignments"
        }
        return {"pg_info": pg_info}

class DeleteAssignment(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('assignment_id', type=str)
        args = parser.parse_args()

        assn_id = args['assignment_id']
        ih.libs["assn_fileop"].del_assn(assn_id)
        return {"message": "Assignment deleted successfully"}

class ListAssignments(Resource):
    def get(self):
        assn_ids = ih.libs["assn_fileop"].list_assignment_ids()
        assn_titles = [ih.libs["assn_fileop"].get_assn_prop(assn_id, "title") for assn_id in assn_ids]
        assn_descs = [ih.libs["assn_fileop"].get_assn_prop(assn_id, "description") for assn_id in assn_ids]

        btn_names = ["Start", "Edit", "Copy", "Delete"]
        btns = {
            "Start": {"method": "GET", "url": "/api/assignments"},
            "Edit": {"method": "GET", "url": "/api/assignment/edit"},
            "Copy": {"method": "GET", "url": "/api/assignment/create"},
            "Delete": {"method": "POST", "url": "/api/assignment/delete"}
        }

        pg_info = {
            "assn_ids": assn_ids,
            "assn_titles": assn_titles,
            "assn_descs": assn_descs,
            "btn_names": btn_names,
            "btns": btns,
        }
        return {"pg_info": pg_info}

# Add the resources to the API with their corresponding URLs
api.add_resource(CreateAssignment, '/api/assignment/create')
api.add_resource(EditAssignment, '/api/assignment/edit')
api.add_resource(CopyAssignment, '/api/assignment/copy')
api.add_resource(DeleteAssignment, '/api/assignment/delete')
api.add_resource(ListAssignments, '/api/assignments')

if __name__ == "__main__":
    app.run(debug=True)
