import threading
from typing import Dict
import flask
import json
import import_helper as ih
import sqlalchemy as sa
from dotenv import load_dotenv
import boto3
from datetime import datetime
load_dotenv()

from flask_jwt_extended import jwt_required, get_jwt_identity
tables_info = ih.libs["db_schema"].tables_info
bp = flask.Blueprint("assign_op", __name__)
from enum import Enum
ASSIGNMENT_DIR = ih.get_env_val("PATH_ASSN_DIR_PAR")

s3 = boto3.client('s3')
ASSIGNMENT_BUCKET = 'snaga-dev-cleferr-ai'

class AssignmentType(Enum):
    CODE = "code"
    PDF = "pdf"
    IMAGE = "image"

# Route to create an assignment
@bp.route("/assignments", methods=["POST"])
@jwt_required()
def create_assignment():
    authord_id = get_jwt_identity()
    assignment_id = ih.libs["hex_rel"].gen_hex()
    assignment_info = flask.request.form.to_dict()
    
    assignment_path = f"{ASSIGNMENT_DIR}{assignment_id}/"
    ih.libs["fileop_helper"].make_dir(assignment_path)
    
    info_path = f"{assignment_path}__assn_info.json"
    #ih.libs["fileop_helper"].write_file(info_path, assignment_info, "json")
    #ih.libs["s3_rel"].write_to_s3(info_path, f"assignments/{assignment_id}/__assn_info.json")

    assignment_type = AssignmentType(assignment_info.get("assignmentType"))
    if assignment_type == AssignmentType.CODE:
        _setup_code_assignment(assignment_id, assignment_info)
    elif assignment_type in [AssignmentType.PDF, AssignmentType.IMAGE]:
        uploaded_file = flask.request.files.get("template")
        if uploaded_file:
            release_date = assignment_info.get("releaseDate")
            due_date = assignment_info.get("dueDate")
            file_path = f"/tmp/{assignment_id}_{uploaded_file.filename}"
            uploaded_file.save(file_path)

            #upload to s3
            s3_key = f"assignments/{assignment_id}/{uploaded_file.filename}"
            s3.upload_file(file_path, ASSIGNMENT_BUCKET,s3_key)
            assn_url = f"https://{ASSIGNMENT_BUCKET}.s3.amazonaws.com/{s3_key}"
            stmt = sa.insert(tables_info["assn"]["table"]).values(
                assn_id=assignment_id,
                assn_title=assignment_info.get("assignmentName"),
                author_id=authord_id,
                start_epoch=int(datetime.fromisoformat(release_date).timestamp()) if release_date else None,
                end_epoch=int(datetime.fromisoformat(due_date).timestamp()) if due_date else None,
                assn_url=assn_url,
                last_upd=int(datetime.now().timestamp())
            )

            #stmt2 = sa.insert(tables_info["assn_acc"]["table"]).values(
            #    assn_id=assignment_id,
            #    section_id=assignment_info.get("section_id"),
            #    user_id= authord_id
            #)
            # Execute the insert statement
            ih.libs["db_connect"].run_stmt(stmt)
            #ih.libs["db_connect"].run_stmt(stmt2)


    return flask.jsonify({"id": assignment_id})


# To-do
@bp.route("/api/assignment/edit", methods=["PUT"])
def edit_assignment():
    form = flask.request.form
    assn_id = form.get("assn_id")
    file = flask.request.files.get("file")

    if not assn_id or not form:
        return {"error": "Assignment ID and form data are required"}, 400
    
    # Parse the form data
    assignment_data = {
        "assignmentType": form.get("assignmentType"),
        "assignmentName": form.get("assignmentName"),
        "template": form.get("template"),
        "uploadSubmissions": form.get("uploadSubmissions"),
        "releaseDate": form.get("releaseDate"),
        "dueDate": form.get("dueDate"),
        "submissionType": form.get("submissionType"),
    }

    # Process the updated assignment data and file
    assn_dict = ih.libs["form_helper"].create_assn_formdict(assignment_data)
    ih.libs["assn_fileop"].edit_assignment(assn_id, assn_dict, file)
    return {"operation": "successful"}, 200

# Route to delete an assignment
@bp.route("/api/assignment/delete", methods=["DELETE"])
def delete_assignment(): 
    assn_id = flask.request.form.get("assignment_id")
    if not assn_id:
        return {"error": "Assignment ID is required"}, 400

    ih.libs["assn_fileop"].del_assn(assn_id)
    return {"operation": "successful"}, 200

# Route to list assignments
@bp.route("/api/assignments", methods=["GET"])
def list_assignments():
    assn_ids = ih.libs["assn_fileop"].list_assignment_ids()
    assignments = [
        {
            "id": assn_id,
            "title": ih.libs["assn_fileop"].get_assn_prop(assn_id, "title"),
            "description": ih.libs["assn_fileop"].get_assn_prop(assn_id, "description")
        }
        for assn_id in assn_ids
    ]
    return {"assignments": assignments}, 200

# Route to copy an assignment
@bp.route("/api/assignment/copy", methods=["POST"])
def copy_assignment(): 
    assn_id = flask.request.form.get("assignment_id")
    if not assn_id:
        return {"error": "Assignment ID is required"}, 400

    # Logic to copy assignment based on ID
    new_assn_id = ih.libs["assn_fileop"].copy_assignment(assn_id)
    return {"operation": "successful", "new_assignment_id": new_assn_id}, 201

@bp.route("/assignments/<assignment_id>/submissions", methods=["POST"])
def submit_assignment(assignment_id):
    student_id = flask.request.form.get("student_id")
    if not student_id:
        return flask.jsonify({"error": "Student ID required"}), 400

    submission = flask.request.files.get("submission")
    if not submission:
        return flask.jsonify({"error": "Submission file required"}), 400

    submission_dir = f"{ASSIGNMENT_DIR}{assignment_id}/submissions/{student_id}"
    ih.libs["fileop_helper"].make_dir(submission_dir)

    assignment_info = _get_assignment_info(assignment_id)
    assignment_type = AssignmentType(assignment_info.get("exam_type"))

    if assignment_type == AssignmentType.CODE:
        return _handle_code_submission(assignment_id, student_id, submission)
    else:
        return _handle_file_submission(assignment_id, student_id, submission)

def _get_assignment_info(assignment_id: str) -> Dict:
    if assignment_id not in assignment_cache:
        file_path = f"{ASSIGNMENT_DIR}{assignment_id}/__assn_info.json"
        assignment_cache[assignment_id] = ih.libs["fileop_helper"].read_file(file_path, "json")
    return assignment_cache[assignment_id]

def _setup_code_assignment(assignment_id: str, info: Dict):
    threads = []
    for i, test_case in enumerate(info.get("test_cases", [])):
        for file_type in ["input", "output"]:
            thread = threading.Thread(
                target=ih.libs["fileop_helper"].write_file,
                args=(f"{ASSIGNMENT_DIR}{assignment_id}/__{file_type}_file_{i}", 
                      test_case[file_type])
            )
            threads.append(thread)
            thread.start()
    
    for thread in threads:
        thread.join()

def _handle_code_submission(assignment_id: str, student_id: str, submission) -> Dict:
    submission_path = f"{ASSIGNMENT_DIR}{assignment_id}/submissions/{student_id}/submission.py"
    submission.save(submission_path)
    
    ih.libs["s3_rel"].write_to_s3(
        submission_path,
        f"assignments/{assignment_id}/submissions/{student_id}/submission.py"
    )
    
    test_results = _run_tests(assignment_id, submission_path)
    grade = _calculate_grade(assignment_id, test_results)
    
    return jsonify({"grade": grade, "test_results": test_results})

def _handle_file_submission(assignment_id: str, student_id: str, submission) -> Dict:
    filename = secure_filename(submission.filename)
    submission_path = f"{ASSIGNMENT_DIR}{assignment_id}/submissions/{student_id}/{filename}"
    submission.save(submission_path)
    
    ih.libs["s3_rel"].write_to_s3(
        submission_path,
        f"assignments/{assignment_id}/submissions/{student_id}/{filename}"
    )
    
    return flask.jsonify({"status": "success"})

def _delete_assignment_files(assignment_id: str, delete_s3: bool = True):
    ih.libs["fileop_helper"].rm_dir(f"{ASSIGNMENT_DIR}{assignment_id}/")
    if delete_s3:
        ih.libs["s3_rel"].delete_file(f"assignments/{assignment_id}/__assn_info.json")
