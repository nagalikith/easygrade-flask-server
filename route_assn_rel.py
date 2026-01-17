import os
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Dict

import boto3
import import_helper as ih
import json
import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

import py_lib.answer_extractor as answer_extractor
from py_lib.auth_utils import get_current_user_id
from py_lib.web_helpers import safe_url_for

router = APIRouter()
tables_info = ih.libs["db_schema"].tables_info
ASSIGNMENT_DIR = ih.get_env_val("PATH_ASSN_DIR_PAR")
assignment_cache = {}

s3 = boto3.client('s3')
ASSIGNMENT_BUCKET = 'snaga-dev-cleferr-ai'


class AssignmentType(Enum):
    CODE = "code"
    PDF = "pdf"
    IMAGE = "image"


@router.post("/assignments")
async def create_assignment(request: Request,
                            user_id: str = Depends(get_current_user_id)):
    form = await request.form()
    assignment_id = ih.libs["hex_rel"].gen_hex()
    assignment_info = {
        key: value
        for key, value in form.items()
        if key != "template"
    }

    assignment_path = os.path.join(ASSIGNMENT_DIR, assignment_id)
    ih.libs["fileop_helper"].make_dir(assignment_path)

    assignment_type = AssignmentType(assignment_info.get("assignmentType"))
    if assignment_type == AssignmentType.CODE:
        _setup_code_assignment(assignment_id, assignment_info)
    elif assignment_type in [AssignmentType.PDF, AssignmentType.IMAGE]:
        uploaded_file = form.get("template")
        if uploaded_file:
            await _handle_assignment_template_upload(
                assignment_id, user_id, assignment_info, uploaded_file)

    return {"id": assignment_id}


@router.put("/api/assignment/edit")
async def edit_assignment(request: Request):
    form = await request.form()
    assn_id = form.get("assn_id")

    if not assn_id or not form:
        raise HTTPException(status_code=400, detail="Assignment ID and form data are required")

    assignment_data = {
        "assignmentType": form.get("assignmentType"),
        "assignmentName": form.get("assignmentName"),
        "template": form.get("template"),
        "uploadSubmissions": form.get("uploadSubmissions"),
        "releaseDate": form.get("releaseDate"),
        "dueDate": form.get("dueDate"),
        "submissionType": form.get("submissionType"),
    }

    assn_dict = ih.libs["form_helper"].create_assn_formdict(assignment_data)
    ih.libs["assn_fileop"].edit_assignment(assn_id, assn_dict, form.get("file"))
    return {"operation": "successful"}


@router.delete("/api/assignment/delete")
async def delete_assignment(request: Request):
    form = await request.form()
    assn_id = form.get("assignment_id")
    if not assn_id:
        raise HTTPException(status_code=400, detail="Assignment ID is required")

    delete_fn = getattr(ih.libs["assn_fileop"], "delete_assignment", None)
    if delete_fn is None:
        delete_fn = getattr(ih.libs["assn_fileop"], "del_assn", None)
    if delete_fn is None:
        raise HTTPException(status_code=501, detail="Delete not implemented")
    delete_fn(assn_id)
    return {"operation": "successful"}


@router.get("/api/assignments")
def list_assignments():
    assn_ids = ih.libs["assn_fileop"].list_assignment_ids()
    assignments = [
        {
            "id": assn_id,
            "title": ih.libs["assn_fileop"].get_assignment_property(assn_id, "title"),
            "description": ih.libs["assn_fileop"].get_assignment_property(assn_id, "description")
        }
        for assn_id in assn_ids
    ]
    return {"assignments": assignments}


@router.post("/api/assignment/copy")
async def copy_assignment(request: Request):
    form = await request.form()
    assn_id = form.get("assignment_id")
    if not assn_id:
        raise HTTPException(status_code=400, detail="Assignment ID is required")

    copy_fn = getattr(ih.libs["assn_fileop"], "copy_assignment", None)
    if copy_fn is None:
        raise HTTPException(status_code=501, detail="Copy assignment not implemented")
    new_assn_id = copy_fn(assn_id)
    return {"operation": "successful", "new_assignment_id": new_assn_id}


@router.post("/assignments/{assignment_id}/submissions")
async def submit_assignment(assignment_id: str,
                            student_id: str = Form(...),
                            submission: UploadFile = File(...)):
    assignment_info = _get_assignment_info(assignment_id)
    assignment_type = _infer_assignment_type(assignment_info, submission.filename)

    if assignment_type == AssignmentType.CODE:
        return await _handle_code_submission(assignment_id, student_id, submission)
    return await _handle_file_submission(assignment_id, student_id, submission)


def _get_assignment_info(assignment_id: str) -> Dict:
    if assignment_id not in assignment_cache:
        file_path = os.path.join(ASSIGNMENT_DIR, assignment_id, "__assn_info.json")
        if os.path.exists(file_path):
            assignment_cache[assignment_id] = ih.libs["fileop_helper"].read_file(file_path, "json")
        else:
            assignment_cache[assignment_id] = {}
    return assignment_cache[assignment_id]


def _infer_assignment_type(assignment_info: Dict, filename: str) -> AssignmentType:
    assn_type = assignment_info.get("exam_type") or assignment_info.get("assignmentType")
    if assn_type in [member.value for member in AssignmentType]:
        return AssignmentType(assn_type)

    _, ext = os.path.splitext(filename.lower())
    if ext in [".py", ".c", ".cpp", ".rb"]:
        return AssignmentType.CODE
    if ext == ".pdf":
        return AssignmentType.PDF
    return AssignmentType.IMAGE


def _setup_code_assignment(assignment_id: str, info: Dict):
    threads = []
    for i, test_case in enumerate(info.get("test_cases", [])):
        for file_type in ["input", "output"]:
            thread = threading.Thread(
                target=ih.libs["fileop_helper"].write_file,
                args=(os.path.join(ASSIGNMENT_DIR, assignment_id, f"__{file_type}_file_{i}"),
                      test_case[file_type])
            )
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()


async def _handle_assignment_template_upload(assignment_id: str, user_id: str,
                                             assignment_info: Dict,
                                             uploaded_file: UploadFile):
    release_date = assignment_info.get("releaseDate")
    due_date = assignment_info.get("dueDate")
    temp_path = os.path.join("/tmp", f"{assignment_id}_{uploaded_file.filename}")
    await _write_upload_file(uploaded_file, temp_path)

    s3_key = f"assignments/{assignment_id}/{uploaded_file.filename}"
    s3.upload_file(temp_path, ASSIGNMENT_BUCKET, s3_key)
    assn_url = f"https://{ASSIGNMENT_BUCKET}.s3.amazonaws.com/{s3_key}"
    stmt = sa.insert(tables_info["assn"]["table"]).values(
        assn_id=assignment_id,
        assn_title=assignment_info.get("assignmentName"),
        author_id=user_id,
        start_epoch=int(datetime.fromisoformat(release_date).timestamp()) if release_date else None,
        end_epoch=int(datetime.fromisoformat(due_date).timestamp()) if due_date else None,
        assn_url=assn_url,
        last_upd=int(datetime.now().timestamp())
    )
    ih.libs["db_connect"].run_stmt(stmt)


async def _handle_code_submission(assignment_id: str, student_id: str,
                                  submission: UploadFile):
    submission_path = os.path.join(
        ASSIGNMENT_DIR, assignment_id, "submissions", student_id, "submission.py")
    ih.libs["fileop_helper"].make_dir(os.path.dirname(submission_path))
    await _write_upload_file(submission, submission_path)

    test_results = _run_tests(assignment_id, submission_path)
    grade = _calculate_grade(assignment_id, test_results)
    return {"grade": grade, "test_results": test_results}


async def _handle_file_submission(assignment_id: str, student_id: str,
                                  submission: UploadFile):
    submission_id = ih.libs["hex_rel"].gen_hex()
    filename = _safe_filename(submission.filename)
    submission_dir = os.path.join(
        ASSIGNMENT_DIR, assignment_id, "submissions", student_id, submission_id)
    ih.libs["fileop_helper"].make_dir(submission_dir)
    submission_path = os.path.join(submission_dir, filename)
    await _write_upload_file(submission, submission_path)

    answers_dir = os.path.join(submission_dir, "answers")
    assignment_dir = os.path.join(ASSIGNMENT_DIR, assignment_id)
    template_boxes = answer_extractor.load_template_boxes(assignment_dir)
    extraction_error = None
    try:
        answer_extractor.extract_submission_answers(
            submission_path,
            answers_dir,
            template_boxes=template_boxes,
            ocr_enabled=True
        )
    except Exception as exc:
        extraction_error = str(exc)

    meta = {
        "submission_id": submission_id,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "file_name": filename,
        "submitted_at": int(time.time()),
        "answers_index": os.path.join("answers", answer_extractor.DEFAULT_INDEX_NAME)
    }
    ih.libs["fileop_helper"].write_file(
        os.path.join(submission_dir, "submission_meta.json"), meta, "json")

    response = {
        "status": "success",
        "submission_id": submission_id,
        "answers_extracted": extraction_error is None
    }
    if extraction_error:
        response["extraction_error"] = extraction_error
    return response


@router.get("/assignments/{assignment_id}/questions/{question_num}/answers")
def list_question_answers(request: Request, assignment_id: str, question_num: int):
    submissions_root = os.path.join(ASSIGNMENT_DIR, assignment_id, "submissions")
    if not os.path.isdir(submissions_root):
        return {
            "assignment_id": assignment_id,
            "question_num": question_num,
            "answers": []
        }

    answers = []
    for student_id in os.listdir(submissions_root):
        student_dir = os.path.join(submissions_root, student_id)
        if not os.path.isdir(student_dir):
            continue
        for submission_id in os.listdir(student_dir):
            submission_dir = os.path.join(student_dir, submission_id)
            if not os.path.isdir(submission_dir):
                continue
            index_path = os.path.join(
                submission_dir, "answers", answer_extractor.DEFAULT_INDEX_NAME)
            if not os.path.exists(index_path):
                continue
            try:
                with open(index_path, "r") as handle:
                    index = json.load(handle)
            except Exception:
                continue
            for answer in index.get("answers", []):
                if answer.get("question_num") != question_num:
                    continue
                answers.append({
                    "student_id": student_id,
                    "submission_id": submission_id,
                    "page": answer.get("page"),
                    "bbox": answer.get("bbox"),
                    "answer_path": os.path.join(
                        ASSIGNMENT_DIR, assignment_id, "submissions",
                        student_id, submission_id, "answers",
                        answer.get("path", "")),
                    "download_url": safe_url_for(
                        request,
                        "download_answer_file",
                        assignment_id=assignment_id,
                        student_id=student_id,
                        submission_id=submission_id,
                        filename=answer.get("path", "")
                    ),
                    "source_file": index.get("source_file"),
                    "detection": answer.get("source"),
                    "ocr_text": answer.get("ocr_text"),
                    "ocr_confidence": answer.get("ocr_confidence"),
                    "ocr_error": answer.get("ocr_error")
                })

    return {
        "assignment_id": assignment_id,
        "question_num": question_num,
        "answers": answers
    }


@router.get(
    "/assignments/{assignment_id}/submissions/{student_id}/{submission_id}/answers/{filename:path}"
)
def download_answer_file(assignment_id: str, student_id: str,
                         submission_id: str, filename: str):
    answers_dir = os.path.join(
        ASSIGNMENT_DIR, assignment_id, "submissions", student_id, submission_id, "answers")
    if not os.path.isdir(answers_dir):
        raise HTTPException(status_code=404, detail="Answers directory not found")

    safe_root = os.path.abspath(answers_dir)
    safe_path = os.path.abspath(os.path.join(answers_dir, filename))
    if not safe_path.startswith(safe_root + os.sep):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not os.path.isfile(safe_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(safe_path)


def _delete_assignment_files(assignment_id: str, delete_s3: bool = True):
    ih.libs["fileop_helper"].rm_dir(os.path.join(ASSIGNMENT_DIR, assignment_id))
    if delete_s3:
        ih.libs["s3_rel"].delete_file(f"assignments/{assignment_id}/__assn_info.json")


def _run_tests(assignment_id: str, submission_path: str):
    return {}


def _calculate_grade(assignment_id: str, test_results: Dict):
    return 0


async def _write_upload_file(upload_file: UploadFile, destination: str):
    content = await upload_file.read()
    with open(destination, "wb") as handle:
        handle.write(content)


def _safe_filename(filename: str) -> str:
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    return "".join(ch if ch in keep else "_" for ch in filename)
