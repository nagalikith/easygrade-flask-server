import json

from fastapi import APIRouter, Depends, HTTPException, Request

from app import import_helper as ih
from app.core.web_helpers import json_payload, redirect_to, safe_url_for, template_response

router = APIRouter()


def get_user_id(request: Request):
    user_id = request.session.get("userid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


@router.get("/user/logoff")
def logoff(request: Request, userid: str = Depends(get_user_id)):
    request.session.pop("userid", None)
    request.session.pop("eph_pass", None)
    return redirect_to(safe_url_for(request, "get_login_page", default="/login"))


@router.get("/user/view")
def get_userinfo_page(request: Request, userid: str = Depends(get_user_id)):
    pg_info = {}
    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for admin")

        req_userid = request.query_params.get("userid")
        user_info = ih.libs["db_userop"].admin_user_view(req_userid)
        pg_info["user_info"] = user_info
        pg_info["endpoint_users"] = safe_url_for(request, "get_users_page", default="/users")

        return template_response(
            request, "user_view.html", {"pg_info": json_payload(pg_info)}
        )
    except ValueError:
        request.session["error_id"] = "e06"
        return redirect_to(safe_url_for(request, "get_adduser_page", default="/user/add"))
    except Exception:
        return redirect_to(safe_url_for(request, "get_home_page", default="/"))


@router.post("/user/addreq")
async def add_user(request: Request, userid: str = Depends(get_user_id)):
    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for admin")

        form = await request.form()
        username = form.get("username")
        email = form.get("email") or None
        password = form.get("password")

        ih.libs["db_userop"].register_user(username, password, email)
        request.session["succ_id"] = "s03"

        return redirect_to(safe_url_for(request, "get_users_page", default="/users"))
    except ValueError:
        request.session["error_id"] = "e05"
        return redirect_to(safe_url_for(request, "get_adduser_page", default="/user/add"))
    except Exception:
        return redirect_to(safe_url_for(request, "get_home_page", default="/"))


@router.get("/user/add")
def get_adduser_page(request: Request, userid: str = Depends(get_user_id)):
    pg_info = {"endpoint_useradd": safe_url_for(request, "add_user", default="/user/addreq")}
    ih.libs["form_helper"].add_codes(request.session, pg_info)

    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for admin")

        return template_response(
            request, "adduser.html", {"pg_info": json_payload(pg_info)}
        )
    except Exception:
        return redirect_to(safe_url_for(request, "get_home_page", default="/"))


@router.get("/users")
def get_users_page(request: Request, userid: str = Depends(get_user_id)):
    pg_info = {
        "endpoint_user_v": safe_url_for(request, "get_userinfo_page", default="/user/view"),
        "endpoint_adduser": safe_url_for(request, "get_adduser_page", default="/user/add"),
    }
    ih.libs["form_helper"].add_codes(request.session, pg_info)

    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for admin")

        user_info = ih.libs["db_userop"].get_all_users()
        pg_info["user_info"] = user_info
        return template_response(
            request, "users.html", {"pg_info": json_payload(pg_info)}
        )
    except Exception:
        return redirect_to(safe_url_for(request, "get_home_page", default="/"))


@router.get("/account/c_password")
def get_password_change_page(request: Request, userid: str = Depends(get_user_id)):
    pg_info = {"endpoint_password_c": safe_url_for(
        request, "change_password", default="/account/c_passwordreq")}
    ih.libs["form_helper"].add_codes(request.session, pg_info)
    return template_response(
        request, "change_password.html", {"pg_info": json_payload(pg_info)}
    )


@router.post("/account/c_passwordreq")
async def change_password(request: Request, userid: str = Depends(get_user_id)):
    try:
        form = await request.form()
        curr_password = form.get("curr_password")
        new_password = form.get("new_password")

        if not ih.libs["user_auth"].authenticate_using_password(userid, curr_password):
            request.session["error_id"] = "e02"
            raise PermissionError("Authentication Failed")

        ih.libs["db_userop"].update_password(userid, new_password)
        request.session["succ_id"] = "s02"

        return redirect_to(safe_url_for(request, "get_account_page", default="/account"))
    except Exception:
        return redirect_to(safe_url_for(request, "get_password_change_page", default="/account/c_password"))


@router.get("/account/c_email")
def get_email_change_page(request: Request, userid: str = Depends(get_user_id)):
    pg_info = {"endpoint_email_c": safe_url_for(
        request, "change_email", default="/account/c_emailreq")}
    ih.libs["form_helper"].add_codes(request.session, pg_info)
    return template_response(
        request, "change_email.html", {"pg_info": json_payload(pg_info)}
    )


@router.post("/account/c_emailreq")
async def change_email(request: Request, userid: str = Depends(get_user_id)):
    try:
        form = await request.form()
        password = form.get("password")
        email = form.get("email") or None

        if email is not None and not ih.libs["form_helper"].validate_email(email):
            request.session["error_id"] = "e03"
            raise ValueError("Email Change Failed")

        if not ih.libs["user_auth"].authenticate_using_password(userid, password):
            request.session["error_id"] = "e02"
            raise PermissionError("Authentication Failed")

        ih.libs["db_userop"].update_email(userid, email)
        request.session["succ_id"] = "s01"

        return redirect_to(safe_url_for(request, "get_account_page", default="/account"))
    except Exception:
        return redirect_to(safe_url_for(request, "get_email_change_page", default="/account/c_email"))


@router.get("/account")
def get_account_page(request: Request, userid: str = Depends(get_user_id)):
    row = ih.libs["db_userop"].get_user_info(userid=userid)
    pg_info = {}
    ih.libs["form_helper"].add_codes(request.session, pg_info)
    pg_info["endpoint_chng_email"] = safe_url_for(
        request, "get_email_change_page", default="/account/c_email")
    pg_info["endpoint_chng_password"] = safe_url_for(
        request, "get_password_change_page", default="/account/c_password")
    pg_info["user_info"] = row
    return template_response(
        request, "account.html", {"pg_info": json_payload(pg_info)}
    )
