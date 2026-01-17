import json
from typing import Any, Dict, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SUPP_LANG: List[str] = ["c", "cpp", "python", "ruby"]
    CHECK_DELAY: int = 1000
    LANG_CLASS: List[str] = ["LangC", "LangCPP", "LangPython", "LangRuby"]
    PATH_UPL_DIR_PAR: str = "submissions/"
    PATH_ASSN_DIR_PAR: str = "assignments/"
    links: Dict[str, str] = {"upload_page": "/upload_code"}
    HEX_ID_LENGTH: int = 32
    DB_INFO: Dict[str, Any] = {}
    AWS_CRED: Dict[str, Any] = {}
    AWS_BUCKET: str = ""
    JWT_SECRET_KEY: str = "change-me"
    CORS_ORIGIN: str = "http://localhost:3000"
    VISION_OCR: Dict[str, Any] = {}

    @field_validator("DB_INFO", "AWS_CRED", "VISION_OCR", "links", mode="before")
    @classmethod
    def _parse_json(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    @field_validator("SUPP_LANG", "LANG_CLASS", mode="before")
    @classmethod
    def _parse_list(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value


settings = Settings()
