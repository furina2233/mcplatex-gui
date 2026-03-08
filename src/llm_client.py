# llm_client.py
import os
import instructor
import openai
from dotenv import load_dotenv
import httpx
from utils.log_util import log_util

# 加载 .env 文件中的环境变量
load_dotenv()

# 定义超时配置：连接 60s，读取 180s，写入 60s，池化 60s
TIMEOUT_CONFIG = httpx.Timeout(180.0, connect=60.0)

# 请求拦截器 - 记录请求体
def log_request(request: httpx.Request):
    try:
        # 获取请求体内容
        body_content = request.content.decode('utf-8') if isinstance(request.content, bytes) else str(request.content)
        # 记录请求体到日志
        log_util.log_request_body(body_content)
    except Exception as e:
        log_util.log_request_body(f"Failed to log request body: {str(e)}")

# 响应拦截器 - 记录响应体
def log_response(response: httpx.Response):
    try:
        # 获取响应体内容
        response.read()
        response_content = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)
        # 记录响应体到日志
        log_util.log_response_body(response_content)
    except Exception as e:
        log_util.log_response_body(f"Failed to log response body: {str(e)}")

# 异步请求拦截器
async def async_log_request(request: httpx.Request):
    try:
        # 获取请求体内容
        body_content = request.content.decode('utf-8') if isinstance(request.content, bytes) else str(request.content)
        # 记录请求体到日志
        log_util.log_request_body(body_content)
    except Exception as e:
        log_util.log_request_body(f"Failed to log request body: {str(e)}")

# 异步响应拦截器
async def async_log_response(response: httpx.Response):
    try:
        # 获取响应体内容
        response.read()
        response_content = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)
        # 记录响应体到日志
        log_util.log_response_body(response_content)
    except Exception as e:
        log_util.log_response_body(f"Failed to log response body: {str(e)}")

# --- DeepSeek 配置  ---
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not API_KEY or not BASE_URL:
    raise ValueError("DeepSeek 环境变量未配置，请检查 .env 文件")

# 默认客户端（同步）
sync_http_client = httpx.Client(timeout=TIMEOUT_CONFIG)
sync_http_client.event_hooks["request"] = [log_request]
sync_http_client.event_hooks["response"] = [log_response]

client = instructor.from_openai(
    openai.OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT_CONFIG,
        http_client=sync_http_client
    )
)

# 客户端（异步）
async_http_client = httpx.AsyncClient(timeout=TIMEOUT_CONFIG)
async_http_client.event_hooks["request"] = [async_log_request]
async_http_client.event_hooks["response"] = [async_log_response]

async_client = instructor.from_openai(
    openai.AsyncOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT_CONFIG,
        http_client=async_http_client
    )
)

# --- Monica 配置 ---
MONICA_API_KEY = os.getenv("MONICA_API_KEY")
MONICA_BASE_URL = os.getenv("MONICA_BASE_URL")
MONICA_MODEL = os.getenv("MONICA_MODEL", "gpt-4o")

if not MONICA_API_KEY or not MONICA_BASE_URL:
    raise ValueError("Monica 环境变量未配置，请检查 .env 文件")

# 视觉/多模态客户端（同步）
visual_sync_http_client = httpx.Client(timeout=TIMEOUT_CONFIG)
visual_sync_http_client.event_hooks["request"] = [log_request]
visual_sync_http_client.event_hooks["response"] = [log_response]

visual_client = instructor.from_openai(
    openai.OpenAI(
        api_key=MONICA_API_KEY,
        base_url=MONICA_BASE_URL,
        timeout=TIMEOUT_CONFIG,
        http_client=visual_sync_http_client
    ),
    mode=instructor.Mode.JSON,
)

# 视觉/多模态客户端（异步）
visual_async_http_client = httpx.AsyncClient(timeout=TIMEOUT_CONFIG)
visual_async_http_client.event_hooks["request"] = [async_log_request]
visual_async_http_client.event_hooks["response"] = [async_log_response]

visual_async_client = instructor.from_openai(
    openai.AsyncOpenAI(
        api_key=MONICA_API_KEY,
        base_url=MONICA_BASE_URL,
        timeout=TIMEOUT_CONFIG,
        http_client=visual_async_http_client
    ),
    mode=instructor.Mode.JSON,
)

# --- Gemini配置 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-image-preview")

if not GEMINI_API_KEY or not GEMINI_BASE_URL:
    raise ValueError("Gemini 环境变量未配置，请检查 .env 文件")

gemini_client = httpx.Client(timeout=TIMEOUT_CONFIG)
gemini_client.event_hooks["request"] = [log_request]
gemini_client.event_hooks["response"] = [log_response]

gemini_client = instructor.from_openai(
    openai.OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL,
        timeout=TIMEOUT_CONFIG,
    ),
    mode=instructor.Mode.JSON,
)

__all__ = [
    "client",
    "async_client",
    "MODEL",
    "visual_client",
    "visual_async_client",
    "MONICA_MODEL",
    "GEMINI_MODEL",
    "gemini_client"
]