import json
from pathlib import Path

from app.core.settings import settings

BASE_DIR = Path(__file__).resolve().parents[1]


def get_env_val(var_name, return_type=None):
    value = getattr(settings, var_name, None)
    if isinstance(value, str) and var_name.startswith("PATH"):
        path = Path(value)
        if not path.is_absolute():
            value = str(BASE_DIR / path)

    if return_type == "json" and isinstance(value, dict):
        return json.dumps(value)
    return value


libs = {}

from app.py_lib import hex_rel  # noqa: E402
libs["hex_rel"] = hex_rel

from app.py_lib import form_helper  # noqa: E402
libs["form_helper"] = form_helper

from app.core import security as user_auth  # noqa: E402
libs["user_auth"] = user_auth

from app.py_lib.aws_rel import s3_rel  # noqa: E402
libs["s3_rel"] = s3_rel

from app.py_lib.db_libs import db_connect  # noqa: E402
libs["db_connect"] = db_connect

from app.py_lib.db_libs import db_schema  # noqa: E402
libs["db_schema"] = db_schema

from app.py_lib.db_libs import db_userop  # noqa: E402
libs["db_userop"] = db_userop

from app.py_lib.db_libs import db_secop  # noqa: E402
libs["db_secop"] = db_secop

from app.py_lib.fileop_libs import fileop_helper  # noqa: E402
libs["fileop_helper"] = fileop_helper

from app.py_lib.fileop_libs import subm_fileop  # noqa: E402
libs["subm_fileop"] = subm_fileop

from app.py_lib.fileop_libs import assn_fileop  # noqa: E402
libs["assn_fileop"] = assn_fileop

from app.py_lib.run_lang import Lang  # noqa: E402
libs["Lang"] = Lang

from app.py_lib.run_lang import LangCPP  # noqa: E402
libs["LangCPP"] = LangCPP

from app.py_lib.run_lang import LangC  # noqa: E402
libs["LangC"] = LangC

from app.py_lib.run_lang import LangPython  # noqa: E402
libs["LangPython"] = LangPython

from app.py_lib.run_lang import LangRuby  # noqa: E402
libs["LangRuby"] = LangRuby

from app.py_lib.run_lang import run_code  # noqa: E402
libs["run_code"] = run_code

from app.py_lib import gen_hex  # noqa: E402
libs["gen_hex"] = gen_hex
