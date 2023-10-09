import import_helper as ih
import subprocess
import threading

_lns = ih.get_env_val("SUPP_LANG")
_lcs = ih.get_env_val("LANG_CLASS")

# this dictionary maps lang_name (str) with its corresponding class
lang_class = {_lns[i]:getattr(ih.libs[_lcs[i]], _lcs[i]) for i in range(len(_lns))}

def dict_append(d_src, d_delta):
  for key, val in d_delta.items():
    d_src[key] = val

def set_start_status(subdir_name, dict_d=None):
  res = {"status": "running"}

  if (dict_d != None):
    dict_append(res, dict_d)

  ih.libs["subm_fileop"].write_file_subdir(
    subdir_name, "__output.json", res, "json"
  )

def set_end_status(subdir_name, dict_d=None):
  res = {}
  res["status"] = "Done"

  if (dict_d != None):
    dict_append(res, dict_d)

  ih.libs["subm_fileop"].write_file_subdir(
    subdir_name, "__output.json", res, "json"
  )

  #delete me
  subprocess.run(["tree"], shell=True)

def run_test_case(lo, casenum, end_info):
  exec_statement = "{} < \"{}\" > \"{}\"".format(
    lo.exec_statement(),
    lo.get_full_path("__input_file_{}".format(casenum)),
    lo.get_full_path("__output_file_{}".format(casenum)),
  )

  subprocess.run([exec_statement], shell=True)

  end_info["output_info"][str(casenum)] = ih.libs["subm_fileop"].diff_files(
    end_info["subdir_name"], 
    "__output_file_{}".format(casenum),
    "__expected_output_file_{}".format(casenum)
  )

  end_info["ran_cases"] += 1

  if (end_info["ran_cases"] == end_info["num_cases"]):
    set_end_status(end_info["subdir_name"], end_info["output_info"])


    # uploading code file to s3
    ih.libs["s3_rel"].write_to_s3(
      lo.get_full_path(lo.file_name),
      "submissions/{}/{}".format(
        end_info["subdir_name"], 
        lo.file_name
      )
    )

    # uploading output file to s3
    ih.libs["s3_rel"].write_to_s3(
      lo.get_full_path("__output.json"),
      "submissions/{}/{}".format(
        end_info["subdir_name"], 
        "__output.json"
      )
    )

# this method actually runs the program, by calling the (build and) exec statement of the language object
def run_assn(code_info):
  subdir_name = code_info.get("subdir_info").get("subdir_name")
  lc = lang_class.get(code_info.get("lang"))
  lo = lc(
    code_info.get("file_name"),
    code_info.get("subdir_info").get("subdir_path")
  )

  assn_id = code_info["assn_id"]
  num_cases = ih.libs["subm_fileop"].copy_assn_files_subdir(subdir_name, assn_id)

  set_start_status(subdir_name)

  if (lo.lang_type == "COMPILED"):
    subprocess.run([lo.build_statement()], shell=True)

  end_info = {"ran_cases": 0, "num_cases": num_cases, "subdir_name": subdir_name}

  end_info["output_info"] = {}
  end_info["output_info"]["assn_id"] = assn_id

  for i in range(num_cases):
    tc_thread = threading.Thread(target=run_test_case, args=( lo, i, end_info))
    tc_thread.start() 
