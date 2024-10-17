## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import time
import sqlalchemy as sa

tables_info = ih.libs["db_schema"].tables_info


import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sectionview_stmt() -> tuple[list[str], any]:
    """
    Constructs a SQL SELECT statement to retrieve section details.
    
    Returns:
        A tuple containing:
            - A list of column names (str)
            - A SQLAlchemy select statement object
    """
    logger.info("Creating section view statement.")

    # Define column names to be retrieved
    col_names = ["section_id", "section_code", "section_name"]

    # Retrieve corresponding column references from tables_info
    cols = [tables_info["section"]["col"][cname] for cname in col_names]

    # Construct the SQL SELECT statement
    stmt = sa.select(*cols)

    logger.debug(f"Column names: {col_names}")
    logger.debug(f"Generated statement: {stmt}")

    return (col_names, stmt)


def ret_map_list(col_names: list[str], stmt: any) -> dict[str, list]:
    """
    Executes a SQL statement and maps the results to a dictionary format.

    Args:
        col_names: A list of column names to retrieve from the result set.
        stmt: A SQLAlchemy select statement object.

    Returns:
        A dictionary mapping each column name to a list of values.
    """
    logger.info("Executing statement and mapping results.")

    # Initialize the result dictionary
    res = {cname: [] for cname in col_names}

    # Execute the SQL statement and retrieve results
    try:
        rp = ih.libs["db_connect"].run_stmt(stmt)
    except Exception as e:
        logger.error(f"Error executing statement: {e}")
        return res

    # Map the results to the corresponding column names
    for row in rp:
        for cname in col_names:
            res[cname].append(getattr(row, cname))
    
    logger.debug(f"Mapped results: {res}")
    return res


def admin_sectionview() -> dict[str, list]:
    """
    Retrieves section view data for admin purposes.

    Returns:
        A dictionary mapping section details to their corresponding values.
    """
    logger.info("Retrieving section view data for admin.")

    # Get the column names and the statement for the section view
    col_names, stmt = get_sectionview_stmt()

    # Get the mapped results
    results = ret_map_list(col_names, stmt)

    logger.info("Successfully retrieved section view data.")
    return results

def get_sectionview(userid):
    # Ensure userid is a string
    if not isinstance(userid, str):
        raise ValueError("userid must be a string")

    # Check the structure of tables_info and make sure it contains the expected keys
    try:
        section_col = tables_info["sec_acc"]["col"]
        section_id_col = section_col["section_id"]
        user_id_col = section_col["user_id"]
    except KeyError as e:
        print(f"KeyError: {e} - Check the structure of tables_info")
        return []

    # Prepare the SQL statement
    stmt_filter_secid = sa.select(section_id_col).where(user_id_col == userid)

    # Execute the statement and fetch section IDs
    try:
        result = ih.libs["db_connect"].run_stmt(stmt_filter_secid)
        sel_sections = [getattr(row, "section_id") for row in result]
    except Exception as e:
        print(f"Error executing statement: {e}")
        return []

    # Debugging output for fetched section IDs
    print("Fetched section IDs:", sel_sections)

    col_names, stmt_select = get_sectionview_stmt()

    # Ensure sel_sections is not empty
    if not sel_sections:
        print("No sections found for the user.")
        return []

    # Prepare the final statement to retrieve section views
    try:
        stmt = stmt_select.where(tables_info["section"]["col"]["section_id"].in_(sel_sections))
    except Exception as e:
        print(f"Error building final statement: {e}")
        return []

    # Return the mapped list
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
