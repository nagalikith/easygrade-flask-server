## Cleferr AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import import_helper as ih
import sqlalchemy as sa
import time

tables_info = ih.libs["db_schema"].tables_info


def get_user_id(username):
    return get_user_info(username=username, cols=["user_id"])[0]


def admin_user_view(user_id):
    col_names = ["Username", "Email", "Join Date--epoch", "Last Access--epoch"]
    col_mapping = {
        "user_info": ["username", "email", "reg_epoch"],
        "user_auth": ["last_access"]
    }
    
    columns = [
        tables_info["user_info"]["col"][col] for col in col_mapping["user_info"]
    ] + [
        tables_info["user_auth"]["col"][col] for col in col_mapping["user_auth"]
    ]
    
    stmt = sa.select(*columns).select_from(
        tables_info["user_auth"]["table"].join(tables_info["user_info"]["table"])
    ).where(
        tables_info["user_auth"]["col"]["user_id"] == user_id
    )
    
    row = ih.libs["db_connect"].run_stmt(stmt).first()
    return dict(zip(col_names, row)) if row else {}


def get_all_users():
    col_names = ["user_id", "username", "email"]
    columns = [tables_info["user_info"]["col"][col] for col in col_names]
    
    stmt = sa.select(*columns).order_by(columns[-1])
    result = ih.libs["db_connect"].run_stmt(stmt)
    
    return {
        "col_names": ["userid", "username", "email"],
        "values": [[getattr(row, col) for col in col_names] for row in result]
    }


def get_user_info(username=None, user_id=None, cols=None):
    if cols is None:
        cols = [tables_info["user_info"]["table"]]
    else:
        cols = [tables_info["user_info"]["col"][col] for col in cols]

    stmt = sa.select(*cols)
    if username:
        stmt = stmt.where(tables_info["user_info"]["col"]["username"] == username)
    elif user_id:
        stmt = stmt.where(tables_info["user_info"]["col"]["user_id"] == user_id)
    else:
        return None

    return ih.libs["db_connect"].run_stmt(stmt).first()


def get_hashed_password(username=None, user_id=None):
    result = get_user_info(username=username, user_id=user_id, cols=["hashed_password"])
    if not result:
        raise ValueError("User does not exist")
    return result[0]


def register_user(username, password, email=None, user_id=None):
    if get_user_info(username=username, cols=["user_id"]):
        raise ValueError("Username is already taken")

    user_id = user_id or generate_unique_user_id()

    hashed_password = ih.libs["user_auth"].get_hash_pass(password)

    # Insert user info
    stmt_user_info = sa.insert(tables_info["user_info"]["table"]).values(
        user_id=user_id, username=username, hashed_password=hashed_password,
        email=email, reg_epoch=time.time()
    )
    ih.libs["db_connect"].run_stmt(stmt_user_info)


def generate_unique_user_id():
    user_id = ih.libs["hex_rel"].gen_hex()
    while get_user_info(user_id=user_id, cols=["user_id"]):
        user_id = ih.libs["hex_rel"].gen_hex()
    return user_id


def update_email(user_id, email):
    stmt = sa.update(tables_info["user_info"]["table"]).where(
        tables_info["user_info"]["col"]["user_id"] == user_id
    ).values(email=email)
    ih.libs["db_connect"].run_stmt(stmt)


def update_password(user_id, password):
    hashed_password = ih.libs["user_auth"].get_hash_pass(password)
    stmt = sa.update(tables_info["user_info"]["table"]).where(
        tables_info["user_info"]["col"]["user_id"] == user_id
    ).values(hashed_password=hashed_password)
    ih.libs["db_connect"].run_stmt(stmt)


def create_assignment(author_id, title, body, start_epoch, end_epoch, url):
    if not all([author_id, title, body, start_epoch, end_epoch, url]):
        raise ValueError("All parameters must be provided.")

    stmt = sa.insert(tables_info["assn"]["table"]).values(
        author_id=author_id, assn_title=title, assn_body=body,
        last_upd=time.time(), start_epoch=start_epoch, end_epoch=end_epoch, assn_url=url
    )

    try:
        return ih.libs["db_connect"].run_stmt(stmt).rowcount
    except Exception as e:
        print(f"Error inserting assignment: {e}")
        return None
