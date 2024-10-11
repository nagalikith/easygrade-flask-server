## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import flask
import json

bp = flask.Blueprint("user_rel", __name__, template_folder="templates", static_folder="static")

@bp.route("/user/logoff")
@ih.handle_login
def logoff(userid):
  del flask.session["userid"]
  del flask.session["eph_pass"]
  
  return flask.redirect(flask.url_for("user_rel.get_login_page"))

@bp.route("/user/view")
@ih.handle_login
def get_userinfo_page(userid):
  
  pg_info = {}

  try: 
    if (not(ih.libs["user_auth"].is_admin(userid))):
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for admin")

    req_userid = flask.request.args.get("userid")

    user_info = ih.libs["db_userop"].admin_userview(req_userid)

    pg_info["user_info"] = user_info
    pg_info["endpoint_users"] = flask.url_for("user_rel.get_users_page")

    return flask.render_template(
      "user_view.html", pg_info=json.dumps(pg_info)
    )
  except ValueError:
    flask.session["error_id"] = "e06"
    return flask.redirect(flask.url_for("user_rel.get_adduser_page"))
  except Exception as e:
    print(e)
    return flask.redirect(flask.url_for("get_home_page"))

@bp.route("/user/addreq", methods=["POST"])
@ih.handle_login
def add_user(userid):
  
  try: 
    if (not(ih.libs["user_auth"].is_admin(userid))):
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for admin")

    form = flask.request.form
    username = form.get("username") 
    email = form.get("email")
    password = form.get("password")

    if (email == ''):
      email = None

    ih.libs["db_userop"].reg_user(username, password, email)
    flask.session["succ_id"] = "s03"

    return flask.redirect(flask.url_for("user_rel.get_users_page")) 
  except ValueError:
    flask.session["error_id"] = "e05"
    return flask.redirect(flask.url_for("user_rel.get_adduser_page"))
  except Exception as e:
    print(e)
    return flask.redirect(flask.url_for("get_home_page"))

@bp.route("/user/add")
@ih.handle_login
def get_adduser_page(userid):

  pg_info = {"endpoint_useradd": flask.url_for("user_rel.add_user")}

  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  try: 
    if (not(ih.libs["user_auth"].is_admin(userid))):
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for admin")


    return flask.render_template(
      "adduser.html", pg_info=json.dumps(pg_info)
    )  
  except:
    return flask.redirect(flask.url_for("get_home_page"))

@bp.route("/users")
@ih.handle_login
def get_users_page(userid):
  
  pg_info = {}
  pg_info["endpoint_user_v"] = flask.url_for("user_rel.get_userinfo_page")
  pg_info["endpoint_adduser"] = flask.url_for("user_rel.get_adduser_page");

  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  try: 
    if (not(ih.libs["user_auth"].is_admin(userid))):
      flask.session["error_id"] = "e04"
      raise PermissionError("Only for admin")
    
    user_info = ih.libs["db_userop"].get_all_users()
    pg_info["user_info"] = user_info
    return flask.render_template("users.html", pg_info=json.dumps(pg_info))
  except Exception as e:
    print(e)
    return flask.redirect(flask.url_for("get_home_page"))

@bp.route("/account/c_password")
@ih.handle_login
def get_password_change_page(userid):
  pg_info = {"endpoint_password_c": flask.url_for("user_rel.change_password")}
  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  return flask.render_template(
    "change_password.html", pg_info=json.dumps(
      pg_info
    )
  )

@bp.route("/account/c_passwordreq", methods=["POST"])
@ih.handle_login
def change_password(userid):
  try:
    form = flask.request.form
    curr_password = form.get("curr_password")
    new_password = form.get("new_password")

    if (not(ih.libs["user_auth"].authenticate_using_password(userid, curr_password))):
      flask.session["error_id"] = "e02"
      raise PermissionError("Authentication Failed")
    
    ih.libs["db_userop"].upd_passwd(userid, new_password) 
    flask.session["succ_id"] = "s02"

    return flask.redirect(flask.url_for("user_rel.get_account_page"))

  except:
    return flask.redirect(flask.url_for("user_rel.get_password_change_page"))

@bp.route("/account/c_email")
@ih.handle_login
def get_email_change_page(userid):

  pg_info = {"endpoint_email_c": flask.url_for("user_rel.change_email")}

  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  return flask.render_template(
    "change_email.html", pg_info=json.dumps(
      pg_info
    )
  )

@bp.route("/account/c_emailreq", methods=["POST"])
@ih.handle_login
def change_email(userid):
  try:
    form = flask.request.form
    password = form.get("password")
    email = form.get("email")

    if (email == ''):
      email = None

    if ((email != None) and  not(ih.libs["form_helper"].validate_email(email))):
      flask.session["error_id"] = "e03"
      raise ValueError("Email Change Failed")

    if (not(ih.libs["user_auth"].authenticate_using_password(userid, password))):
      flask.session["error_id"] = "e02"
      raise PermissionError("Authentication Failed")
    
    ih.libs["db_userop"].upd_email(userid, email) 
    flask.session["succ_id"] = "s01"

    return flask.redirect(flask.url_for("user_rel.get_account_page"))

  except:
    return flask.redirect(flask.url_for("user_rel.get_email_change_page"))

@bp.route("/account")
@ih.handle_login
def get_account_page(userid):

  row = ih.libs["db_userop"].get_user_info(userid=userid)

  pg_info = {}

  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  pg_info["endpoint_chng_email"] = flask.url_for("user_rel.get_email_change_page")
  pg_info["endpoint_chng_password"] = flask.url_for("user_rel.get_password_change_page")

  user_info = {
    "username": getattr(row, "username"),
    "email": getattr(row, "email"),
    "join_time": getattr(row, "reg_epoch")
  }

  pg_info["user_info"] = user_info

  return flask.render_template("account.html", pg_info=json.dumps(pg_info))

@bp.route("/login")
def get_login_page():

  pg_info = {"endpoint_validate": flask.url_for("user_rel.verify_user")}

  ih.libs["form_helper"].add_codes(flask.session, pg_info)

  try:

    ver_info = ih.libs["db_userop"].verify_eph_cred(
      flask.session.get("userid"),
      flask.session.get("eph_pass")
    )
    

    if (ver_info["status"] and not(ver_info["upd_info"]["update"]) and (ver_info["upd_info"]["action"] == None)):
      return flask.redirect(flask.url_for("get_home_page"))

    else:
      return flask.render_template("login.html", pg_info=json.dumps(pg_info))
  
  except:
    return flask.render_template("login.html", pg_info=json.dumps(pg_info))

## delete this
# @bp.route("/login/usercred")
# @ih.handle_login
# def get_user_cred(userd):
#   return "<p>{}: {}</p>".format(
#     userid, flask.session["eph_pass"]
#   ) 

@bp.route("/verify", methods=["POST"])
def verify_user():
  try:
    form = flask.request.form
    username = form.get("username")
    password = form.get("password")
    valid_info = ih.libs["user_auth"].validate_login(username, password)

    if (valid_info["status"]):
      cred = valid_info["eph_cred"]
      flask.session["userid"] = cred["userid"]  
      flask.session["eph_pass"] =  cred["eph_pass"]
      return flask.redirect(flask.url_for("get_home_page"))
    
    else:
      flask.session["error_id"] = "e01" 
      return (flask.redirect(flask.url_for("user_rel.get_login_page")))

  except:
    flask.session["error_id"] = "e01" 
    return (flask.redirect(flask.url_for("user_rel.get_login_page")))

## EOF
