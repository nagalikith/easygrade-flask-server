import import_helper as ih
import subprocess

_lns = ih.get_env_val("SUPP_LANG")
_lcs = ih.get_env_val("LANG_CLASS")

# this dictionary maps lang_name (str) with its corresponding class
lang_class = {_lns[i]:getattr(ih.libs[_lcs[i]], _lcs[i]) for i in range(len(_lns))}

def set_start_status(subdir_name):
  res = {"status": "running"}
  ih.libs["handle_fileop"].write_file_subdir(
    subdir_name, "output.json", res, "json"
  )

def set_end_status(subdir_name):
  res = {}
  res["status"] = "Done"
  res["output"] = ih.libs["handle_fileop"].read_file_subdir(subdir_name, "output_file")
  ih.libs["handle_fileop"].write_file_subdir(
    subdir_name, "output.json", res, "json"
  )

# this method actually runs the program, by calling the (build and) exec statement of the language object
def run_code(code_info):
  subdir_name = code_info.get("subdir_info").get("subdir_name")
  lc = lang_class.get(code_info.get("lang"))
  lo = lc(
    code_info.get("file_name"),
    code_info.get("subdir_info").get("subdir_path")
  )
  
  inp_path = lo.get_full_path("input_file")
  out_path = lo.get_full_path("output_file")

  set_start_status(subdir_name)
  ih.libs["handle_fileop"].write_file_subdir(
    subdir_name,
    "input_file",
    code_info.get("input")
  )

  if (lo.lang_type == "COMPILED"):
    subprocess.run([lo.build_statement()], shell=True)

  exec_statement = "{} < \"{}\" > \"{}\"".format(
    lo.exec_statement(),
    inp_path,
    out_path
  )

  subprocess.run([exec_statement], shell=True)
  set_end_status(subdir_name)
