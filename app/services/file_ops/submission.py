import import_helper as ih
import subprocess


#stores the submission directory-path
sub_dir_path = ih.get_env_val("PATH_UPL_DIR_PAR")


def copy_assn_files_subdir(subdir_id, assn_id):
  file_name = "{}.sh".format(ih.libs["hex_rel"].gen_hex())
  assn_path = "{}{}/".format(
    ih.libs["assn_fileop"].assn_dir_path,
    assn_id
  )  

  subm_path = "{}{}/".format(
    sub_dir_path,
    subdir_id
  )  

  num_cases = ih.libs["assn_fileop"].get_assn_prop(assn_id, "__len_testcases")

  content = "cd \"{}\"\n".format(subm_path);

  for i in range(num_cases):
    content += "cp \"{}{}\" .\n".format(assn_path, "__input_file_{}".format(i))
    content += "cp \"{}{}\" .\n".format(assn_path, "__expected_output_file_{}".format(i))

  content += "rm -rf {}\n".format(file_name)

  write_file_subdir(subdir_id, file_name, content);
  subprocess.run(["sh \"{}{}\"".format(subm_path, file_name)], shell=True) 
  return num_cases

def diff_files(subbir_name, f1, f2):
  c1 = read_file_subdir(subbir_name, f1)
  c2 = read_file_subdir(subbir_name, f2)

  c1 = c1.rstrip()
  c2 = c2.rstrip()

  if (c1 == c2):
    return 1
  else:
    return 0

#makes a subdircetory in the submission folder, and returns the subdirectory information
def make_sub_subdir():
  subdir_name = ih.libs["hex_rel"].gen_hex()
  run_cond = 1

  while (run_cond):
    try:
      ih.libs["fileop_helper"].make_dir("/{}{}/".format(sub_dir_path, subdir_name))
      run_cond = 0
    except:
      subdir_name = ih.libs["hex_rel"].gen_hex()
    
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
  ih.libs["fileop_helper"].write_file(
    "{}{}/{}".format(sub_dir_path, subdir_name, file_name),
    content,
    content_type
  )

#removes the subdirectory
def rm_sub_subdir(subdir_name):
  try:
    ih.libs["fileop_helper"].rm_dir("{}{}/".format(sub_dir_path, subdir_name))
    return True
  except:
    return False

# read file from the subdirectory
def read_file_subdir(subdir_name, file_name, content_type="text"):
  
  res = ih.libs["fileop_helper"].read_file(
    "{}{}/{}".format(sub_dir_path, subdir_name, file_name),
    content_type
  )

  return (res)
  
# check if a filetype is valid
ALLOWED_EXTENSIONS = {'c', "cpp", "py", "rb"}

def validate_file(file):
  if (file == None or file.filename == ''):
    raise ValueError("File is empty")
  if '.' not in file.filename or (file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS):
    raise ValueError("Not a valid file extension")
