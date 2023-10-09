import flask
import json
import import_helper as ih

bp = flask.Blueprint("assign_op", __name__, template_folder="templates", static_folder="static")

@bp.route("/assignment/create")
def get_create_assignment_page():
  pg_info = {
    "supp_lang": ih.get_env_val("SUPP_LANG"),
    "endpoint_create": flask.url_for("assign_op.create_assignment"),
    "endpoint_list": flask.url_for("assign_op.list_assignments"),
  }

  return flask.render_template("create_assignment.html", pg_info=json.dumps(pg_info))

@bp.route("/assignment/createreq", methods=["POST"])
def create_assignment():
  form = flask.request.form
  assn_dict = ih.libs["form_helper"].create_assn_formdict(form)
  ih.libs["assn_fileop"].create_assignment(assn_dict)
  return ({"operation": "successfull"})

@bp.route("/assignment/edit")
def edit_assignment_page(): 
  assn_id = flask.request.args.get("assignment_id")
  pg_info = {
    "assn_id": assn_id,
    "supp_lang": ih.get_env_val("SUPP_LANG"),
    "assn": ih.libs["assn_fileop"].get_assn_dict_nosys(assn_id),
    "endpoint_edit": flask.url_for("assign_op.edit_assignment"),
    "endpoint_list": flask.url_for("assign_op.list_assignments")
  }
  return flask.render_template("edit_assignment.html", pg_info=json.dumps(pg_info))

@bp.route("/assignment/editreq", methods=["POST"])
def edit_assignment(): 
  form = flask.request.form
  assn_id = form.get("assn_id")
  assn_dict = ih.libs["form_helper"].create_assn_formdict(form)
  ih.libs["assn_fileop"].edit_assignment(assn_id, assn_dict)
  return {"Operation": "Successfull"}

@bp.route("/assignment/copy")
def copy_assignment_page(): 
  assn_id = flask.request.args.get("assignment_id")
  pg_info = {
    "assn_id": assn_id,
    "supp_lang": ih.get_env_val("SUPP_LANG"),
    "assn": ih.libs["assn_fileop"].get_assn_dict_nosys(assn_id),
    "endpoint_create": flask.url_for("assign_op.create_assignment"),
    "endpoint_list": flask.url_for("assign_op.list_assignments")
  }
  return flask.render_template("copy_assignment.html", pg_info=json.dumps(pg_info))

@bp.route("/assignment/deletereq", methods=["POST"])
def delete_assignment(): 
  assn_id = flask.request.form.get("assignment_id")
  ih.libs["assn_fileop"].del_assn(assn_id)
  return flask.redirect(flask.url_for("assign_op.list_assignments"))

@bp.route("/assignments")
def list_assignments():

  assn_ids = ih.libs["assn_fileop"].list_assignment_ids()
  assn_titles = [ih.libs["assn_fileop"].get_assn_prop(assn_id, "title") for assn_id in assn_ids]
  assn_descs = [ih.libs["assn_fileop"].get_assn_prop(assn_id, "description") for assn_id in assn_ids]

  btn_names = ["Start", "Edit", "Copy", "Delete"]
  btns = {}
  btns["Start"] = {"method": "GET", "url": flask.url_for("exec_code.get_upload_page")}
  btns["Edit"] = {"method": "GET", "url": flask.url_for("assign_op.edit_assignment_page")}
  btns["Copy"] = {"method": "GET", "url": flask.url_for("assign_op.copy_assignment_page")}
  btns["Delete"] = {"method": "POST", "url": flask.url_for("assign_op.delete_assignment")}

  pg_info = {
    "assn_ids": assn_ids, 
    "assn_titles": assn_titles,
    "assn_descs": assn_descs,
    "btn_names": btn_names,
    "btns": btns,
  }

  return flask.render_template("list_assignment.html", pg_info=json.dumps(pg_info))
