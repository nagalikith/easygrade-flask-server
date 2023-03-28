import import_helper as ih

class LangC(ih.libs["Lang"].Lang):
  
  def __init__(self, file_name, dir_path):
    super().__init__('c', "COMPILED", file_name,
      dir_path)
  
  #helper method to get the file_name of the compiled code
  def get_comp_file_name(self):
    return "{}.out".format(
      self.file_name.split('.')[0]
    )

  #gets the command to compile file
  def build_statement(self):
    return "gcc \"{}\" -o \"{}\"".format(
      self.get_full_path(self.file_name),
      self.get_full_path(self.get_comp_file_name())
    )

  #gets the command to execute machine code
  def exec_statement(self):
    return "\"{}\"".format(
      self.get_full_path(self.get_comp_file_name())
    )
