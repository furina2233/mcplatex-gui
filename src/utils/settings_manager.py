import json
import os
from typing import Any


SETTINGS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")


DEFAULT_SETTINGS = {
    "max_retries": 5,
    "temperature": 0.1,
    "max_tokens": 32768,
}


def _ensure_settings_file() -> None:
    if not os.path.exists(SETTINGS_FILE_PATH):
        with open(SETTINGS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)


def load_settings() -> dict[str, Any]:
    _ensure_settings_file()
    with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings: dict[str, Any]) -> None:
    _ensure_settings_file()
    with open(SETTINGS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


def get_setting(key: str, default: Any = None) -> Any:
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> None:
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
