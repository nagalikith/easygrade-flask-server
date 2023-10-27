## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih

def create_tables():
  metadata = ih.libs["db_schema"].metadata
  engine = ih.libs["db_connect"].engine
  metadata.create_all(engine)

def make_admin_user():
  username = "admin"
  password = input("Enter \"admin\" password ")
  email = input("Enter email, press enter to skip ")
  userid = '0' * ih.get_env_val("HEX_ID_LENGTH")

  if (email == ''):
    email = None

  ih.libs["db_userop"].reg_user(username, password, email, userid)

## EOF
