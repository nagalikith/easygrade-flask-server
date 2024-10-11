import import_helper as ih
import json
import threading
from flask import Flask, Blueprint, request, jsonify
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)

bp = Blueprint("exec_code_api", __name__, template_folder="templates", static_folder="static")

# Create an API object
api = Api(bp)

class UploadPage(Resource):
    def get(self):
        assn_id = request.args.get("assignment_id")
        pg_info = {
            "assn": ih.libs["assn_fileop"].get_res_assn_dict(assn_id),
            "endpoint_upload": "/api/submission/upload",
            "endpoint_output": "/api/submission/report",
            "check_delay": ih.get_env_val("CHECK_DELAY"),
        }

        pg_info["assn"]["id"] = assn_id

        return jsonify(pg_info)

class CodeOutput(Resource):
    def post(self):
        subdir_name = request.form.get("codeOutputToken")
        output_resp = ih.libs["subm_fileop"].read_file_subdir(subdir_name, "__output.json", "json")

        if output_resp["status"] == "Done":
            ih.libs["subm_fileop"].rm_sub_subdir(subdir_name)
            return {
                "status": "Done",
                "score": ih.libs["assn_fileop"].calc_score(output_resp)
            }

        return jsonify(output_resp)

class UploadCode(Resource):
    def post(self):
        try:
            req = request
            file = req.files.get("file")
            ih.libs["subm_fileop"].validate_file(file)
            subdir_info = ih.libs["subm_fileop"].make_sub_subdir()
            code_rel_info = {
                "file_name": file.filename,
                "subdir_info": subdir_info,
                "lang": req.form.get("sel_lang"),
                "assn_id": req.form.get("assn_id")
            }

            file.save("{}{}".format(
                subdir_info.get("subdir_path"),
                file.filename
            ))

            run_code_thread = threading.Thread(target=ih.libs["run_code"].run_assn, args=(code_rel_info,))
            run_code_thread.start()

            return jsonify({"codeOutputToken": subdir_info.get("subdir_name")})

        except Exception as e:
            return {"Error": str(e)}

# Add the resources to the API with their corresponding URLs
api.add_resource(UploadPage, '/api/submission/upload')
api.add_resource(CodeOutput, '/api/submission/report')
api.add_resource(UploadCode, '/api/submission/uploadreq')

if __name__ == "__main__":
    app.run(debug=True)
