import json
import time
import import_helper as ih
create_assn_fields = (("sel_lang", "json"), ("title", "text"), ("description", "text"), ("total points", "int"), ("max attempts", "int"), ("test cases", "json"))

def add_codes(sc, res_dict):
  
  if (sc.get("error_id") != None):
    res_dict["error_id"] = sc["error_id"]
    del sc["error_id"]

  if (sc.get("succ_id") != None):
    res_dict["succ_id"] = sc["succ_id"]
    del sc["succ_id"]

def create_formdict(form, field_list):
  res = {}
  for field_name, field_type in field_list:
    if (form.get(field_name) == None):
      raise ValueError("Required field {} not present in form".format(field_name))
    else:
      if (field_type == "text"):
        res[field_name] = form.get(field_name)
      elif (field_type == "int"):
        res[field_name] = int(form.get(field_name))
      elif (field_type == "float"):
        res[field_name] = float(form.get(field_name))
      elif (field_type == "json"):
        res[field_name] = json.loads(form.get(field_name))
      else:
        raise ValueError("Invalid field type {}".format(field_type))
  
  return res

def create_assn_formdict(form):
  res = create_formdict(form, create_assn_fields)
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
