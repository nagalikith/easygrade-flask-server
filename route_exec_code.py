## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import flask
import import_helper as ih
import json
import threading

bp = flask.Blueprint("exec_code", __name__, template_folder="templates", static_folder="static")

@bp.route("/submission/upload")
def get_upload_page():
  assn_id = flask.request.args.get("assignment_id")
  pg_info = {
    "assn": ih.libs["assn_fileop"].get_res_assn_dict(assn_id),
    "endpoint_upload": flask.url_for("exec_code.upl_code_params"),
    "endpoint_output": flask.url_for("exec_code.get_code_output"),
    "check_delay": ih.get_env_val("CHECK_DELAY"),
  }

  pg_info["assn"]["id"] = assn_id

  return (
    flask.render_template("upload.html", pg_info=json.dumps(pg_info))
  )

#endpoint to report the status of code and output
@bp.route("/submission/report", methods=["POST"])
def get_code_output():
  subdir_name = flask.request.form.get("codeOutputToken")

  # reads the output.json corresponding to the subdirectory
  output_resp = (
    ih.libs["subm_fileop"].read_file_subdir(subdir_name, "__output.json", "json")
  )
  
  # removes the subdirectory
  if (output_resp["status"] == "Done"):
    ih.libs["subm_fileop"].rm_sub_subdir(subdir_name)
    return(
      {"status": "Done", 
      "score":  ih.libs["assn_fileop"].calc_score(output_resp)}
    )

  return (output_resp)

#endpoint to upload the file, saves the file
@bp.route("/submission/uploadreq", methods=["POST"])
def upl_code_params():

  try:
    req = flask.request
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

    # running a seperate thread to run the code
    run_code_thread = threading.Thread(target=ih.libs["run_code"].run_assn, args=( code_rel_info,))

    run_code_thread.start()

    # returns the sub directory name as json
    return (json.dumps(
      {"codeOutputToken": subdir_info.get("subdir_name")}
    ))

  except Exception as e:
    return {"Error": str(e)}

## EOF
