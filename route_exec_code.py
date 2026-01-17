import json
import threading

import import_helper as ih
from fastapi import APIRouter, File, Form, Request, UploadFile

from py_lib.web_helpers import json_payload, safe_url_for, template_response

router = APIRouter()


@router.get("/submission/upload")
def get_upload_page(request: Request):
    assn_id = request.query_params.get("assignment_id")
    pg_info = {
        "assn": ih.libs["assn_fileop"].get_restricted_assignment_dictionary(assn_id),
        "endpoint_upload": safe_url_for(request, "upl_code_params"),
        "endpoint_output": safe_url_for(request, "get_code_output"),
        "check_delay": ih.get_env_val("CHECK_DELAY"),
    }

    pg_info["assn"]["id"] = assn_id
    return template_response(
        request, "upload.html", {"pg_info": json_payload(pg_info)}
    )


@router.post("/submission/report")
def get_code_output(codeOutputToken: str = Form(...)):
    output_resp = ih.libs["subm_fileop"].read_file_subdir(
        codeOutputToken, "__output.json", "json")

    if output_resp["status"] == "Done":
        ih.libs["subm_fileop"].rm_sub_subdir(codeOutputToken)
        return {
            "status": "Done",
            "score": ih.libs["assn_fileop"].calculate_score(output_resp)
        }

    return output_resp


@router.post("/submission/uploadreq")
async def upl_code_params(
    file: UploadFile = File(...),
    sel_lang: str = Form(None),
    assn_id: str = Form(None),
):
    try:
        ih.libs["subm_fileop"].validate_file(file)
        subdir_info = ih.libs["subm_fileop"].make_sub_subdir()
        code_rel_info = {
            "file_name": file.filename,
            "subdir_info": subdir_info,
            "lang": sel_lang,
            "assn_id": assn_id
        }

        content = await file.read()
        with open(f"{subdir_info.get('subdir_path')}{file.filename}", "wb") as handle:
            handle.write(content)

        run_code_thread = threading.Thread(
            target=ih.libs["run_code"].run_assn, args=(code_rel_info,)
        )
        run_code_thread.start()

        return json.dumps({"codeOutputToken": subdir_info.get("subdir_name")})
    except Exception as exc:
        return {"Error": str(exc)}
