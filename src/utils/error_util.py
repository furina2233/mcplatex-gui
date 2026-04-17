from __future__ import annotations

import re

_MODEL_CONFIG_ERROR_PATTERNS = [
    r"api[-_ ]?key",
    r"authentication",
    r"unauthori[sz]ed",
    r"invalid\s+api\s+key",
    r"base\s*url",
    r"\bbase_url\b",
    r"failed to connect",
    r"connection refused",
    r"name or service not known",
    r"dns",
    r"timed? out",
    r"not found",
    r"does not exist",
    r"unknown model",
    r"model name",
    r"environment variables are not configured",
    r"please check \.env",
]

_MODEL_CONFIG_EXCEPTION_TYPES = {
    "AuthenticationError",
    "APIConnectionError",
    "APITimeoutError",
    "BadRequestError",
    "NotFoundError",
    "APIStatusError",
    "ValueError",
}


def is_model_config_error(message: str | None = None, exception_type: str | None = None) -> bool:
    text = " ".join(part for part in (exception_type or "", message or "") if part).lower()
    if not text:
        return False

    if exception_type in _MODEL_CONFIG_EXCEPTION_TYPES:
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in _MODEL_CONFIG_ERROR_PATTERNS):
            return True

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in _MODEL_CONFIG_ERROR_PATTERNS)


def get_user_facing_error_message(message: str | None = None, exception_type: str | None = None) -> str:
    if is_model_config_error(message, exception_type):
        return "\u8bf7\u68c0\u67e5\u6a21\u578b\u914d\u7f6e"
    return message or "\u64cd\u4f5c\u5931\u8d25"
