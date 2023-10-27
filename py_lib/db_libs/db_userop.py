## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import sqlalchemy as sa
import time

tables_info = ih.libs["db_schema"].tables_info


def admin_userview(userid):
  col_names_userinfo = ["username", "email", "reg_epoch"]
  col_names_userauth = ["last_access"]

  col_names = ["Username", "Email", "Join Date--epoch", "Last Acces--epoch"]
  
  cols = []

  for cname in col_names_userinfo:
    cols.append(
      tables_info["user_info"]["col"][cname]
    )

  for cname in col_names_userauth:
    cols.append(
      tables_info["user_auth"]["col"][cname]
    )

  stmt = sa.select(*cols).select_from(
    tables_info["user_auth"]["table"].join(
      tables_info["user_info"]["table"]
    )
  ).where(tables_info["user_auth"]["col"]["user_id"] == userid)
  
  rpf = ih.libs["db_connect"].run_stmt(stmt).first()

  res = {}

  for i in range(len(col_names)):
    res[col_names[i]] = rpf[i]

  return res
    

def get_all_users():
  col_names= ["user_id", "username", "email"]

  cols = [tables_info["user_info"]["col"][cname] for cname in col_names]

  stmt = sa.select(*cols).order_by(cols[-1])
  
  res = []
  for row in ih.libs["db_connect"].run_stmt(stmt):
    res.append(
      [getattr(row, cname) for cname in col_names]
    )

  col_names[0] = "userid"

  return {"col_names": col_names, "values": res}

def get_user_info(username=None, userid=None, cols=None):
  
  if (cols == None):
    cols = [tables_info["user_info"]["table"]]
  else:
    cols = [tables_info["user_info"]["col"][col] for col in cols]
  
  stmt = sa.select(*cols)

  if (username != None):
    stmt = stmt.where(tables_info["user_info"]["col"]["username"] == username)
  elif (userid != None):
    stmt = stmt.where(tables_info["user_info"]["col"]["user_id"] == userid)
  else:
    return None

  res = None

  rp = ih.libs["db_connect"].run_stmt(stmt)
  
  for elem in rp:
    res = elem
  
  return res

def get_hash_passwd(username=None, userid=None):
    res = get_user_info(username=username, userid=userid, cols=["hashed_password"])
    if (res == None):
      raise ValueError("user doesnt exist")
    else:
      return res[0]

def reg_user(username, password, email=None,userid=None):

  if (get_user_info(username=username, cols=["user_id"]) != None):
    raise ValueError("Username taken")

  if (userid == None):
    userid = ih.libs["hex_rel"].gen_hex()
    while (get_user_info(userid=userid, cols=["user_id"]) != None):
      userid = ih.libs["hex_rel"].gen_hex()

  else:
    if (get_user_info(userid=userid, cols=["user_id"]) != None):
      raise ValueError("Userid taken")

  hash_pass = ih.libs["user_auth"].get_hash_pass(password)

  stmt_reg_user = sa.insert(
    tables_info["user_info"]["table"]
  ).values(
    user_id=userid,
    username=username,
    hashed_password=hash_pass,
    email=email,
    reg_epoch=time.time()
  )

  ih.libs["db_connect"].run_stmt(stmt_reg_user)

  stmt_user_auth = sa.insert(
    tables_info["user_auth"]["table"]
  ).values(
    user_id=userid,
    eph_pass=ih.libs["hex_rel"].gen_hex(),
    last_access=time.time(),
    period_start=time.time(),
    num_hits=1
  )

  ih.libs["db_connect"].run_stmt(stmt_user_auth)

def get_eph_cred_info(userid, cols=None):

  if (cols == None):
    cols = [tables_info["user_auth"]["table"]]
  else:
    cols = [tables_info["user_auth"]["col"][col] for col in cols]

  stmt = sa.select(
    *cols
  ).where(
    tables_info["user_auth"]["col"]["user_id"] == userid
  )

  rp = ih.libs["db_connect"].run_stmt(stmt)
  return (rp.first())

def upd_user_auth(row):
  
  res = {"update": False, "cred": None, "action": None}
  
  userid = getattr(row, "user_id")
  period_start = getattr(row, "period_start")
  num_hits = getattr(row, "num_hits")
  last_access = getattr(row, "last_access")

  if ((time.time() - last_access) > 3600 * 2):
    res["action"] = "log off"

  kwargs = {"last_access": time.time()}
  if ((time.time() - period_start) > 3600 * 24):
    num_hits = 1
    kwargs["period_start"] = time.time()
    
    new_eph_pass = ih.libs["hex_rel"].gen_hex()

    kwargs["eph_pass"] = new_eph_pass
    res["update"] = True
    res["cred"] = {"userid": userid, "eph_pass": new_eph_pass}

  else:
    num_hits += 1

  kwargs["num_hits"] = num_hits
  
  stmt  = sa.update(
      tables_info["user_auth"]["table"]
    ).where(
      tables_info["user_auth"]["col"]["user_id"] == userid
    ).values(
      **kwargs
    )

  ih.libs["db_connect"].run_stmt(stmt)

  return res

def verify_eph_cred(userid, eph_pass):

  res = {"status": False}

  row = get_eph_cred_info(userid)
  acc_eph_pass = getattr(row, "eph_pass") 

  if (acc_eph_pass != eph_pass):
    return res

  upd_info = upd_user_auth(row)
  res["status"] = True
  res["upd_info"] = upd_info

  return res

def create_cred(username):
  userid = get_user_info(username=username, cols=["user_id"])[0]
  eph_pass = ih.libs["hex_rel"].gen_hex()
  stmt = sa.update(tables_info["user_auth"]["table"]).where(tables_info["user_auth"]["col"]["user_id"] == userid).values(eph_pass=eph_pass, last_access=time.time())

  ih.libs["db_connect"].run_stmt(stmt)

  upd_user_auth(
    get_eph_cred_info(userid)
  )
  
  return(
    {"userid": userid, "eph_pass": eph_pass}
  )

def upd_email(userid, email):
  stmt = sa.update(tables_info["user_info"]["table"]).where(tables_info["user_info"]["col"]["user_id"] == userid).values(email=email)

  ih.libs["db_connect"].run_stmt(stmt)

def upd_passwd(userid, password):
  
  hashed_passwd = ih.libs["user_auth"].get_hash_pass(password)

  stmt = sa.update(tables_info["user_info"]["table"]).where(tables_info["user_info"]["col"]["user_id"] == userid).values(hashed_password=hashed_passwd)

  ih.libs["db_connect"].run_stmt(stmt)

## EOF
