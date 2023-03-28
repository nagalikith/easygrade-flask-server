import import_helper as ih

class LangCPP(ih.libs["Lang"].Lang):
  
  def __init__(self, file_name, dir_path):
    super().__init__("cpp", "COMPILED", file_name,
      dir_path)

  def get_comp_file_name(self):
    return "{}.out".format(
      self.file_name.split('.')[0]
    )

  def build_statement(self):
    return "g++ \"{}\" -o \"{}\"".format(
      self.get_full_path(self.file_name),
      self.get_full_path(self.get_comp_file_name())
    )

  def exec_statement(self):
    return "\"{}\"".format(
      self.get_full_path(self.get_comp_file_name())
    )
