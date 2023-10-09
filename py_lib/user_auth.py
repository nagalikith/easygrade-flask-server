## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import passlib.hash as ph
import flask
import functools
import traceback
import logging

sha256 = ph.pbkdf2_sha256

def handle_login(func):
  
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    
    try:

      ver_info = ih.libs["db_userop"].verify_eph_cred(
        flask.session["userid"],
        flask.session["eph_pass"]
      )
      print("Ver INFO: ", ver_info)
      
      if (ver_info["status"]):
        upd_info = ver_info["upd_info"]
        
        if (upd_info["action"] == "log off"):
          del flask.session["userid"]
          del flask.session["eph_pass"]

          return flask.redirect(flask.url_for("user_rel.get_login_page"))

        if (upd_info["update"]):
          flask.session["userid"] = upd_info["cred"]["userid"]
          flask.session["eph_pass"] = upd_info["cred"]["eph_pass"]

        kwargs["userid"] = flask.session.get("userid")
        return func(*args, **kwargs)

      else:
        return flask.redirect(flask.url_for("user_rel.get_login_page"))

    except Exception as e:
      traceback.print_exc()
      return flask.redirect(flask.url_for("user_rel.get_login_page"))
  
  return wrapper

def get_hash_pass(password):
  return (
    sha256.hash(password)
  )

def validate_login(username, password):
  hashed_passwd = ih.libs["db_userop"].get_hash_passwd(username=username)
  res = {"status": sha256.verify(password, hashed_passwd)}
  if (res["status"]):
    eph_cred = ih.libs["db_userop"].create_cred(username)
    res["eph_cred"] = eph_cred
  return res

def authenticate_using_password(userid, password):
  hashed_passwd = ih.libs["db_userop"].get_hash_passwd(userid=userid)

  return (hashed_passwd != None and sha256.verify(password, hashed_passwd))

def get_userid_session(session_cookie):
  return(
    session_cookie.get("userid")
  )

def is_admin(userid):
  return (
    userid == '0' * ih.get_env_val("HEX_ID_LENGTH")
  )

## EOF
