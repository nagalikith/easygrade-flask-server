import import_helper as ih
import threading

# Path to the directory where assignments are stored, fetched from an environment variable.
assn_dir_path = ih.get_env_val("PATH_ASSN_DIR_PAR")
# Dictionary to store assignment information in memory for quick access.
assn_info_dict = {}

# Retrieves the assignment information for a given assignment ID.
def get_assn_dict(assn_id):
  # If the assignment info is not already in the dictionary, read it from a file.
  if (assn_info_dict.get(assn_id) == None):
    assn_info_dict[assn_id] = read_file_subdir(
      assn_id,
      "__assn_info.json",
      "json"
    )
  return assn_info_dict[assn_id]

# Similar to get_assn_dict, but filters out system info.
def get_assn_dict_nosys(assn_id):
  assn_info = {key:value for key, value in get_assn_dict(assn_id).items() if not(key.startswith("__"))}
  return assn_info

# Calculates the score for an assignment based on test case results.
def calc_score(output_dict):
  assn_id = output_dict["assn_id"]
  test_cases = get_assn_prop(assn_id, "test cases")
  num_cases = get_assn_prop(assn_id, "__len_testcases")

  max_points = get_assn_prop(assn_id, "total points")
  
  tot_rel_grade = 0
  score_frac = 0
  for i in range(num_cases):
    rel_grade = test_cases[i]["rel_grade"]
    tot_rel_grade += rel_grade 
    score_frac += output_dict[str(i)] * rel_grade

  score_frac /= tot_rel_grade
  return (max_points * score_frac)

# Retrieves a specific property of an assignment.
def get_assn_prop(assn_id, prop_name):
  return get_assn_dict(assn_id).get(prop_name)

# Fetches assignment details and formats them for presenting, excluding system properties.
def get_res_assn_dict(assn_id):
  d = {key: val for key, val in get_assn_dict_nosys(assn_id).items()}
  test_cases = d["test cases"]
  del d["test cases"]

  sample_cases = [i for i in test_cases if i["is sample"]]
  d["sample cases"] = [{"input": i["input"], "output": i["output"]} for i in sample_cases]
  return d
# Deletes an assignment's local directory and optionally its S3 file.
def del_assn(assn_id, del_s3=True):
  ih.libs["fileop_helper"].rm_dir(
    "{}{}/".format(assn_dir_path, assn_id)
  )

  if (del_s3):
    ih.libs["s3_rel"].delete_file(
      "assignments/{}/__assn_info.json".format(
        assn_id
      )
    )

  if (assn_info_dict.get(assn_id) != None):
    del assn_info_dict[assn_id]

# Writes a file in a specific subdirectory of the assignment directory.
def write_file_subdir(assn_subdir, file_name, content, content_type="text"):
  ih.libs["fileop_helper"].write_file(
    "{}{}/{}".format(assn_dir_path, assn_subdir, file_name),
    content,
    content_type
  )

# Reads a file from a specific subdirectory of the assignment directory.

def read_file_subdir(assn_subdir, file_name, content_type="text"):
  res = ih.libs["fileop_helper"].read_file(
    "{}{}/{}".format(assn_dir_path, assn_subdir, file_name),
    content_type
  )
  return res

# Creates a new assignment directory, writes assignment info, and handles test cases.

def make_assignment(assn_subdir, assn_info):
  assn_subdir_path = "{}{}/".format(assn_dir_path, assn_subdir)
  ih.libs["fileop_helper"].make_dir(assn_subdir_path)
  write_file_subdir(assn_subdir, "__assn_info.json", assn_info, "json")
  
  ih.libs["s3_rel"].write_to_s3(
    "{}__assn_info.json".format(assn_subdir_path),
    "assignments/{}/__assn_info.json".format(assn_subdir)
  )


  ind = 0
  for test_case in assn_info.get("test cases"):
    # Using threading for concurrent processing of input and output files for test cases.
    inp_thread = threading.Thread(target=write_file_subdir, 
      args=(assn_subdir, "__input_file_{}".format(ind),
        test_case["input"]
      )
    ) 

    outp_thread = threading.Thread(target=write_file_subdir, 
      args=(assn_subdir, "__expected_output_file_{}".format(ind),
        test_case["output"]
      )
    ) 

    inp_thread.start()
    outp_thread.start()

    ind += 1

def create_assignment(assn_info):
  assn_subdir = ih.libs["hex_rel"].gen_hex()
  make_assignment(assn_subdir, assn_info)
  return assn_subdir

def edit_assignment(assn_subdir, assn_info):
  del_assn(assn_subdir, del_s3=False)
  make_assignment(assn_subdir, assn_info)

def list_assignment_ids():
  return (ih.libs["fileop_helper"].list_dir_contents(assn_dir_path))
  
