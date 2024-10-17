import import_helper as ih
import threading
import os
import json
import logging
from typing import Dict, Any, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

assignment_directory_path = ih.get_env_val("PATH_ASSN_DIR_PAR")
assignment_info_dictionary = {}

def get_assignment_dictionary(assignment_id: str) -> Dict[str, Any]:
    """
    Retrieve the assignment dictionary for a given assignment ID.
    If not in memory, read it from the file system.

    Args:
        assignment_id (str): The assignment ID.

    Returns:
        Dict[str, Any]: The assignment dictionary.
    """
    if assignment_id not in assignment_info_dictionary:
        logger.info(f"Reading assignment info for {assignment_id} from file system")
        assignment_info_dictionary[assignment_id] = read_file_subdirectory(assignment_id, "__assn_info.json", "json")
    return assignment_info_dictionary[assignment_id]

def get_assignment_dictionary_no_system(assignment_id: str) -> Dict[str, Any]:
    """
    Get the assignment dictionary without system-specific keys.

    Args:
        assignment_id (str): The assignment ID.

    Returns:
        Dict[str, Any]: The filtered assignment dictionary.
    """
    assignment_info = {key: value for key, value in get_assignment_dictionary(assignment_id).items() if not key.startswith("__")}
    return assignment_info

def calculate_score(output_dictionary: Dict[str, Any]) -> float:
    """
    Calculate the score for a submission based on test case results.

    Args:
        output_dictionary (Dict[str, Any]): Dictionary containing test results.

    Returns:
        float: The calculated score.
    """
    assignment_id = output_dictionary["assn_id"]
    test_cases = get_assignment_property(assignment_id, "test cases")
    number_of_cases = get_assignment_property(assignment_id, "__len_testcases")
    maximum_points = get_assignment_property(assignment_id, "total points")
    
    total_relative_grade = 0
    score_fraction = 0
    for i in range(number_of_cases):
        relative_grade = test_cases[i]["rel_grade"]
        total_relative_grade += relative_grade 
        score_fraction += output_dictionary[str(i)] * relative_grade

    score_fraction /= total_relative_grade
    final_score = maximum_points * score_fraction
    logger.info(f"Calculated score for assignment {assignment_id}: {final_score}")
    return final_score

def get_assignment_property(assignment_id: str, property_name: str) -> Any:
    """
    Get a specific property from the assignment dictionary.

    Args:
        assignment_id (str): The assignment ID.
        property_name (str): The name of the property to retrieve.

    Returns:
        Any: The value of the requested property.
    """
    return get_assignment_dictionary(assignment_id).get(property_name)

def get_restricted_assignment_dictionary(assignment_id: str) -> Dict[str, Any]:
    """
    Get a restricted version of the assignment dictionary, including only sample cases.

    Args:
        assignment_id (str): The assignment ID.

    Returns:
        Dict[str, Any]: The restricted assignment dictionary.
    """
    dictionary = get_assignment_dictionary_no_system(assignment_id)
    test_cases = dictionary.pop("test cases")
    sample_cases = [case for case in test_cases if case["is sample"]]
    dictionary["sample cases"] = [{"input": case["input"], "output": case["output"]} for case in sample_cases]
    return dictionary

def delete_assignment(assignment_id: str, delete_s3: bool = True):
    """
    Delete an assignment from the file system and optionally from S3.

    Args:
        assignment_id (str): The assignment ID to delete.
        delete_s3 (bool, optional): Whether to delete from S3 as well. Defaults to True.
    """
    logger.info(f"Deleting assignment {assignment_id}")
    ih.libs["fileop_helper"].rm_dir(f"{assignment_directory_path}{assignment_id}/")

    if delete_s3:
        ih.libs["s3_rel"].delete_file(f"assignments/{assignment_id}/__assn_info.json")

    assignment_info_dictionary.pop(assignment_id, None)

def write_file_subdirectory(assignment_subdirectory: str, file_name: str, content: Any, content_type: str = "text"):
    """
    Write content to a file in the assignment subdirectory.

    Args:
        assignment_subdirectory (str): The assignment subdirectory.
        file_name (str): The name of the file to write.
        content (Any): The content to write to the file.
        content_type (str, optional): The type of content. Defaults to "text".
    """
    file_path = f"{assignment_directory_path}{assignment_subdirectory}/{file_name}"
    logger.info(f"Writing file: {file_path}")
    ih.libs["fileop_helper"].write_file(file_path, content, content_type)

def read_file_subdirectory(assignment_subdirectory: str, file_name: str, content_type: str = "text") -> Union[str, Dict[str, Any]]:
    """
    Read content from a file in the assignment subdirectory.

    Args:
        assignment_subdirectory (str): The assignment subdirectory.
        file_name (str): The name of the file to read.
        content_type (str, optional): The type of content. Defaults to "text".

    Returns:
        Union[str, Dict[str, Any]]: The content of the file.
    """
    file_path = f"{assignment_directory_path}{assignment_subdirectory}/{file_name}"
    logger.info(f"Reading file: {file_path}")
    return ih.libs["fileop_helper"].read_file(file_path, content_type)

def make_assignment(assignment_subdirectory: str, assignment_info: Dict[str, Any]):
    """
    Create a new assignment.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        assignment_info (Dict[str, Any]): Information about the assignment.
    """
    logger.info(f"Creating new assignment in {assignment_subdirectory}")
    assignment_subdirectory_path = f"{assignment_directory_path}{assignment_subdirectory}/"
    ih.libs["fileop_helper"].make_dir(assignment_subdirectory_path)
    write_file_subdirectory(assignment_subdirectory, "__assn_info.json", assignment_info, "json")
    
    ih.libs["s3_rel"].write_to_s3(
        f"{assignment_subdirectory_path}__assn_info.json",
        f"assignments/{assignment_subdirectory}/__assn_info.json"
    )

    if assignment_info.get("exam_type") == "code":
        _handle_code_assignment(assignment_subdirectory, assignment_info, assignment_subdirectory_path)
    elif assignment_info.get("exam_type") in ["pdf", "image"]:
        _handle_file_assignment(assignment_subdirectory, assignment_info, assignment_subdirectory_path)
    else:
        raise ValueError(f"Unsupported exam type: {assignment_info.get('exam_type')}")

def _handle_code_assignment(assignment_subdirectory: str, assignment_info: Dict[str, Any], assignment_subdirectory_path: str):
    """
    Handle the creation of a code-based assignment.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        assignment_info (Dict[str, Any]): Information about the assignment.
        assignment_subdirectory_path (str): The full path to the assignment subdirectory.
    """
    logger.info(f"Handling code assignment in {assignment_subdirectory}")
    threads = []
    for index, test_case in enumerate(assignment_info.get("test_cases", [])):
        input_thread = threading.Thread(
            target=write_file_subdirectory, 
            args=(assignment_subdirectory, f"__input_file_{index}", test_case["input"])
        )
        output_thread = threading.Thread(
            target=write_file_subdirectory, 
            args=(assignment_subdirectory, f"__expected_output_file_{index}", test_case["output"])
        )
        threads.extend([input_thread, output_thread])
        input_thread.start()
        output_thread.start()

    for thread in threads:
        thread.join()

def _handle_file_assignment(assignment_subdirectory: str, assignment_info: Dict[str, Any], assignment_subdirectory_path: str):
    """
    Handle the creation of a file-based assignment (PDF or image).

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        assignment_info (Dict[str, Any]): Information about the assignment.
        assignment_subdirectory_path (str): The full path to the assignment subdirectory.
    """
    logger.info(f"Handling file assignment in {assignment_subdirectory}")
    file_path = assignment_info.get("file_path")
    if not file_path:
        raise ValueError("File path not provided for PDF/image assignment")

    file_name = os.path.basename(file_path)
    destination_path = os.path.join(assignment_subdirectory_path, file_name)
    
    ih.libs["fileop_helper"].copy_file(file_path, destination_path)
    
    ih.libs["s3_rel"].write_to_s3(
        destination_path,
        f"assignments/{assignment_subdirectory}/{file_name}"
    )

    answer_key_path = assignment_info.get("answer_key_path")
    if answer_key_path:
        key_name = os.path.basename(answer_key_path)
        key_destination_path = os.path.join(assignment_subdirectory_path, key_name)
        ih.libs["fileop_helper"].copy_file(answer_key_path, key_destination_path)
        ih.libs["s3_rel"].write_to_s3(
            key_destination_path,
            f"assignments/{assignment_subdirectory}/{key_name}"
        )

def handle_submission(assignment_subdirectory: str, student_id: str, submission_file: Any) -> Dict[str, Any]:
    """
    Handle a student's submission for an assignment.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        student_id (str): The ID of the student submitting the assignment.
        submission_file (Any): The submitted file or content.

    Returns:
        Dict[str, Any]: The result of processing the submission.
    """
    logger.info(f"Handling submission for assignment {assignment_subdirectory} from student {student_id}")
    assignment_info = get_assignment_dictionary(assignment_subdirectory)
    submission_directory = os.path.join(assignment_directory_path, assignment_subdirectory, "submissions", student_id)
    ih.libs["fileop_helper"].make_dir(submission_directory)

    if assignment_info.get("exam_type") == "code":
        return _handle_code_submission(assignment_subdirectory, student_id, submission_file, submission_directory)
    elif assignment_info.get("exam_type") in ["pdf", "image"]:
        return _handle_file_submission(assignment_subdirectory, student_id, submission_file, submission_directory)
    else:
        raise ValueError(f"Unsupported exam type: {assignment_info.get('exam_type')}")

def _handle_code_submission(assignment_subdirectory: str, student_id: str, submission_file: Any, submission_directory: str) -> Dict[str, Any]:
    """
    Handle a code submission for an assignment.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        student_id (str): The ID of the student submitting the assignment.
        submission_file (Any): The submitted code file.
        submission_directory (str): The directory to save the submission.

    Returns:
        Dict[str, Any]: The result of processing the code submission.
    """
    logger.info(f"Handling code submission for assignment {assignment_subdirectory} from student {student_id}")
    submission_path = os.path.join(submission_directory, "submission.py")
    with open(submission_path, "w") as f:
        f.write(submission_file.read())
    
    ih.libs["s3_rel"].write_to_s3(
        submission_path,
        f"assignments/{assignment_subdirectory}/submissions/{student_id}/submission.py"
    )
    
    # Run tests and grade submission
    test_results = run_tests(assignment_subdirectory, submission_path)
    grade = calculate_grade(test_results)
    
    return {"status": "success", "grade": grade, "test_results": test_results}

def _handle_file_submission(assignment_subdirectory: str, student_id: str, submission_file: Any, submission_directory: str) -> Dict[str, Any]:
    """
    Handle a file submission (PDF or image) for an assignment.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        student_id (str): The ID of the student submitting the assignment.
        submission_file (Any): The submitted file.
        submission_directory (str): The directory to save the submission.

    Returns:
        Dict[str, Any]: The result of processing the file submission.
    """
    logger.info(f"Handling file submission for assignment {assignment_subdirectory} from student {student_id}")
    file_name = submission_file.filename
    submission_path = os.path.join(submission_directory, file_name)
    submission_file.save(submission_path)
    
    ih.libs["s3_rel"].write_to_s3(
        submission_path,
        f"assignments/{assignment_subdirectory}/submissions/{student_id}/{file_name}"
    )
    
    return {"status": "success", "message": "Submission received successfully"}

# Placeholder functions - these would need to be implemented based on your specific requirements
def run_tests(assignment_subdirectory: str, submission_path: str) -> List[Dict[str, Any]]:
    """
    Run tests on a code submission.

    Args:
        assignment_subdirectory (str): The subdirectory for the assignment.
        submission_path (str): The path to the submitted code file.

    Returns:
        List[Dict[str, Any]]: The results of running the tests.
    """
    logger.info(f"Running tests for submission in {assignment_subdirectory}")
    # Implementation for running tests on code submissions
    pass

def calculate_grade(test_results: List[Dict[str, Any]]) -> float:
    """
    Calculate the grade based on test results.

    Args:
        test_results (List[Dict[str, Any]]): The results of running the tests.

    Returns:
        float: The calculated grade.
    """
    logger.info("Calculating grade based on test results")
    assn_id = test_results["assn_id"]
    test_cases = get_assignment_property(assn_id, "test cases")
    num_cases = get_assignment_property(assn_id, "__len_testcases")
    max_points = get_assignment_property(assn_id, "total points")
    
    tot_rel_grade = sum(case["rel_grade"] for case in test_cases[:num_cases])
    score_frac = sum(test_results[str(i)] * test_cases[i]["rel_grade"] for i in range(num_cases))
    
    return max_points * (score_frac / tot_rel_grade)

def create_assignment(assn_info):
  assn_subdir = ih.libs["hex_rel"].gen_hex()
  make_assignment(assn_subdir, assn_info)
  return assn_subdir

def edit_assignment(assn_subdir, assn_info):
  delete_assignment(assn_subdir, del_s3=False)
  make_assignment(assn_subdir, assn_info)

def list_assignment_ids():
  return (ih.libs["fileop_helper"].list_dir_contents(assignment_directory_path))
  
