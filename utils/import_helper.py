
import importlib
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class ImportManager:
    def __init__(self):
        self.libs: Dict = {}
        self._import_libraries()

    def import_lib(self, module_name: str, alias: str) -> None:
        """Import a library and store it in the libs dictionary."""
        try:
            module = importlib.import_module(module_name)
            self.libs[alias] = module
            logger.debug(f"Successfully imported {module_name} as {alias}")
        except ImportError as e:
            logger.error(f"Error importing {module_name}: {str(e)}")
            raise

    def _import_libraries(self) -> None:
        """Import all required libraries."""
        lib_imports: List[Tuple[str, str]] = [
            ("py_lib.hex_rel", "hex_rel"),
            ("py_lib.form_helper", "form_helper"),
            ("py_lib.user_auth", "user_auth"),
            ("py_lib.aws_rel.s3_rel", "s3_rel"),
            ("py_lib.db_libs.db_connect", "db_connect"),
            ("py_lib.db_libs.db_schema", "db_schema"),
            ("py_lib.db_libs.db_userop", "db_userop"),
            ("py_lib.db_libs.db_secop", "db_secop"),
            ("py_lib.fileop_libs.fileop_helper", "fileop_helper"),
            ("py_lib.fileop_libs.subm_fileop", "subm_fileop"),
            ("py_lib.fileop_libs.assn_fileop", "assn_fileop"),
            ("py_lib.run_lang.Lang", "Lang"),
            ("py_lib.run_lang.LangCPP", "LangCPP"),
            ("py_lib.run_lang.LangC", "LangC"),
            ("py_lib.run_lang.LangPython", "LangPython"),
            ("py_lib.run_lang.LangRuby", "LangRuby"),
            ("py_lib.run_lang.run_code", "run_code"),
        ]

        for module_name, alias in lib_imports:
            self.import_lib(module_name, alias)

# Create a singleton instance
import_manager = ImportManager()
libs = import_manager.libs
handle_login = libs["user_auth"].handle_login