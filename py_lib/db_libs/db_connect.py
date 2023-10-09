## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import sqlalchemy
import import_helper as ih
import time
import random


db_info = ih.get_env_val("DB_INFO")
conn_str = "{}://{}:{}@{}:{}/{}".format(
  db_info["dbms_name"],
  db_info["username"], db_info["password"],
  db_info["host"], db_info["port"], db_info["name"]
)
max_time_conn = db_info["max_time_connection"]
print("CONN STR:")
engine = sqlalchemy.create_engine(conn_str)

class DBConnection:
  
  def __init__(self):  
    self.start_time = time.time()
    self.connection = engine.connect()
    self.isOn = False

  def execute(self, stmt, listOfDict=None):
    self.isOn = True

    if (listOfDict == None):
      rp = self.connection.execute(stmt)
    else:
      rp = self.connection.execute(stmt, listOfDict)
      
    self.connection.commit()
    self.isOn = False
    return rp

  def isBusy(self):
    return self.isOn

  def age(self):
    return (time.time() - self.start_time)

  def terminate(self):
    self.connection.close()

conn_info = {"connections": []}

def del_old_connections():
  young_connections = []
  for conn in conn_info["connections"]:
    if (conn.age() > max_time_conn):
      conn.terminate()
    else:
      young_connections.append(conn)
  conn_info["connections"] = young_connections

def run_stmt(stmt):
  del_old_connections()
  
  rp = None

  if (len(conn_info["connections"]) == 0):
    conn = DBConnection()
    rp = conn.execute(stmt)
    conn_info["connections"].append(conn)

  else:
    ind = random.randint(0, len(conn_info["connections"]) - 1) 
    conn = conn_info["connections"].pop(ind)
    rp = conn.execute(stmt)
    conn_info["connections"].append(conn)

  return rp

## EOF
