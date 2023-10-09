## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import time
import sqlalchemy as sa

tables_info = ih.libs["db_schema"].tables_info


def get_sectionview_stmt():
  col_names = ["section_id", "section_code", "section_name"]

  cols = [tables_info["section"]["col"][cname] for cname in col_names]

  stmt  = sa.select(*cols)

  return (col_names, stmt)

def ret_map_list(col_names, stmt):
  res = {cname: [] for cname in col_names}
  
  rp = ih.libs["db_connect"].run_stmt(stmt)

  for row in rp:
    for cname in col_names:
      res[cname].append(getattr(row, cname))

  return res

def admin_sectionview():
  col_names, stmt  = get_sectionview_stmt()
  return ret_map_list(col_names, stmt)

def get_sectionview(userid):
 
  stmt_filter_secid = sa.select(tables_info["sec_acc"]["col"]["section_id"]).where(tables_info["sec_acc"]["col"]["user_id"] == userid)

  sel_sections = [getattr(row, "section_id") for row in ih.libs["db_connect"].run_stmt(stmt_filter_secid)]

  col_names, stmt_select  = get_sectionview_stmt()

  stmt = stmt_select.where(tables_info["section"]["col"]["section_id"].in_(sel_sections))

  return ret_map_list(col_names, stmt)

def get_section_info(secid=None, section_code=None, cols=None):
  if (cols == None):
    cols = [tables_info["section"]["table"]]
  else:
    cols = [tables_info["section"]["col"][cname] for cname in cols]

  stmt = sa.select(*cols)

  if (secid == None):
    stmt = stmt.where(tables_info["section"]["col"]["section_id"] == secid)

  elif(section_code != None):
    stmt = stmt.where(tables_info["section"]["col"]["section_code"] == section_code)

  else:
    return None
  
  res = None
  rp = ih.libs["db_connect"].run_stmt(stmt)

  for row in rp:
    res = row

  return res

def create_section(section_code, section_name = None):
  
  sec_id = ih.libs["hex_rel"].gen_hex()
  
  while(get_section_info(secid=sec_id, cols=["section_id"]) != None):
    sec_id = ih.libs["hex_rel"].gen_hex()

  stmt = sa.insert(tables_info["section"]["table"]).values(
    section_id=sec_id,
    section_code=section_code,
    section_name=section_name
  )

  ih.libs["db_connect"].run_stmt(stmt)

def change_section_name(secid, section_name):
  stmt = sa.update(tables_info["section"]["table"]).where(tables_info["section"]["col"]["section_id"] == secid).values(section_name=section_name)

  ih.libs["db_connect"].run_stmt(stmt)

def add_usr_section(secid, userid, role):
  stmt = sa.insert(tables_info["sec_acc"]["table"]).values(
    section_id=secid,
    user_id=userid,
    role=role,
    add_epoch=time.time()
  )

  ih.libs["db_connect"].run_stmt(stmt)

def sec_users_list(secid):
  cols = [
    tables_info["user_info"]["col"]["username"],
    tables_info["sec_acc"]["col"]["role"]
  ]

  stmt = sa.select(*cols).select_from(
    tables_info["sec_acc"]["table"].join(
      tables_info["user_info"]["table"]
    )
  ).where(
    tables_info["sec_acc"]["col"]["section_id"] == secid
  )

  rp = ih.libs["db_connect"].run_stmt(stmt)
  res = {"student": [], "teacher": []}
  
  for row in rp:
    role = getattr(row, "role")
    username = getattr(row, "username")
    if (role) == 'T':
      res["teacher"].append(username) 
    elif (role) == 'S':
      res["student"].append(username)

  return res

def user_has_secacc(userid, secid):
  res = {"status": None, "role": None}

  if (ih.libs["user_auth"].is_admin(userid)):
    res["status"] = True
    res["role"] = "admin"

  else:
    stmt = sa.select(tables.info["sec_acc"]["col"]["role"]).where(
      sa.and_(
        tables.info["sec_acc"]["col"]["section_id"] == secid,
        tables.info["sec_acc"]["col"]["user_id"] == userid
      )
    )

    rp = ih.libs["db_connect"].run_stmt(stmt)

    stmt_res = None
    for row in rp:
      stmt_res = getattr(row, "role")

    if (stmt_res == None):
      res["status"] = False

    else:
      res["status"] = True
      res["role"] = "teacher" if stmt_res == 'T' else "student"
## EOF
