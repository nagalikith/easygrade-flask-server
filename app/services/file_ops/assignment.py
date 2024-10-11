import import_helper as ih
import threading

# Path to the directory where assignments are stored, fetched from an environment variable.
# Get the base path for assignments from the environment variable
assn_dir_path = ih.get_env_val("PATH_ASSN_DIR_PAR")

# Dictionary to cache assignment information to avoid repeated file reads
assn_info_dict = {}

# Retrieves the assignment information for a given assignment ID.
def get_assn_dict(assn_id):
    """
    Retrieves the assignment dictionary from cache if available, otherwise reads it from the filesystem.
    Caches the result for future use.
    
    :param assn_id: The assignment ID
    :return: Assignment dictionary
    """
    if assn_id not in assn_info_dict:
        assn_info_dict[assn_id] = read_file_subdir(assn_id, "__assn_info.json", "json")
    return assn_info_dict[assn_id]

# Similar to get_assn_dict, but filters out system info.
def get_assn_dict_nosys(assn_id):
    """
    Returns the assignment dictionary excluding any system fields (fields starting with '__').
    
    :param assn_id: The assignment ID
    :return: Filtered assignment dictionary without system fields
    """
    return {key: value for key, value in get_assn_dict(assn_id).items() if not key.startswith("__")}

def calc_score(output_dict):
    """
    Calculates the score based on the output dictionary and test cases.

    :param output_dict: Dictionary containing the outputs for each test case
    :return: Calculated score
    """
    assn_id = output_dict["assn_id"]
    test_cases = get_assn_prop(assn_id, "test cases")
    num_cases = get_assn_prop(assn_id, "__len_testcases")
    max_points = get_assn_prop(assn_id, "total points")
    
    tot_rel_grade = sum(tc["rel_grade"] for tc in test_cases)
    score_frac = sum(output_dict[str(i)] * test_cases[i]["rel_grade"] for i in range(num_cases))
    
    return max_points * (score_frac / tot_rel_grade)

def get_assn_prop(assn_id, prop_name):
    """
    Retrieves a specific property from the assignment dictionary.

    :param assn_id: The assignment ID
    :param prop_name: The property name to retrieve
    :return: The value of the specified property
    """
    return get_assn_dict(assn_id).get(prop_name)

# Fetches assignment details and formats them for presenting, excluding system properties.
def get_res_assn_dict(assn_id):
    """
    Retrieves the assignment dictionary for the response, filtering out test cases and including only sample cases.

    :param assn_id: The assignment ID
    :return: Assignment dictionary with sample cases
    """
    d = get_assn_dict_nosys(assn_id)
    test_cases = d.pop("test cases")
    
    d["sample cases"] = [{"input": tc["input"], "output": tc["output"]} for tc in test_cases if tc.get("is sample")]
    return d

def del_assn(assn_id, del_s3=True):
    """
    Deletes the assignment files from the local filesystem and optionally from S3.

    :param assn_id: The assignment ID
    :param del_s3: Whether to delete from S3 as well
    """
    ih.libs["fileop_helper"].rm_dir(f"{assn_dir_path}{assn_id}/")
    
    if del_s3:
        ih.libs["s3_rel"].delete_file(f"assignments/{assn_id}/__assn_info.json")
    
    if assn_id in assn_info_dict:
        del assn_info_dict[assn_id]

# Writes a file in a specific subdirectory of the assignment directory.
def write_file_subdir(assn_subdir, file_name, content, content_type="text"):
    """
    Writes content to a file in the assignment subdirectory.
    
    :param assn_subdir: The subdirectory of the assignment
    :param file_name: The name of the file to write to
    :param content: The content to write
    :param content_type: The content type (e.g., 'text' or 'json')
    """
    ih.libs["fileop_helper"].write_file(f"{assn_dir_path}{assn_subdir}/{file_name}", content, content_type)

def read_file_subdir(assn_subdir, file_name, content_type="text"):
    """
    Reads content from a file in the assignment subdirectory.

    :param assn_subdir: The subdirectory of the assignment
    :param file_name: The name of the file to read
    :param content_type: The content type (e.g., 'text' or 'json')
    :return: The content read from the file
    """
    return ih.libs["fileop_helper"].read_file(f"{assn_dir_path}{assn_subdir}/{file_name}", content_type)

def make_assignment(assn_subdir, assn_info):
    """
    Creates a new assignment by writing metadata and test cases to the filesystem and uploading to S3.

    :param assn_subdir: The subdirectory where the assignment files will be stored
    :param assn_info: The assignment information dictionary
    """
    assn_subdir_path = f"{assn_dir_path}{assn_subdir}/"
    ih.libs["fileop_helper"].make_dir(assn_subdir_path)
    
    write_file_subdir(assn_subdir, "__assn_info.json", assn_info, "json")
    
    # Upload assignment info to S3
    ih.libs["s3_rel"].write_to_s3(f"{assn_subdir_path}__assn_info.json", f"assignments/{assn_subdir}/__assn_info.json")

    # Multithreaded writing of test case files
    for ind, test_case in enumerate(assn_info.get("test cases", [])):
        threading.Thread(target=write_file_subdir, args=(assn_subdir, f"__input_file_{ind}", test_case["input"])).start()
        threading.Thread(target=write_file_subdir, args=(assn_subdir, f"__expected_output_file_{ind}", test_case["output"])).start()

def create_assignment(assn_info):
    """
    Generates a new unique subdirectory for the assignment, creates the assignment, and returns the subdirectory.

    :param assn_info: The assignment information dictionary
    :return: The generated assignment subdirectory
    """
    assn_subdir = ih.libs["hex_rel"].gen_hex()
    make_assignment(assn_subdir, assn_info)
    return assn_subdir

def edit_assignment(assn_subdir, assn_info):
    """
    Edits an existing assignment by deleting the current version (without removing from S3) and recreating it.

    :param assn_subdir: The subdirectory where the assignment files are stored
    :param assn_info: The updated assignment information
    """
    del_assn(assn_subdir, del_s3=False)
    make_assignment(assn_subdir, assn_info)

def list_assignment_ids():
    """
    Lists all assignment IDs (subdirectories) present in the assignment directory.

    :return: A list of assignment IDs
    """
    return ih.libs["fileop_helper"].list_dir_contents(assn_dir_path)
