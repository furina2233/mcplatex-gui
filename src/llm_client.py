# llm_client.py
import os

import httpx
import instructor
import openai
from dotenv import load_dotenv

from utils.log_util import log_util

load_dotenv(override=True)

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


TEXT_API_KEY = os.getenv("TEXT_API_KEY")
TEXT_BASE_URL = normalize_openai_base_url(os.getenv("TEXT_BASE_URL", ""))
TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-5.4-mini")

if not TEXT_API_KEY or not TEXT_BASE_URL:
    raise ValueError("TEXT environment variables are not configured. Please check .env.")

text_client = build_sync_instructor_client(TEXT_API_KEY, TEXT_BASE_URL)
text_async_client = build_async_instructor_client(TEXT_API_KEY, TEXT_BASE_URL)

VISUAL_API_KEY = os.getenv("VISUAL_API_KEY")
VISUAL_BASE_URL = normalize_openai_base_url(os.getenv("VISUAL_BASE_URL", ""))
VISUAL_MODEL = os.getenv("VISUAL_MODEL", "qwen3-vl-plus")

if not VISUAL_API_KEY or not VISUAL_BASE_URL:
    raise ValueError("VISUAL environment variables are not configured. Please check .env.")

visual_client = build_sync_instructor_client(VISUAL_API_KEY, VISUAL_BASE_URL, json_mode=True)
visual_async_client = build_async_instructor_client(VISUAL_API_KEY, VISUAL_BASE_URL, json_mode=True)

__all__ = [
    "TEXT_MODEL",
    "text_client",
    "text_async_client",
    "VISUAL_MODEL",
    "visual_client",
    "visual_async_client",
]
