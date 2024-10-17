## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request
from flask_restful import Api, Resource
import import_helper as ih
import passlib.hash as ph
import flask
import functools
import traceback
import logging

sha256 = ph.pbkdf2_sha256

app = flask.Flask(__name__)
api = Api(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = '8B{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%'
jwt = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
    data = flask.request.get_json()
    username = data.get('username')
    password = data.get('password')

    auth_result = validate_login(username, password)

    if auth_result['status']:
        return flask.jsonify({"access_token": auth_result['access_token']})
    else:
        return flask.jsonify({"message": "Invalid credentials"}), 401

def handle_login(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            kwargs["userid"] = get_jwt_identity()
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            return flask.jsonify({"message": "Access token is missing or invalid"}), 401

    return wrapper

def get_hash_pass(password):
  return (
    sha256.hash(password)
  )

def validate_login(username, password):
    hashed_passwd = ih.libs["db_userop"].get_hash_passwd(username=username)
    is_valid = sha256.verify(password, hashed_passwd)

    if is_valid:
        eph_cred = ih.libs["db_userop"].create_cred(username)
        user_id = ih.libs["db_userop"].get_userid(username)
        return {"status": True, "user_id": user_id}
    else:
        return {"status": False}

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
