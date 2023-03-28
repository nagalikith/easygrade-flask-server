# base class, stores information of code-file
class Lang:
  
  LANG_TYPE = {"COMPILED", "INTERPRETED"}

  def __init__(self, lang, lang_type, file_name, dir_path):
    """
      lang: stores language name of the file
      lang_type: stores the LANG_TYPE of the language
      file_name: stores the filename
      dir_path: path of the directory where the file is stored
    """
    self.lang = lang
    self.lang_type = lang_type
    self.file_name = file_name
    self.dir_path = dir_path

  def __repr__(self):
    return "Lang(\"{}\", \"{}\", \"{}\")".format(
      self.lang, self.lang_type, 
      self.file_name, self.dir_path
    )

  # helper function to get the full path of a file stored in dir_path
  def get_full_path(self, file_name):
    return ("{}{}".format(
      self.dir_path,
      file_name
    ))
