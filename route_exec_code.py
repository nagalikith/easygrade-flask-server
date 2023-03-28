## GTG
import flask
import import_helper as ih
import json
import threading

#sets the default length of the hex code generated
ih.libs["gen_hex"].config["length"] = 20

bp = flask.Blueprint("exec_code", __name__, template_folder="templates", static_folder="static")

#endpoint to report the status of code and output
@bp.route("/report_code_info", methods=["POST"])
def get_code_output():
  subdir_name = flask.request.form.get("codeOutputToken")

  # reads the output.json corresponding to the subdirectory
  output_resp = (
    ih.libs["handle_fileop"].read_file_subdir(subdir_name, "output.json", "json")
  )
  
  # removes the subdirectory
  if (output_resp["status"] == "Done"):
    ih.libs["handle_fileop"].rm_sub_subdir(subdir_name)

  return (output_resp)

#endpoint to upload the file, saves the file
@bp.route("/upload", methods=["POST"])
def upl_code_params():

  try:
    req = flask.request
    file = req.files.get("file")
    ih.libs["handle_fileop"].validate_file(file)
    subdir_info = ih.libs["handle_fileop"].make_sub_subdir()
    code_rel_info = {
      "file_name": file.filename,
      "subdir_info": subdir_info,
      "lang": req.form.get("sel_lang"),
      "input": req.form.get("code_input"),
    }

    file.save("{}{}".format(
      subdir_info.get("subdir_path"),
      file.filename
    ))

    # running a seperate thread to run the code
    run_code_thread = threading.Thread(target=ih.libs["run_code"].run_code, args=( code_rel_info,))

    run_code_thread.start()

    # returns the sub directory name as json
    return (json.dumps(
      {"codeOutputToken": subdir_info.get("subdir_name")}
    ))

  except Exception as e:
    return {"Error": str(e)}

## TYJC
