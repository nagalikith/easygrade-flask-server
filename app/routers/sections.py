from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Request

from app import import_helper as ih
from app.core.auth_utils import get_current_user_id
from app.core.web_helpers import json_payload, redirect_to, safe_url_for, template_response

router = APIRouter()


def get_session_user_id(request: Request):
    user_id = request.session.get("userid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def get_term_from_date(date_str):
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month = date.month
    year = date.year

    if 8 <= month <= 12:
        return f"Fall {year}"
    if 1 <= month <= 5:
        return f"Spring {year}"
    return f"Summer {year}"


@router.get("/api/sections")
def get_sections(user_id: str = Depends(get_current_user_id)):
    try:
        if ih.libs["user_auth"].is_admin(user_id):
            data = ih.libs["db_secop"].admin_sectionview()
        else:
            data = ih.libs["db_secop"].get_sectionview(user_id)

        formatted_response = {
            "status": True,
            "courses": {}
        }

        for i in range(len(data['section_id'])):
            term = get_term_from_date(data['start_date'][i]) if 'start_date' in data else "Fall 2023"
            section_data = {
                "title": data['section_name'][i],
                "subtitle": f"Section {data['section_code'][i]}",
                "assignmentCount": data.get('assignment_count', [0])[i] if 'assignment_count' in data else 0,
                "sectionId": str(data['section_id'][i]),
                "instructor": data.get('instructor_name', [''])[i] if 'instructor_name' in data else '',
                "enrollmentCount": data.get('enrollment_count', [0])[i] if 'enrollment_count' in data else 0,
                "startDate": data.get('start_date', [''])[i] if 'start_date' in data else '',
                "endDate": data.get('end_date', [''])[i] if 'end_date' in data else ''
            }

            formatted_response["courses"].setdefault(term, []).append(section_data)

        for term in formatted_response["courses"]:
            formatted_response["courses"][term].sort(key=lambda x: x["title"])

        return formatted_response
    except Exception as exc:
        return {
            "status": False,
            "error": "Failed to fetch courses. Please try again later.",
            "debug_message": str(exc)
        }


@router.get("/api/sections/{section_id}")
def get_section(section_id: str,
                request: Request,
                user_id: str = Depends(get_current_user_id)):
    response_data = {}
    try:
        if not ih.libs["form_helper"].validate_hex_ids(section_id):
            request.session["error_id"] = "e04"
            raise ValueError("Invalid Section Id")

        acc_info = ih.libs["db_secop"].user_has_secacc(user_id, section_id)

        if not acc_info["status"]:
            request.session["error_id"] = "e04"
            raise PermissionError("User doesn't have access to this resource")

        course_info = ih.libs["db_secop"].get_course_info(section_id)
        if not course_info:
            request.session["error_id"] = "e04"
            raise ValueError("Course not found")

        if isinstance(course_info["instructors"], str):
            return {}

        response_data["course"] = {
            "id": course_info["section_id"],
            "name": course_info["section_name"],
            "entryCode": course_info["section_code"],
            "sectionId": section_id,
            "instructors": [{"name": instructor} for instructor in course_info.get("instructors", [])]
        }
        return response_data
    except Exception as exc:
        request.session["error_msg"] = str(exc)
        return redirect_to(safe_url_for(request, "get_section_page", default="/section"))


@router.get("/api/sections/{section_id}/assignments")
def get_section_assignments(section_id: str,
                            request: Request,
                            user_id: str = Depends(get_current_user_id)):
    response_data = {}
    try:
        if not ih.libs["form_helper"].validate_hex_ids(section_id):
            request.session["error_id"] = "e04"
            raise ValueError("Invalid Section Id")

        acc_info = ih.libs["db_secop"].user_has_secacc(user_id, section_id)
        if not acc_info["status"]:
            request.session["error_id"] = "e04"
            raise PermissionError("User doesn't have access to this resource")

        assignments = ih.libs["db_secop"].get_assignments_by_section(section_id)
        response_data["assignments"] = [
            {
                "id": assignment["assn_id"],
                "name": assignment["name"],
                "released": datetime.fromtimestamp(assignment["released"]).isoformat(),
                "due": datetime.fromtimestamp(assignment["due"]).isoformat(),
            }
            for assignment in assignments
        ]
        return response_data
    except Exception as exc:
        request.session["error_msg"] = str(exc)
        return redirect_to(safe_url_for(request, "get_section_page", default="/section"))


@router.get("/section/users")
def get_users_page(request: Request, userid: str = Depends(get_session_user_id)):
    pg_info = {}
    try:
        secid = request.query_params.get("sectionid")
        if not ih.libs["form_helper"].validate_hex_ids(secid):
            request.session["error_id"] = "e04"
            raise ValueError("Invalid Section Id")

        acc_info = ih.libs["db_secop"].user_has_secacc(userid, secid)
        if not acc_info["status"]:
            request.session["error_id"] = "e04"
            raise PermissionError("User doesnt have access to this resource")

        user_info = ih.libs["db_secop"].sec_users_list(secid)
        pg_info["user_info"] = user_info

        if acc_info["role"] != "student":
            links = {"Add People": safe_url_for(request, "get_addusers_page", default="/section/add")}
            pg_info["links"] = links

        return template_response(
            request, "section_users.html", {"pg_info": json_payload(pg_info)}
        )
    except Exception:
        return redirect_to(safe_url_for(request, "get_section_list_page", default="/sections"))


@router.get("/section/create")
def get_create_section_page(request: Request, userid: str = Depends(get_session_user_id)):
    pg_info = {"endpoint_createsec": safe_url_for(request, "create_section", default="/section/createreq")}
    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for Admin")

        ih.libs["form_helper"].add_codes(request.session, pg_info)
        return template_response(
            request, "create_section.html", {"pg_info": json_payload(pg_info)}
        )
    except Exception:
        return redirect_to(safe_url_for(request, "get_section_list_page", default="/sections"))


@router.post("/section/createreq")
async def create_section(request: Request, userid: str = Depends(get_session_user_id)):
    try:
        if not ih.libs["user_auth"].is_admin(userid):
            request.session["error_id"] = "e04"
            raise PermissionError("Only for Admin")

        form = await request.form()
        sec_code = form.get("sec_code")
        sec_name = form.get("sec_name") or None

        if not ih.libs["form_helper"].validate_section_code(sec_code):
            request.session["error_id"] = "e07"
            raise ValueError("Invalid section code")

        if sec_name is not None and not ih.libs["form_helper"].validate_section_name(sec_name):
            request.session["error_id"] = "e07"
            raise ValueError("Invalid section name")

        ih.libs["db_secop"].create_section(section_code=sec_code, section_name=sec_name)
        return redirect_to(safe_url_for(request, "get_section_list_page", default="/sections"))
    except Exception as exc:
        request.session["error_id"] = "e07"
        return redirect_to(safe_url_for(request, "get_create_section_page", default="/section/create"))
