import json
import time
import import_helper as ih

# Field definitions for the assignment form
create_assn_fields = [
    ("sel_lang", "json"),
    ("title", "text"),
    ("description", "text"),
    ("total points", "int"),
    ("max attempts", "int"),
    ("test cases", "json")
]

# Add codes for success and error identifiers to the response dictionary
def add_codes(sc, res_dict):
    for code_type in ["error_id", "succ_id"]:
        if sc.get(code_type) is not None:
            res_dict[code_type] = sc[code_type]
            del sc[code_type]

# Create a dictionary from the form using specified field names and types
def create_formdict(form, field_list):
    res = {}
    for field_name, field_type in field_list:
        field_value = form.get(field_name)
        if field_value is None:
            raise ValueError(f"Required field {field_name} not present in form")

        res[field_name] = parse_field_value(field_value, field_type, field_name)
    return res

# Helper function to parse individual field values based on their type
def parse_field_value(value, field_type, field_name):
    try:
        if field_type == "text":
            return value
        elif field_type == "int":
            return int(value)
        elif field_type == "float":
            return float(value)
        elif field_type == "json":
            return json.loads(value)
        else:
            raise ValueError(f"Invalid field type for {field_name}: {field_type}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error parsing field {field_name}: {str(e)}")

# Create the form dictionary for an assignment, adding metadata
def create_assn_formdict(form):
    res = create_formdict(form, create_assn_fields)
    res["__last_modified"] = time.time()
    res["__len_testcases"] = len(res["test cases"])
    return res

# Validate email format
def validate_email(email):
    sp_email = email.split('@')
    return len(email) < 100 and len(sp_email) == 2 and len(sp_email[0]) > 0 and len(sp_email[1]) > 0

# Validate section code based on length
def validate_section_code(sec_code):
    return len(sec_code) <= 30

# Validate section name based on length
def validate_section_name(sec_name):
    return len(sec_name) <= 100

# Validate hexadecimal ID using the imported hex library
def validate_hex_ids(val):
    return ih.libs["hex_rel"].check_hex(val)
