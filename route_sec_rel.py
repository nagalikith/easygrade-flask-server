## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import datetime
import py_lib.helper_libs.import_helper as ih
import flask
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify, make_response, request

bp = flask.Blueprint("/api/sections", __name__)
class Config:
   CORS_ORIGIN = "http://localhost:3000"
   COOKIE_SECURE = False  # Set to True in production
   COOKIE_SAMESITE = 'Lax'

@bp.before_app_request
def handle_cors_preflight():
    """Handle CORS preflight requests."""
    if request.method == 'OPTIONS':
        response = make_response()  # Create a response
        response.headers.update({
            'Access-Control-Allow-Origin': Config.CORS_ORIGIN,
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        })
        return response, 200  # Return 200 OK status

def get_term_from_date(date_str):
    """Helper function to determine the term based on the date"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month = date.month
    year = date.year
    
    if month >= 8 and month <= 12:
        return f"Fall {year}"
    elif month >= 1 and month <= 5:
        return f"Spring {year}"
    else:
        return f"Summer {year}"

@bp.route("/api/sections", methods=['GET'])
@jwt_required()
def get_sections():
    try:
        userid = get_jwt_identity()
        
        # Get sections based on user role
        if ih.libs["user_auth"].is_admin(userid):
            data = ih.libs["db_secop"].admin_sectionview()
        else:
            data = ih.libs["db_secop"].get_sectionview(userid)
        
        # Initialize the response structure
        formatted_response = {
            "status": True,
            "courses": {}  # Will be organized by terms
        }
        
        # Process each section
        for i in range(len(data['section_id'])):
            # Get the term for this section
            # Assuming there's a start_date field in your data
            term = get_term_from_date(data['start_date'][i]) if 'start_date' in data else "Fall 2023"
            
            # Create section data
            section_data = {
                "title": data['section_name'][i],
                "subtitle": f"Section {data['section_code'][i]}",
                "assignmentCount": data.get('assignment_count', [0])[i] if 'assignment_count' in data else 0,
                "sectionId": str(data['section_id'][i]),  # Convert to string to ensure JSON compatibility
                "instructor": data.get('instructor_name', [''])[i] if 'instructor_name' in data else '',
                "enrollmentCount": data.get('enrollment_count', [0])[i] if 'enrollment_count' in data else 0,
                "startDate": data.get('start_date', [''])[i] if 'start_date' in data else '',
                "endDate": data.get('end_date', [''])[i] if 'end_date' in data else ''
            }
            
            # Initialize the term list if it doesn't exist
            if term not in formatted_response["courses"]:
                formatted_response["courses"][term] = []
            
            # Add the section to the appropriate term
            formatted_response["courses"][term].append(section_data)
        
        # Sort sections within each term by title
        for term in formatted_response["courses"]:
            formatted_response["courses"][term].sort(key=lambda x: x["title"])
        
        return jsonify(formatted_response), 200
    
    except Exception as e:
        # Log the error for debugging (implement proper logging)
        print(f"Error in get_sections: {str(e)}")
        
        return jsonify({
            "status": False,
            "error": "Failed to fetch courses. Please try again later.",
            "debug_message": str(e)  # Remove in production
        }), 500

@bp.route("/api/sections/<string:section_id>", methods=["GET"])
@jwt_required()
def get_section(section_id):
    userid = get_jwt_identity()
    response_data = {}

    try:
        # Validate section_id
        if not ih.libs["form_helper"].validate_hex_ids(section_id):
            flask.session["error_id"] = "e04"
            raise ValueError("Invalid Section Id")

        # Check if the user has access to the section
        acc_info = ih.libs["db_secop"].user_has_secacc(userid, section_id)

        if not acc_info["status"]:
            flask.session["error_id"] = "e04"
            raise PermissionError("User doesn't have access to this resource")

        # Fetch the course information
        course_info = ih.libs["db_secop"].get_course_info(section_id)

        if not course_info:
            flask.session["error_id"] = "e04"
            raise ValueError("Course not found")

        # Populate the course data
        response_data["course"] = {
            "id": course_info["id"],
            "name": course_info["name"],
            "term": course_info["term"],
            "description": course_info["description"],
            "entryCode": course_info["entry_code"],
            "sectionId": section_id,
            "instructors": [
                {"id": instructor["id"], "name": instructor["name"], "role": instructor["role"]}
                for instructor in course_info["instructors"]
            ]
        }

        # Include available links based on user role
        links = {}
        links["Assignments"] = flask.url_for("get_section_assignments", section_id=section_id)
        links["People"] = flask.url_for("sec_rel.get_users_page")

        if acc_info["role"] == "student":
            links["Results"] = flask.url_for("sec_rel.get_user_result_page")
        else:
            links["Create Assignment"] = flask.url_for("assign_op.get_create_assignment_page")
            links["Results"] = flask.url_for("sec_rel.get_sec_result_page")

        response_data["links"] = links

        return flask.jsonify(response_data)

    except Exception as e:
        # Log the error and redirect to the section page if an issue occurs
        flask.session["error_msg"] = str(e)
        return flask.redirect(flask.url_for("sec_rel.get_section_page"))


@bp.route("/api/sections/<string:section_id>/assignments", methods=["GET"])
@jwt_required()
def get_section_assignments(section_id):
    userid = flask.request.cookies.get('user_id_cookie')
    response_data = {}

    try:
        # Validate section_id
        if not ih.libs["form_helper"].validate_hex_ids(section_id):
            flask.session["error_id"] = "e04"
            raise ValueError("Invalid Section Id")

        # Check if the user has access to the section
        acc_info = ih.libs["db_secop"].user_has_secacc(userid, section_id)

        if acc_info["status"]:
            flask.session["error_id"] = "e04"
            raise PermissionError("User doesn't have access to this resource")

        # Fetch assignments for the given section
        assignments = ih.libs["db_secop"].get_assignments_by_section(section_id)

        # Format assignments data
        response_data["assignments"] = [
            {
                "id": assignment["id"],
                "name": assignment["name"],
                "released": assignment["released"],
                "due": assignment["due"],
                "submissions": assignment["submissions"],
                "graded": assignment["graded"],
                "published": assignment["published"],
                "regrades": assignment.get("regrades")
            }
            for assignment in assignments
        ]

        return flask.jsonify(response_data)

    except Exception as e:
        # Log the error and redirect to the section page if an issue occurs
        flask.session["error_msg"] = str(e)
        return flask.redirect(flask.url_for("sec_rel.get_section_page"))

@bp.route("/section/users")

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
