import json
import sys
import os

# Define the root path of your project. You can make this dynamic or environment-based.
ROOT_PATH = os.path.abspath("/Users/nagalikiths/Desktop/Easy Grade/easygrade-flask-server/")
sys.path.insert(0, ROOT_PATH)

# Dictionary to store dynamically imported libraries
libs = {}

# Load environment variables
ENV_PATH = os.path.join(ROOT_PATH, "py_lib/helper_libs/env.json")

try:
    with open(ENV_PATH, 'r') as f:
        env = json.load(f)
except FileNotFoundError:
    print(f"Error: Environment file not found at {ENV_PATH}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Failed to parse the environment file at {ENV_PATH}")
    sys.exit(1)

# Function to get environment variables
def get_env_val(var_name, return_type=None):
    value = env.get(var_name)

    # Prefix ROOT_PATH if it's a PATH variable
    if var_name.startswith("PATH"):
        value = os.path.join(ROOT_PATH, value) if value else None

    # Handle return types (e.g., JSON)
    if return_type == "json" and isinstance(value, dict):
        return json.dumps(value)
    return value

# Dynamic importing of libraries and assigning them to `libs` dictionary
def import_lib(module_name, alias=None):
    try:
        module = __import__(module_name, fromlist=[''])
        libs[alias if alias else module_name] = module
    except ImportError as e:
        print(f"Error importing {module_name}: {str(e)}")

# List of libraries to import, in (module_path, alias) format
lib_imports = [
    ("py_lib.hex_rel", "hex_rel"),
    ("py_lib.form_helper", "form_helper"),
    ("py_lib.user_auth", "user_auth"),
    ("py_lib.aws_rel.s3_rel", "s3_rel"),
    ("py_lib.db_libs.db_connect", "db_connect"),
    ("py_lib.db_libs.db_schema", "db_schema"),
    ("py_lib.db_libs.db_userop", "db_userop"),
    ("py_lib.db_libs.db_secop", "db_secop"),
    ("py_lib.fileop_libs.fileop_helper", "fileop_helper"),
    ("py_lib.fileop_libs.subm_fileop", "subm_fileop"),
    ("py_lib.fileop_libs.assn_fileop", "assn_fileop"),
    ("py_lib.run_lang.Lang", "Lang"),
    ("py_lib.run_lang.LangCPP", "LangCPP"),
    ("py_lib.run_lang.LangC", "LangC"),
    ("py_lib.run_lang.LangPython", "LangPython"),
    ("py_lib.run_lang.LangRuby", "LangRuby"),
    ("py_lib.run_lang.run_code", "run_code"),
]

# Dynamically import all listed libraries
for lib_path, lib_alias in lib_imports:
    import_lib(lib_path, lib_alias)

# Example usage: user_auth is loaded and accessible in libs
handle_login = libs["user_auth"].handle_login
