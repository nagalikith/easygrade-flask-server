import import_helper as ih
import subprocess
import json


def make_dir(abs_dir_path):
  subprocess.run(["mkdir \"{}\"".format(abs_dir_path)], check=True, shell=True)

def list_dir_contents(abs_dir_path):
  print(abs_dir_path)
  ls_outp = subprocess.run(["ls \"{}\"".format(abs_dir_path)], capture_output=True, check=True, shell=True)
  ls_str = ls_outp.stdout.decode().strip()
  if (ls_str == ""):
    ls_list = []
  else:
    ls_list = ls_str.split('\n')
  return ls_list

def rm_dir(abs_dir_path):
  subprocess.run(["rm -rf \"{}\"".format(abs_dir_path)], check=True, shell=True)

def write_file(abs_file_path, content, content_type="text"):
  f = open("{}".format(abs_file_path), 'w')
  if (content_type == "text"):
    f.write(content)
  elif (content_type == "json" and type(content) == dict):
    json.dump(content, f)
  else:
    f.close()
    raise(ValueError("Unrecognized Content Type"))
  f.close()

def read_file(abs_file_path, content_type="text"):
  res = ''

  f = open("{}".format(abs_file_path), 'r')

  if (content_type == "text"):
    res = f.read()
  elif (content_type == "json"):
    res = json.load(f)
  else:
    f.close()
    raise(ValueError("Unrecognized Content Type"))

  f.close()
  return res
