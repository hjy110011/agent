"""
🌐 浏览器工具模块 - 高级动态网页抓取

使用 Playwright 无头浏览器渲染 JavaScript 动态内容，
支持等待页面加载、提取纯文本内容。
"""

import logging
import re
from langchain.tools import tool

logger = logging.getLogger(__name__)

# ============================================================
# 辅助函数：清洗 HTML 提取纯文本
# ============================================================


def _clean_html_text(html: str, max_length: int = 10000) -> str:
    """
    清洗 HTML，提取有意义的纯文本内容。

    步骤：
    1. 移除 <script> 及其内容
    2. 移除 <style> 及其内容
    3. 移除 HTML 注释 <!-- -->
    4. 移除 <svg> 及其内容
    5. 移除所有剩余 HTML 标签
    6. 解码常见 HTML 实体
    7. 合并空白字符
    8. 按句子分割重建段落
    9. 过滤过短碎片
    10. 截断最大长度
    """
    if not html:
        return ""

    text = html

    # 1. 移除 script 标签及其内容
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. 移除 style 标签及其内容
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 3. 移除 HTML 注释
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # 4. 移除 svg 标签及其内容
    text = re.sub(r'<svg[^>]*>.*?</svg>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 5. 移除所有剩余的 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)

    # 6. 解码 HTML 实体
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&#39;': "'", '&nbsp;': ' ', '&copy;': '©', '&reg;': '®',
        '&trade;': '™', '&mdash;': '—', '&ndash;': '–',
        '&hellip;': '…', '&bull;': '•', '&middot;': '·',
        '&raquo;': '»', '&laquo;': '«', '&rsquo;': "'", '&lsquo;': "'",
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    # 解码数字实体 &#NNN; 和 &#xHH;
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)

    # 7. 合并空白字符
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # 8. 按句尾标点分割重建段落
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    paragraphs = []
    current_para = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        current_para.append(sentence)
        # 如果句子以句尾标点结束，或当前段落达到一定长度，结束段落
        if re.search(r'[。！？.!?]$', sentence) or len(''.join(current_para)) > 200:
            paragraphs.append(''.join(current_para))
            current_para = []
    if current_para:
        paragraphs.append(''.join(current_para))

    # 9. 过滤过短碎片（少于10字符且无中文）
    filtered = []
    for p in paragraphs:
        p = p.strip()
        if len(p) < 10 and not re.search(r'[\u4e00-\u9fff]', p):
            continue
        filtered.append(p)

    # 10. 截断最大长度
    result = '\n\n'.join(filtered)
    if len(result) > max_length:
        result = result[:max_length] + f'\n\n... [内容已截断，共 {max_length} 字符]'

    return result


# ============================================================
# 核心工具函数
# ============================================================

@tool
def fetch_dynamic_webpage(
    url: str,
    wait_time: int = 2,
    timeout: int = 30,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
) -> str:
    """
    使用 Playwright 无头浏览器访问网页，等待 JavaScript 渲染完成后提取纯文本内容。

    适用于需要 JavaScript 渲染的动态网页、SPA 应用、在线文档等。

    Args:
        url: 目标网页的完整 URL（必须包含 http:// 或 https://）
        wait_time: 页面加载后等待的秒数，确保 JavaScript 渲染完成（默认 2 秒）
        timeout: 总超时时间（秒），包括页面加载和等待时间（默认 30 秒）
        viewport_width: 浏览器视口宽度（默认 1920）
        viewport_height: 浏览器视口高度（默认 1080）

    Returns:
        包含页面纯文本内容的格式化字符串，包含来源 URL、状态、耗时和文本长度信息
    """
    import time

    start_time = time.time()

    # 参数校验
    if not url or not isinstance(url, str):
        return "❌ 错误：请提供有效的 URL"

    if not url.startswith(('http://', 'https://')):
        return "❌ 错误：URL 必须以 http:// 或 https:// 开头"

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        logger.info(f"🌐 Playwright 正在访问: {url}")

        with sync_playwright() as p:
            # 启动 Chromium 无头浏览器
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            # 创建浏览器上下文（模拟真实浏览器）
            context = browser.new_context(
                viewport={'width': viewport_width, 'height': viewport_height},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )

            # 创建新页面
            page = context.new_page()

            # 设置超时并访问页面
            page.set_default_timeout(timeout * 1000)  # 转换为毫秒

            try:
                page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            except PlaywrightTimeout:
                logger.warning(f"⏰ 页面加载超时({timeout}s)，尝试获取已加载的内容...")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                except Exception:
                    pass

            # 等待额外时间让 JavaScript 渲染完成
            if wait_time > 0:
                logger.info(f"⏳ 等待 {wait_time} 秒让 JavaScript 渲染...")
                time.sleep(wait_time)

            # 获取页面标题
            page_title = page.title()

            # 获取页面完整 HTML
            html_content = page.content()

            # 关闭浏览器
            browser.close()

        elapsed = time.time() - start_time

        # 清洗 HTML 提取纯文本
        plain_text = _clean_html_text(html_content)

        # 格式化输出
        result = (
            f"✅ 网页抓取成功\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 来源: {url}\n"
            f"📄 标题: {page_title}\n"
            f"⏱️  耗时: {elapsed:.2f} 秒\n"
            f"📏 文本长度: {len(plain_text)} 字符\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{plain_text}"
        )

        return result

    except ImportError:
        return (
            "❌ 错误：缺少 Playwright 库。请运行以下命令安装：\n"
            "   pip install playwright\n"
            "   playwright install chromium"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        logger.error(f"❌ Playwright 抓取失败 ({elapsed:.2f}s): {error_msg}")
        return (
            f"❌ 网页抓取失败\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 来源: {url}\n"
            f"⏱️  耗时: {elapsed:.2f} 秒\n"
            f"❌ 错误: {error_msg}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 提示：请检查 URL 是否正确，或网络是否可达。"
        )
