## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import py_lib.helper_libs.import_helper as ih
import flask 
import json
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = flask.Blueprint("sec_rel", __name__, template_folder="templates", static_folder="static")

@bp.route("/sections")
@jwt_required()
def get_sections():
    try:
        userid = flask.request.cookies.get('user_id_cookie')
        # Get sections based on user role
        print(type(userid))
        if ih.libs["user_auth"].is_admin(userid):
            data = ih.libs["db_secop"].admin_sectionview()
        else:
            data = ih.libs["db_secop"].get_sectionview(userid)
        
        # Transform sections into the required format
        formatted_sections = {
            "status": True,
            "sections": []
        }
        
        for i in range(len(data['section_id'])):
          section_data = {
              "title": data['section_name'][i],  # Use section name as the title
              "subtitle": data['section_code'][i],  # Use section code as the subtitle
              "assignmentCount": 0,  # Initialize with 0 or fetch from a relevant source
              "sectionId": data['section_id'][i],
              "term": "fall2023"  # Assuming a fixed term; modify as needed
            }
          formatted_sections["sections"].append(section_data)

        return flask.jsonify(formatted_sections)
        
    except Exception as e:
        return flask.jsonify({
            "status": False,
            "error": str(e)
        }), 500

@bp.route("/section")
@jwt_required()
def get_section_page():
  userid = flask.request.cookies.get('user_id_cookie')
  pg_info = {}

  try:
    secid = flask.request.args["sectionid"]
    
    if ((ih.libs["form_helper"].validate_hex_ids(secid))):
      flask.session["error_id"] = "e04"
      raise ValueError("Invalid Section Id")

    acc_info = ih.libs["db_secop"].user_has_secacc(userid, secid)

    if (not(acc_info["status"])):
      flask.session["error_id"] = "e04"
      raise PermissionError("User doesnt have access to this resource")

    pg_info["sec_id"] = secid
    links = {}
    
    links["Assignments"] = flask.url_for("assign_op.list_assignment")
    links["People"] = flask.url_for("sec_rel.get_users_page")

    if (acc_info["role"] == "student"):
      links["Results"] = flask.url_for("sec_rel.get_user_result_page") 
    else:
      links["Create Assignment"] = flask.url_for("assign_op.get_create_assignment_page")
      links["Results"] = flask.url_for("sec_rel.get_sec_result_page")
      
    pg_info["links"] = links

    return flask.render_template(
      "section.html", pg_info=json.dumps(pg_info)
    )
  except:
    return flask.redirect(
      flask.url_for("sec_rel.get_section_page")
    )

@bp.route("/section/users")
@ih.handle_login
def get_users_page(userid):
  pg_info = {}

  try:
    secid = flask.request.args["sectionid"]
    
    if ((ih.libs["form_helper"].validate_hex_ids(secid))):
      flask.session["error_id"] = "e04"
      raise ValueError("Invalid Section Id")

    acc_info = ih.libs["db_secop"].user_has_secacc(userid, secid)

    if (not(acc_info["status"])):
      flask.session["error_id"] = "e04"
      raise PermissionError("User doesnt have access to this resource")
    
    user_info = ih.libs["db_secop"].sec_users_list(secid)
    
    pg_info["user_info"] = user_info

    if (acc_info["role"] != "student"):
      links = {"Add People": flask.url_for("sec_rel.get_addusers_page")}
      pg_info["links"] = links
    
    return flask.render_template(
      "section_users.html", pg_info=json.dumps(pg_info)
    )

  except:
    return flask.redirect(
      flask.url_for("sec_rel.get_section_list_page")
    )

@bp.route("/section/create")
@ih.handle_login
def get_create_section_page(userid):
  pg_info = {"endpoint_createsec": flask.url_for("sec_rel.create_section")}

  try:
    if (not(ih.libs["user_auth"].is_admin(userid))): 
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for Admin")

    ih.libs["form_helper"].add_codes(flask.session, pg_info)

    return (flask.render_template("create_section.html", pg_info=json.dumps(pg_info)))

  except:
    return flask.redirect(flask.url_for("sec_rel.get_section_list_page"))


@bp.route("/section/createreq", methods=["POST"])
@ih.handle_login
def create_section(userid):
  try:
    if (not(ih.libs["user_auth"].is_admin(userid))): 
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for Admin")

    form = flask.request.form
    sec_code = form.get("sec_code")
    sec_name = form.get("sec_name")

    if (sec_name == ''):
      sec_name = None
    
    if (not(ih.libs["form_helper"].validate_section_code(sec_code))):
      flask.session["error_id"] = error_map["e07"]
      raise ValueError("Invalid section code")

    if (sec_name != None and not(ih.libs["form_helper"].validate_section_name(sec_name))):
      flask.session["error_id"] = "e07"
      raise ValueError("Invalid section name")

    ih.libs["db_secop"].create_section(section_code=sec_code, section_name=sec_name);
    
    return (
      flask.redirect(
        flask.url_for("sec_rel.get_section_list_page")
      )
    )
  except Exception as e:
    print(e)
    flask.session["error_id"] = "e07"
    return flask.redirect(flask.url_for("sec_rel.get_create_section_page"))

## EOF
