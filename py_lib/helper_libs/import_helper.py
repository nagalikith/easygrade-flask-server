import json
import sys

#for easy import of libraries and fetching of environment variables

#change this to the root document of your project
ROOT_PATH = "<APP_ROOT_DIR>"

sys.path.insert(0, ROOT_PATH)

#will be used to store the imported libraries as dictionaries
libs = {}

#loads the environment variables
f = open("{}/py_lib/helper_libs/.env.json".format(
  ROOT_PATH
))
env = json.load(f)
f.close()

# method to get environment variables
def get_env_val(var_name, return_type=None):
  res = None
  if (var_name.startswith("PATH")):
    res = "{}{}".format(
      ROOT_PATH,
      env.get(var_name)
    )
  else:
    res = (env.get(var_name))

  if (return_type == "json" and type(res) == dict):
    return (json.dumps(res))
  else:
    return (res)

import py_lib.gen_hex as gen_hex
libs["gen_hex"] = gen_hex

import py_lib.handle_fileop as handle_fileop
libs["handle_fileop"] = handle_fileop

import py_lib.run_lang.Lang as Lang
libs["Lang"] = Lang

import py_lib.run_lang.LangCPP as LangCPP
libs["LangCPP"] = LangCPP

import py_lib.run_lang.LangC as LangC
libs["LangC"] = LangC

import py_lib.run_lang.LangPython as LangPython
libs["LangPython"] = LangPython

import py_lib.run_lang.LangRuby as LangRuby
libs["LangRuby"] = LangRuby

import py_lib.run_lang.run_code as run_code
libs["run_code"] = run_code
