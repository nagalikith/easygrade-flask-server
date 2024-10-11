import import_helper as ih
import subprocess
import json

# set the max length of hex code generated to 20 chars
ih.libs["gen_hex"].config["length"] = 20

#stores the submission directory-path
sub_dir_path = ih.get_env_val("PATH_UPL_DIR_PAR")

#makes a subdircetory in the submission folder, and returns the subdirectory information
def make_sub_subdir():
  subdir_name = ih.libs["gen_hex"].gen_hex()
  run_cond = 1

  while (run_cond):
    try:
      subprocess.run(
          ["mkdir \"{}{}\"".format(sub_dir_path, subdir_name)], 
          shell=True
        )
      run_cond = 0
    except:
      subdir_name = ih.libs["gen_hex"].gen_hex()
    
  res = {
    "subdir_path": "{}{}/".format(
      sub_dir_path,
      subdir_name
    ),
    "subdir_name": subdir_name
  }
  
  return (res)

# saves file in the subdirectory
def write_file_subdir(subdir_name, file_name, content, content_type="text"):
  f = open("{}{}/{}".format(
    sub_dir_path, subdir_name, file_name
  ), 'w')
  
  if (content_type == "json"):
    json.dump(content, f)
  else:
    f.write(content)

  f.close()

#removes the subdirectory
def rm_sub_subdir(subdir_name):
  try:
    subprocess.run(
      "rm -rf \"{}{}/\"".format(sub_dir_path, subdir_name), 
      shell=True
    )
    return True
  except:
    return False

# read file from the subdirectory
def read_file_subdir(subdir_name, file_name, content_type="text"):
  
  res = None

  f = open("{}{}/{}".format(
    sub_dir_path, subdir_name, file_name
  ), 'r')
  
  if (content_type == "json"):
    res = json.load(f)
  else:
    res = f.read()

  f.close()

  return (res)

# check if a filetype is valid
ALLOWED_EXTENSIONS = {'c', "cpp", "py", "rb"}

def validate_file(file):
  if (file == None or file.filename == ''):
    raise ValueError("File is empty")
  if '.' not in file.filename or (file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS):
    raise ValueError("Not a valid file extension")
