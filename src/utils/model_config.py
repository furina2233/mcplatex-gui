from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


REQUIRED_MODEL_ENV_KEYS = [
    "TEXT_API_KEY",
    "TEXT_BASE_URL",
    "TEXT_MODEL",
    "VISUAL_API_KEY",
    "VISUAL_BASE_URL",
    "VISUAL_MODEL",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def env_file_path() -> Path:
    return project_root() / ".env"


def load_model_config_values() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = env_file_path()
    if env_path.exists():
        values.update({key: value or "" for key, value in dotenv_values(env_path).items() if key})

    for key in REQUIRED_MODEL_ENV_KEYS:
        values[key] = os.getenv(key, values.get(key, "") or "")
    return values


def get_missing_model_config_keys(values: dict[str, str] | None = None) -> list[str]:
    resolved_values = values or load_model_config_values()
    return [key for key in REQUIRED_MODEL_ENV_KEYS if not str(resolved_values.get(key, "")).strip()]


def has_complete_model_config(values: dict[str, str] | None = None) -> bool:
    return not get_missing_model_config_keys(values)


def format_missing_model_config_message(missing_keys: list[str] | None = None) -> str:
    keys = missing_keys or get_missing_model_config_keys()
    if not keys:
        return ""
    return "、".join(keys)
