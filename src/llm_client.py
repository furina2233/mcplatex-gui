# llm_client.py
import os
from pathlib import Path

import httpx
import instructor
import openai
from dotenv import load_dotenv

from utils.log_util import log_util
from utils.model_config import load_model_config_values

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

TIMEOUT_CONFIG = httpx.Timeout(180.0, connect=60.0)


def normalize_openai_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized[: -len("/chat/completions")]
    return normalized


def log_request(request: httpx.Request):
    try:
        body_content = request.content.decode("utf-8") if isinstance(request.content, bytes) else str(request.content)
        log_util.log_request_body(body_content)
    except Exception as exc:
        log_util.log_request_body(f"Failed to log request body: {exc}")


def log_response(response: httpx.Response):
    try:
        response.read()
        response_content = (
            response.content.decode("utf-8") if isinstance(response.content, bytes) else str(response.content)
        )
        log_util.log_response_body(response_content)
    except Exception as exc:
        log_util.log_response_body(f"Failed to log response body: {exc}")


async def async_log_request(request: httpx.Request):
    try:
        body_content = request.content.decode("utf-8") if isinstance(request.content, bytes) else str(request.content)
        log_util.log_request_body(body_content)
    except Exception as exc:
        log_util.log_request_body(f"Failed to log request body: {exc}")


async def async_log_response(response: httpx.Response):
    try:
        response.read()
        response_content = (
            response.content.decode("utf-8") if isinstance(response.content, bytes) else str(response.content)
        )
        log_util.log_response_body(response_content)
    except Exception as exc:
        log_util.log_response_body(f"Failed to log response body: {exc}")


def build_sync_instructor_client(api_key: str, base_url: str, *, json_mode: bool = False):
    http_client = httpx.Client(timeout=TIMEOUT_CONFIG)
    http_client.event_hooks["request"] = [log_request]
    http_client.event_hooks["response"] = [log_response]

    client = openai.OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=TIMEOUT_CONFIG,
        http_client=http_client,
    )
    if json_mode:
        return instructor.from_openai(client, mode=instructor.Mode.JSON)
    return instructor.from_openai(client)


def build_async_instructor_client(api_key: str, base_url: str, *, json_mode: bool = False):
    http_client = httpx.AsyncClient(timeout=TIMEOUT_CONFIG)
    http_client.event_hooks["request"] = [async_log_request]
    http_client.event_hooks["response"] = [async_log_response]

    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=TIMEOUT_CONFIG,
        http_client=http_client,
    )
    if json_mode:
        return instructor.from_openai(client, mode=instructor.Mode.JSON)
    return instructor.from_openai(client)


TEXT_API_KEY = ""
TEXT_BASE_URL = ""
TEXT_MODEL = "gpt-5.4-mini"
text_client = None
text_async_client = None

VISUAL_API_KEY = ""
VISUAL_BASE_URL = ""
VISUAL_MODEL = "qwen3-vl-plus"
visual_client = None
visual_async_client = None


def reload_model_clients():
    global TEXT_API_KEY, TEXT_BASE_URL, TEXT_MODEL, text_client, text_async_client
    global VISUAL_API_KEY, VISUAL_BASE_URL, VISUAL_MODEL, visual_client, visual_async_client

    values = load_model_config_values()

    TEXT_API_KEY = values.get("TEXT_API_KEY", "")
    TEXT_BASE_URL = normalize_openai_base_url(values.get("TEXT_BASE_URL", ""))
    TEXT_MODEL = values.get("TEXT_MODEL", "gpt-5.4-mini") or "gpt-5.4-mini"

    if TEXT_API_KEY and TEXT_BASE_URL:
        text_client = build_sync_instructor_client(TEXT_API_KEY, TEXT_BASE_URL)
        text_async_client = build_async_instructor_client(TEXT_API_KEY, TEXT_BASE_URL)
    else:
        text_client = None
        text_async_client = None

    VISUAL_API_KEY = values.get("VISUAL_API_KEY", "")
    VISUAL_BASE_URL = normalize_openai_base_url(values.get("VISUAL_BASE_URL", ""))
    VISUAL_MODEL = values.get("VISUAL_MODEL", "qwen3-vl-plus") or "qwen3-vl-plus"

    if VISUAL_API_KEY and VISUAL_BASE_URL:
        visual_client = build_sync_instructor_client(VISUAL_API_KEY, VISUAL_BASE_URL, json_mode=True)
        visual_async_client = build_async_instructor_client(VISUAL_API_KEY, VISUAL_BASE_URL, json_mode=True)
    else:
        visual_client = None
        visual_async_client = None


reload_model_clients()

__all__ = [
    "TEXT_MODEL",
    "reload_model_clients",
    "text_client",
    "text_async_client",
    "VISUAL_MODEL",
    "visual_client",
    "visual_async_client",
]
