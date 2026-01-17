import passlib.hash as ph

from app import import_helper as ih

sha256 = ph.pbkdf2_sha256


def get_hash_pass(password: str) -> str:
    return sha256.hash(password)


def authenticate_using_password(user_id: str, password: str) -> bool:
    try:
        hashed_passwd = ih.libs["db_userop"].get_hashed_password(user_id=user_id)
        return sha256.verify(password, hashed_passwd)
    except Exception:
        return False


def is_admin(userid: str) -> bool:
    return userid == '0' * ih.get_env_val("HEX_ID_LENGTH")
