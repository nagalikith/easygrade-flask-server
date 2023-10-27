## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import time
import import_helper as ih
import threading
import sqlalchemy as sa
import random

n = 1000
num_execs = [0]

def printResult():
  print("Result : ( %d / %d )" % (num_execs[0], n))

def getConnLength():
  length = len(ih.libs["db_connect"].conn_info["connections"])
  print(length)

def exec_statement(ind, n_i):
  rp = ih.libs["db_connect"].run_stmt(stmts[ind])
  res_ = rp.fetchall()
  if (res_ == res[ind]):
    fin_res[n_i] = 1
  if (random.randint(1, n) % (n // 10)):
    getConnLength()

  num_execs[0] += 1

  if (num_execs[0] == n):
    printResult()

stmts = [
  sa.text("select * from cookies"),
  sa.text("select * from orders"),
  sa.text("select * from line_items"),
  sa.text("select * from users")
]

fin_res = [0 for i in range(n)]
res = []

for stmt in stmts:
  rp = ih.libs["db_connect"].run_stmt(stmt)
  res.append(rp.fetchall())

for i in range(n):
  rt = threading.Thread(target=exec_statement, args=(random.randint(0, len(res) - 1), i))
  rt.start()
  time.sleep(0.03)

time.sleep(10)

getConnLength()
## EOF
