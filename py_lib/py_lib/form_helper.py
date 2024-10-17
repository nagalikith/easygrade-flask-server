import json
import time

from flask import request
import import_helper as ih
create_assn_fields = (("sel_lang", "json"), ("title", "text"), ("description", "text"), ("total points", "int"), ("max attempts", "int"), ("test cases", "json"))

def add_codes(sc, res_dict):
  
  if (sc.get("error_id") != None):
    res_dict["error_id"] = sc["error_id"]
    del sc["error_id"]

  if (sc.get("succ_id") != None):
    res_dict["succ_id"] = sc["succ_id"]
    del sc["succ_id"]

def create_json_dict(field_list):
    """
    Converts JSON data from a Flask request into a dictionary
    based on the specified field types.

    :param field_list: A list of tuples where each tuple contains 
                       a field name and its expected type (e.g., 'text', 'int', 'float', 'json').
    :raises ValueError: If a required field is missing or an invalid field type is provided.
    :return: A dictionary containing the processed fields.
    """
    # Get JSON data from the request
    data = request.get_json()

    if data is None:
        raise ValueError("No JSON data provided")

    res = {}
    for field_name, field_type in field_list:
        if field_name not in data:
            raise ValueError("Required field '{}' not present in JSON".format(field_name))
        else:
            if field_type == "text":
                res[field_name] = data[field_name]
            elif field_type == "int":
                res[field_name] = int(data[field_name])
            elif field_type == "float":
                res[field_name] = float(data[field_name])
            elif field_type == "json":
                res[field_name] = json.loads(data[field_name])
            else:
                raise ValueError("Invalid field type '{}' for field '{}'".format(field_type, field_name))

    return res

def create_assn_formdict(form):
  res = create_json_dict(form, create_assn_fields)
  res["__last_modified"] = time.time()
  res["__len_testcases"] = len(res["test cases"])
  return res

def validate_email(email):
  sp_email = email.split('@')
  if (len(email) < 100 and len(sp_email) == 2):
    if (len(sp_email[0]) > 0 and len(sp_email[1]) > 0):
      return True
  return False

def validate_section_code(sec_code):
  if (len(sec_code) > 30):
    return False
  return True

def validate_section_name(sec_name):
  if (len(sec_name) > 100):
    return False
  return True

def validate_hex_ids(val):
  return (ih.libs["hex_rel"].check_hex(val))
