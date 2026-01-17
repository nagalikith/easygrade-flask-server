import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import import_helper as ih
import passlib.hash as ph
from py_lib.auth_utils import create_access_token, get_current_user_id

sha256 = ph.pbkdf2_sha256

logger = logging.getLogger(__name__)
bp = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


def validate_login(username: str, password: str) -> Dict[str, Any]:
    try:
        hashed_passwd = ih.libs["db_userop"].get_hashed_password(username=username)
        is_valid = sha256.verify(password, hashed_passwd)
        if is_valid:
            user_id = ih.libs["db_userop"].get_user_id(username)
            return {"status": True, "user_id": user_id}
        return {"status": False}
    except Exception as exc:
        logger.error("Login validation error: %s", exc)
        return {"status": False}


def get_hash_pass(password: str) -> str:
    return sha256.hash(password)


def authenticate_using_password(user_id: str, password: str) -> bool:
    try:
        hashed_passwd = ih.libs["db_userop"].get_hashed_password(user_id=user_id)
        return sha256.verify(password, hashed_passwd)
    except Exception:
        return False


@bp.post("/login")
def handle_login_request(payload: LoginPayload):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    validation_result = validate_login(payload.username, payload.password)
    if not validation_result["status"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(identity=validation_result["user_id"])
    return {
        "message": "Login successful",
        "user": payload.username,
        "accessToken": access_token
    }


@bp.post("/logout")
def handle_logout_request(user_id: str = Depends(get_current_user_id)):
    return {"message": "Logout successful"}


@bp.get("/api/user/profile")
def get_user_profile(user_id: str = Depends(get_current_user_id)):
    user = ih.libs["db_userop"].get_user_info(user_id=user_id, cols=["user_id", "username", "email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user[0],
        "username": user[1],
        "email": user[2]
    }


def is_admin(userid):
    return userid == '0' * ih.get_env_val("HEX_ID_LENGTH")
