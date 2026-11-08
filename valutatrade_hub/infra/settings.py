
import json
import os
import tomllib
from typing import ClassVar

from valutatrade_hub.infra.metaclass import MetaClass


class SettingsLoader(metaclass=MetaClass):
    # Дефолтные знаения сохранятся, если json и toml окажутся недоступными
    _DEFAULTS: ClassVar[dict] = {
        "data_dir": "data",
        "users_data_file" : "users.json",
        "portfolios_data_file" : "portfolios.json",
        "rates_data_file" : "rates.json",
        "log_dir": "logs",
        "log_file": "actions.log",
        "parser_log_file": "parser.log",
        "log_fmt" : "[%(levelname)s] [%(asctime)s] %(message)s",
        "log_date_fmt" : "%Y-%m-%d %H:%M:%S",
        "log_max_mb": 5,
        "log_count" : 5,
        "base_currency": "USD",
        "RATES_TTL_SECONDS": 300
    }

    CONFIG_JSON = "config.json"
    PYPROJECT = "pyproject.toml"

    def __init__(self):
        self._config = self._load()

    def _load(self) -> dict:
        config = dict(self._DEFAULTS)

        # TOML (перезаписывает дефолты)
        if os.path.exists(self.PYPROJECT):
            try:
                with open(self.PYPROJECT, "rb") as f:
                    data = tomllib.load(f)
                tool_section = data.get("tool", {})
                valutatrade_section = tool_section.get("valutatrade", {})
                config.update(valutatrade_section)
            except tomllib.TOMLDecodeError:
                pass  # битый toml — не применяем

        # JSON (высший приоритет)
        if os.path.exists(self.CONFIG_JSON):
            try:
                with open(self.CONFIG_JSON, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass  # битый json — не применяем

        return config

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def reload(self) -> None:
        self._config = self._load()
