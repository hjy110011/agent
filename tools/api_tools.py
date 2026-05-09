"""
=====================================================================
 🌐 API 工具模块 - 类似 Postman 的 HTTP 请求工具 (v42.0)

 提供：
   - send_api_request: 发送 HTTP 请求，支持 GET/POST/PUT/DELETE/PATCH
   - 自动 JSON 解析与格式化输出
   - 优雅的超时与异常处理
=====================================================================
"""

import json
import logging
from typing import Optional, Dict, Any

import requests
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 30

# 支持的 HTTP 方法
SUPPORTED_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}


@tool
def send_api_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    发送 HTTP API 请求，类似 Postman 的使用体验。

    支持 GET、POST、PUT、DELETE、PATCH 等常见 HTTP 方法，
    自动处理 JSON 请求/响应，优雅处理超时和异常。

    Args:
        url: 请求的目标 URL（必填），例如 "https://api.example.com/data"
        method: HTTP 请求方法，默认 'GET'。
                支持: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
        headers: 请求头字典（可选），例如 {"Authorization": "Bearer xxx", "Content-Type": "application/json"}
        body: 请求体字典（可选），仅 POST/PUT/PATCH 有效，会自动转为 JSON
        timeout: 超时时间（秒），默认 30

    Returns:
        str: 格式化后的响应结果，包含状态码、响应头和响应体
    """
    # ── 参数校验 ──────────────────────────────────────────────
    if not url or not isinstance(url, str):
        return "错误：url 参数不能为空，且必须是字符串类型。"

    method = method.upper().strip()
    if method not in SUPPORTED_METHODS:
        return (
            "错误：不支持的 HTTP 方法 '" + method + "'。"
            "支持的方法: " + ', '.join(sorted(SUPPORTED_METHODS))
        )

    if timeout <= 0:
        timeout = DEFAULT_TIMEOUT

    # ── 构建请求参数 ──────────────────────────────────────────
    request_headers = headers or {}
    request_body = body

    # 如果没有指定 Content-Type，且 body 是 dict，自动设为 application/json
    content_type = request_headers.get('Content-Type', '').lower()
    if request_body is not None and 'application/json' not in content_type:
        request_headers.setdefault('Content-Type', 'application/json')

    # ── 打印请求信息（类似 Postman 的请求预览） ──────────────
    request_summary_lines = [
        "请求信息",
        "   URL:    " + method + " " + url,
        "   方法:   " + method,
        "   超时:   " + str(timeout) + "秒",
    ]
    if request_headers:
        request_summary_lines.append(
            "   请求头: " + json.dumps(request_headers, ensure_ascii=False, indent=2))
    if request_body is not None:
        request_summary_lines.append(
            "   请求体: " + json.dumps(request_body, ensure_ascii=False, indent=2))

    print("\n".join(request_summary_lines))

    # ── 发送请求 ──────────────────────────────────────────────
    try:
        # 根据 method 选择对应的 requests 方法
        method_lower = method.lower()
        http_func = getattr(requests, method_lower, None)

        if http_func is None:
            return "错误：requests 库不支持方法 '" + method + "'。"

        # 发起请求
        response = http_func(
            url,
            headers=request_headers,
            json=request_body if request_body is not None else None,
            timeout=timeout,
        )

        # ── 格式化响应结果 ────────────────────────────────────
        status_code = response.status_code
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)

        result_lines = [
            "\n响应结果",
            "   状态码: " + str(status_code) + " (" + _get_status_text(status_code) + ")",
            "   耗时:   " + str(elapsed_ms) + "ms",
        ]

        # 响应头
        response_headers = dict(response.headers)
        result_lines.append(
            "   响应头: " + json.dumps(response_headers, ensure_ascii=False, indent=2))

        # 响应体 - 尝试解析为 JSON 并美化
        content_type_response = response.headers.get('Content-Type', '').lower()
        if 'application/json' in content_type_response:
            response_data = response.json()
            result_lines.append(
                "   响应体 (JSON):\n"
                + json.dumps(response_data, ensure_ascii=False, indent=2)
            )
        else:
            # 尝试解析 JSON（即使 Content-Type 不是 application/json）
            try:
                response_data = response.json()
                result_lines.append(
                    "   响应体 (检测为JSON):\n"
                    + json.dumps(response_data, ensure_ascii=False, indent=2)
                )
            except (json.JSONDecodeError, ValueError):
                # 纯文本响应
                text = response.text
                if len(text) > 5000:
                    text = text[:5000] + "\n... (响应体过长，已截断至5000字符)"
                result_lines.append("   响应体 (文本):\n" + text)

        return "\n".join(result_lines)

    except requests.exceptions.Timeout:
        error_msg = (
            "\n请求超时"
            "\n   URL: " + method + " " + url +
            "\n   超时时间: " + str(timeout) + "秒" +
            "\n   建议: 检查网络连接或增大 timeout 参数"
        )
        logger.error("API 请求超时: %s %s (timeout=%ss)", method, url, timeout)
        return error_msg

    except requests.exceptions.ConnectionError as e:
        error_msg = (
            "\n连接失败"
            "\n   URL: " + method + " " + url +
            "\n   错误: " + str(e) +
            "\n   建议: 检查 URL 是否正确，或网络是否可达"
        )
        logger.error("API 连接失败: %s %s - %s", method, url, e)
        return error_msg

    except requests.exceptions.HTTPError as e:
        error_msg = (
            "\nHTTP 错误"
            "\n   URL: " + method + " " + url +
            "\n   错误: " + str(e)
        )
        logger.error("API HTTP 错误: %s %s - %s", method, url, e)
        return error_msg

    except requests.exceptions.RequestException as e:
        error_msg = (
            "\n请求异常"
            "\n   URL: " + method + " " + url +
            "\n   错误: " + str(e)
        )
        logger.error("API 请求异常: %s %s - %s", method, url, e)
        return error_msg

    except Exception as e:
        error_msg = (
            "\n未知错误"
            "\n   URL: " + method + " " + url +
            "\n   错误类型: " + type(e).__name__ +
            "\n   错误信息: " + str(e)
        )
        logger.error("API 未知错误: %s %s - %s: %s", method, url, type(e).__name__, e)
        return error_msg


def _get_status_text(status_code: int) -> str:
    """
    获取 HTTP 状态码的文本描述。

    Args:
        status_code: HTTP 状态码

    Returns:
        str: 状态码描述
    """
    status_texts = {
        # 1xx 信息
        100: "Continue", 101: "Switching Protocols",
        # 2xx 成功
        200: "OK", 201: "Created", 202: "Accepted",
        204: "No Content",
        # 3xx 重定向
        301: "Moved Permanently", 302: "Found", 304: "Not Modified",
        # 4xx 客户端错误
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 408: "Request Timeout",
        409: "Conflict", 422: "Unprocessable Entity", 429: "Too Many Requests",
        # 5xx 服务器错误
        500: "Internal Server Error", 502: "Bad Gateway",
        503: "Service Unavailable", 504: "Gateway Timeout",
    }
    return status_texts.get(status_code, "Unknown Status")


# =====================================================================
# 便捷辅助函数（非 tool，供内部使用）
# =====================================================================

def _format_curl(url: str, method: str = 'GET',
                 headers: Optional[Dict[str, str]] = None,
                 body: Optional[Dict[str, Any]] = None) -> str:
    """
    将请求参数转换为 curl 命令（调试用）。

    Args:
        url: 请求 URL
        method: HTTP 方法
        headers: 请求头
        body: 请求体

    Returns:
        str: 等效的 curl 命令字符串
    """
    parts = ["curl"]
    if method != 'GET':
        parts.extend(["-X", method])

    if headers:
        for key, value in headers.items():
            parts.extend(["-H", "'" + key + ": " + value + "'"])

    if body:
        parts.extend(["-d", "'" + json.dumps(body) + "'"])

    parts.append("'" + url + "'")
    return " ".join(parts)
