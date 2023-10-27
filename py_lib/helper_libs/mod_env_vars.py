import json
import import_helper as ih

env_json_full_path = "{}py_lib/helper_libs/env.json".format(ih.ROOT_PATH)

def get_env_dict():
  f = open(env_json_full_path, 'r')
  d = json.load(f)
  f.close()
  return (d)

def upd_env_dict(d):
  f = open(env_json_full_path, 'w')
  json.dump(d, f)
  f.close()
