"""
=====================================================================
 🔍 网络搜索工具集
 包含：read_webpage, web_search
=====================================================================
"""

import os
import sys
import json
import time
import subprocess
from typing import Optional

from langchain_core.tools import tool

from core.config import SAFE_BASE_DIR, SEARCH_TIMEOUT, logger
from core.utils import _truncate_output


# =====================================================================
# 📖 read_webpage
# =====================================================================
@tool
def read_webpage(url: str) -> str:
    """
    使用 requests + BeautifulSoup 抓取目标网页的正文内容。

    Args:
        url: 要抓取的网页 URL

    Returns:
        str: 网页正文内容
    """
    if not url.startswith(('http://', 'https://')):
        return f"无效的 URL: {url}。URL 必须以 http:// 或 https:// 开头。"

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return "需要安装 requests 和 beautifulsoup4: pip install requests beautifulsoup4"

    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        resp = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        resp.encoding = resp.apparent_encoding

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 提取正文
        text = soup.get_text(separator='\n', strip=True)

        # 清理多余空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 截断
        text = _truncate_output(text, max_len=10000)

        return (
            f"网页: {url}\n"
            f"状态码: {resp.status_code}\n"
            f"编码: {resp.encoding}\n"
            f"{'=' * 60}\n"
            f"{text}"
        )
    except Exception as e:
        return f"抓取失败: {e}"


# =====================================================================
# 🌐 web_search
# =====================================================================
@tool
def web_search(query: str) -> str:
    """
    遇到未知报错、查阅文档或寻找思路时调用。支持多引擎回退。

    使用 DuckDuckGo 搜索引擎，如果失败则回退到其他引擎。

    Args:
        query: 搜索关键词

    Returns:
        str: 搜索结果
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "需要安装 duckduckgo_search: pip install duckduckgo_search"

    result_parts = [
        f"搜索: {query}",
        "=" * 60,
    ]

    # 尝试 DuckDuckGo
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                for i, r in enumerate(results, 1):
                    title = r.get('title', '无标题')
                    snippet = r.get('body', '无摘要')
                    link = r.get('href', '无链接')
                    result_parts.append(f"\n[{i}] {title}")
                    result_parts.append(f"    摘要: {snippet[:200]}")
                    result_parts.append(f"    链接: {link}")
                return "\n".join(result_parts)
    except Exception as e:
        result_parts.append(f"DuckDuckGo 搜索失败: {e}")

    # 回退：使用 requests + 搜索引擎
    result_parts.append("\n尝试备用搜索方案...")
    try:
        import requests
        from bs4 import BeautifulSoup

        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36'
            )
        }
        resp = requests.get(search_url, headers=headers, timeout=SEARCH_TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')

        results = soup.select('.result__body')
        for i, result in enumerate(results[:5], 1):
            title_tag = result.select_one('.result__title')
            snippet_tag = result.select_one('.result__snippet')
            title = title_tag.get_text(strip=True) if title_tag else '无标题'
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else '无摘要'
            result_parts.append(f"\n[{i}] {title}")
            result_parts.append(f"    摘要: {snippet[:200]}")

        if results:
            return "\n".join(result_parts)
    except Exception as e:
        result_parts.append(f"备用搜索也失败: {e}")

    result_parts.append("\n所有搜索方案均失败。")
    return "\n".join(result_parts)
