# app/utils/env_manager.py

import json
import os
import sys
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class EnvManager:
    def __init__(self):
        self.root_path = self._get_root_path()
        self.env_data = self._load_env_data()

    @staticmethod
    def _get_root_path() -> str:
        """Determine the root path of the project."""
        return os.path.abspath("/home/snaga/easygrade-flask-server")

    def _load_env_data(self) -> Dict:
        """Load environment variables from JSON file."""
        env_path = os.path.join(self.root_path, "py_lib/helper_libs/env.json")
        try:
            with open(env_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Environment file not found at {env_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse the environment file at {env_path}")
            sys.exit(1)

    def get_env_val(self, var_name: str, return_type: Optional[str] = None) -> Any:
        """Get an environment variable value."""
        value = self.env_data.get(var_name)

        if var_name.startswith("PATH"):
            value = os.path.join(self.root_path, value) if value else None

        if return_type == "json" and isinstance(value, dict):
            return json.dumps(value)
        
        return value

# Create a singleton instance
env_manager = EnvManager()
get_env_val = env_manager.get_env_val