import json
import sys

#for easy import of libraries and fetching of environment variables

#change this to the root document of your project
ROOT_PATH = "/home/snaga/easygrade-flask-server"

sys.path.insert(0, ROOT_PATH)

#will be used to store the imported libraries as dictionaries
libs = {}

#loads the environment variables
f = open("{}/py_lib/helper_libs/env.json".format(
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

import py_lib.hex_rel as hex_rel
libs["hex_rel"] = hex_rel

import py_lib.form_helper as form_helper
libs["form_helper"] = form_helper

import py_lib.user_auth as user_auth
libs["user_auth"] = user_auth

import py_lib.aws_rel.s3_rel as s3_rel
libs["s3_rel"] = s3_rel

import py_lib.db_libs.db_connect as db_connect
libs["db_connect"] = db_connect

import py_lib.db_libs.db_schema as db_schema
libs["db_schema"] = db_schema

import py_lib.db_libs.db_userop as db_userop
libs["db_userop"] = db_userop

import py_lib.db_libs.db_secop as db_secop
libs["db_secop"] = db_secop

import py_lib.fileop_libs.fileop_helper as fileop_helper
libs["fileop_helper"] = fileop_helper

import py_lib.fileop_libs.subm_fileop as subm_fileop
libs["subm_fileop"] = subm_fileop

import py_lib.fileop_libs.assn_fileop as assn_fileop
libs["assn_fileop"] = assn_fileop

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

handle_login = user_auth.handle_login
