## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import sqlalchemy as sa
import time

tables_info = ih.libs["db_schema"].tables_info

def admin_userview(userid):
    if not userid:
        return {"error": "Invalid userid provided."}

    col_names_userinfo = ["username", "email", "reg_epoch"]
    col_names_userauth = ["last_access"]

    col_names = ["Username", "Email", "Join Date--epoch", "Last Access--epoch"]
    cols = []

    for cname in col_names_userinfo:
        cols.append(tables_info["user_info"]["col"][cname])

    for cname in col_names_userauth:
        cols.append(tables_info["user_auth"]["col"][cname])

    stmt = sa.select(*cols).select_from(
        tables_info["user_auth"]["table"].join(
            tables_info["user_info"]["table"]
        )
    ).where(tables_info["user_auth"]["col"]["user_id"] == userid)

    rpf = ih.libs["db_connect"].run_stmt(stmt).first()

    if not rpf:
        return {"error": "User not found."}

    res = {}
    for i in range(len(col_names)):
        res[col_names[i]] = rpf[i]

    return res

def get_all_users():
    col_names = ["user_id", "username", "email"]
    cols = [tables_info["user_info"]["col"][cname] for cname in col_names]

    stmt = sa.select(*cols).order_by(cols[-1])

    res = []
    for row in ih.libs["db_connect"].run_stmt(stmt):
        res.append(
            [getattr(row, cname) for cname in col_names]
        )

    if not res:
        return {"error": "No users found."}

    col_names[0] = "userid"

    return {"col_names": col_names, "values": res}

def get_user_info(username=None, userid=None, cols=None):
    if not username and not userid:
        return {"error": "Username or userid must be provided."}

    if cols is None:
        cols = [tables_info["user_info"]["table"]]
    else:
        cols = [tables_info["user_info"]["col"][col] for col in cols]

    stmt = sa.select(*cols)

    if username:
        stmt = stmt.where(tables_info["user_info"]["col"]["username"] == username)
    elif userid:
        stmt = stmt.where(tables_info["user_info"]["col"]["user_id"] == userid)

    rp = ih.libs["db_connect"].run_stmt(stmt).first()

    if not rp:
        return {"error": "User not found."}

    return rp

def get_hash_passwd(username=None, userid=None):
    res = get_user_info(username=username, userid=userid, cols=["hashed_password"])
    if isinstance(res, dict) and "error" in res:
        return {"error": "User does not exist."}
    
    return res[0]

def reg_user(username, password, email=None, userid=None):
    if get_user_info(username=username, cols=["user_id"]) is not None:
        return {"error": "Username taken."}

    if userid is None:
        userid = ih.libs["hex_rel"].gen_hex()
        while get_user_info(userid=userid, cols=["user_id"]) is not None:
            userid = ih.libs["hex_rel"].gen_hex()
    else:
        if get_user_info(userid=userid, cols=["user_id"]) is not None:
            return {"error": "Userid taken."}

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

    return {"message": "User registered successfully.", "userid": userid}

def get_eph_cred_info(userid, cols=None):
    if not userid:
        return {"error": "Invalid userid."}

    if cols is None:
        cols = [tables_info["user_auth"]["table"]]
    else:
        cols = [tables_info["user_auth"]["col"][col] for col in cols]

    stmt = sa.select(*cols).where(tables_info["user_auth"]["col"]["user_id"] == userid)

    rp = ih.libs["db_connect"].run_stmt(stmt).first()

    if not rp:
        return {"error": "No credentials found for user."}

    return rp

def verify_eph_cred(userid, eph_pass):
    if not userid or not eph_pass:
        return {"status": False, "error": "Invalid credentials provided."}

    res = {"status": False}
    row = get_eph_cred_info(userid)

    if isinstance(row, dict) and "error" in row:
        return row

    acc_eph_pass = getattr(row, "eph_pass")

    if acc_eph_pass != eph_pass:
        return res

    upd_info = upd_user_auth(row)
    res["status"] = True
    res["upd_info"] = upd_info

    return res

def create_cred(username):
    user_info = get_user_info(username=username, cols=["user_id"])
    
    if isinstance(user_info, dict) and "error" in user_info:
        return user_info

    userid = user_info[0]
    eph_pass = ih.libs["hex_rel"].gen_hex()

    stmt = sa.update(tables_info["user_auth"]["table"]).where(
        tables_info["user_auth"]["col"]["user_id"] == userid
    ).values(eph_pass=eph_pass, last_access=time.time())

    ih.libs["db_connect"].run_stmt(stmt)

    upd_user_auth(get_eph_cred_info(userid))

    return {"userid": userid, "eph_pass": eph_pass}

def upd_email(userid, email):
    if not userid:
        return {"error": "Invalid userid."}
    
    stmt = sa.update(tables_info["user_info"]["table"]).where(
        tables_info["user_info"]["col"]["user_id"] == userid
    ).values(email=email)

    ih.libs["db_connect"].run_stmt(stmt)

def upd_passwd(userid, password):
    if not userid or not password:
        return {"error": "Invalid userid or password."}
    
    hashed_passwd = ih.libs["user_auth"].get_hash_pass(password)

    stmt = sa.update(tables_info["user_info"]["table"]).where(
        tables_info["user_info"]["col"]["user_id"] == userid
    ).values(hashed_password=hashed_passwd)

    ih.libs["db_connect"].run_stmt(stmt)

## EOF
