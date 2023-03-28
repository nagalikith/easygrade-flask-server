import import_helper as ih

class LangRuby(ih.libs["Lang"].Lang):
  
  def __init__(self, file_name, dir_path):
    super().__init__("ruby", "INTERPRETED", file_name,
      dir_path)

  def exec_statement(self):
    return "ruby \"{}\"".format(
      self.get_full_path(self.file_name)
    )
