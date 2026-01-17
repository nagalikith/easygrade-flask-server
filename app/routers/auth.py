import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app import import_helper as ih
from app.core.auth_utils import create_access_token, get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


def validate_login(username: str, password: str) -> Dict[str, Any]:
    try:
        hashed_passwd = ih.libs["db_userop"].get_hashed_password(username=username)
        is_valid = ih.libs["user_auth"].sha256.verify(password, hashed_passwd)
        if is_valid:
            user_id = ih.libs["db_userop"].get_user_id(username)
            return {"status": True, "user_id": user_id}
        return {"status": False}
    except Exception as exc:
        logger.error("Login validation error: %s", exc)
        return {"status": False}


@router.post("/login")
def handle_login_request(request: Request, payload: LoginPayload):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    validation_result = validate_login(payload.username, payload.password)
    if not validation_result["status"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(identity=validation_result["user_id"])
    request.session["userid"] = validation_result["user_id"]
    return {
        "message": "Login successful",
        "user": payload.username,
        "accessToken": access_token
    }


@router.post("/logout")
def handle_logout_request(request: Request, user_id: str = Depends(get_current_user_id)):
    request.session.pop("userid", None)
    return {"message": "Logout successful"}


@router.get("/api/user/profile")
def get_user_profile(user_id: str = Depends(get_current_user_id)):
    user = ih.libs["db_userop"].get_user_info(user_id=user_id, cols=["user_id", "username", "email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user[0],
        "username": user[1],
        "email": user[2]
    }
