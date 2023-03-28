import import_helper as ih

class LangPython(ih.libs["Lang"].Lang):
  
  def __init__(self, file_name, dir_path):
    super().__init__("python", "INTERPRETED", file_name,
      dir_path)

  #returns the command to execute the file
  def exec_statement(self):
    return "python \"{}\"".format(
      self.get_full_path(self.file_name)
    )
