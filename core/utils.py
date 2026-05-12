"""
=====================================================================
 🔧 辅助函数模块
 包含：输出截断、安全路径检查、编码解码、格式化大小、
 高低水位线截断、超时执行包装器、交互式输入超时保护
=====================================================================
"""

import os
import sys
import time
import threading
from typing import Optional

from .config import SAFE_BASE_DIR, MAX_OUTPUT_LENGTH, LLM_TIMEOUT, MAX_RETRY_DELAY


# =====================================================================
# 输出截断
# =====================================================================
def _truncate_output(text: str, max_len: int = MAX_OUTPUT_LENGTH) -> str:
    """
    截断过长的输出文本。

    当输出文本超过 max_len 时，截断并在末尾添加省略提示。

    Args:
        text: 原始输出文本
        max_len: 最大允许长度（字符数）

    Returns:
        str: 截断后的文本
    """
    if len(text) > max_len:
        return text[:max_len] + f"\n\n... [输出过长，已截断至 {max_len} 字符]"
    return text


# =====================================================================
# 安全路径检查
# =====================================================================
def _safe_path_check(target_path: str) -> bool:
    """
    检查路径是否在安全目录内。

    安全策略：所有文件操作必须限制在 SAFE_BASE_DIR 及其子目录内。

    Args:
        target_path: 要检查的目标路径

    Returns:
        bool: 如果在安全目录内返回 True，否则返回 False
    """
    abs_path = os.path.abspath(target_path)
    return abs_path.startswith(SAFE_BASE_DIR)


# =====================================================================
# 终端输出解码
# =====================================================================
def _decode_terminal_bytes(raw_bytes: bytes) -> str:
    """
    智能解码终端输出。

    兼容 Windows GBK 和 Linux UTF-8 编码，自动尝试多种编码方式。

    Args:
        raw_bytes: 终端输出的原始字节

    Returns:
        str: 解码后的字符串
    """
    if not raw_bytes:
        return ""
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return raw_bytes.decode('gbk')
        except UnicodeDecodeError:
            return raw_bytes.decode('utf-8', errors='replace')


# =====================================================================
# 文件大小格式化
# =====================================================================
def _format_size(size_bytes: int) -> str:
    """
    将字节数格式化为人类可读的大小。

    自动选择合适的单位（B, KB, MB, GB）。

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小字符串（如 "1.5 MB"）
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# =====================================================================
# v31.0 新增：高低水位线截断函数（v2.0 - 安全切断点算法）
# =====================================================================
def _apply_watermark_truncation(
    messages: list,
    high_watermark: int = 70,
    low_watermark: int = 25
) -> list:
    """
    高低水位线安全滑动窗口截断（v2.0 - 安全切断点算法）。

    当消息数量超过高水位线时，保留系统消息 + 最近 low_watermark 条消息，
    并通过"寻找安全切断点"算法确保不会切断 tool_calls 与 ToolMessage 的配对关系。

    算法思路：
    1. 设定初始切断点 cut_idx = len(messages) - low_watermark
    2. 只要 cut_idx > 1，就检查 messages[cut_idx] 和 messages[cut_idx - 1]
    3. 如果 messages[cut_idx] 带有 tool_call_id（即它是 ToolMessage），
       或者 messages[cut_idx - 1] 带有 tool_calls（即切断了 AI 发起的工具请求），
       则将 cut_idx 减 1 继续向左寻找
    4. 直到找到不满足上述两点的"安全边界"为止跳出循环
    5. 最终返回 [messages[0]] + messages[cut_idx:] 组成的新列表

    Args:
        messages: 原始消息列表
        high_watermark: 高水位线，超过此值触发截断
        low_watermark: 低水位线，保留的最近消息数量

    Returns:
        list: 截断后的消息列表（如果未触发截断，返回原列表）
    """
    if len(messages) <= high_watermark:
        return messages

    # 步骤1：设定初始切断点
    cut_idx = len(messages) - low_watermark

    # 步骤2-4：向左寻找安全切断点
    while cut_idx > 1:
        current_msg = messages[cut_idx]
        prev_msg = messages[cut_idx - 1]

        # 检查当前消息是否是 ToolMessage（带有 tool_call_id）
        is_tool_message = hasattr(current_msg, 'tool_call_id') and current_msg.tool_call_id
        # 检查前一条消息是否带有 tool_calls（AI 发起的工具请求）
        is_ai_tool_call = hasattr(prev_msg, 'tool_calls') and prev_msg.tool_calls

        if is_tool_message or is_ai_tool_call:
            cut_idx -= 1  # 不安全，继续向左寻找
        else:
            break  # 找到安全边界，跳出循环

    # 步骤5：构建新消息列表
    new_messages = [messages[0]] + messages[cut_idx:]

    truncated_count = len(messages) - len(new_messages)
    print(f"   📐 高低水位线触发: {len(messages)} > {high_watermark}")
    print(f"   ✂️  截断 {truncated_count} 条消息, 保留 {len(new_messages)} 条")
    print(f"   🔗 安全切断点算法: cut_idx={cut_idx}")
    print(f"   📊 保留系统消息 + 最近 {len(messages) - cut_idx} 条消息")

    return new_messages


# =====================================================================
# v31.0 新增：超时执行包装器
# =====================================================================
class _TimeoutError(Exception):
    """超时异常"""
    pass


def _execute_with_timeout(func, args=None, kwargs=None, timeout: int = 120) -> object:
    """
    在指定超时时间内执行函数（v34.0 重构版）。

    使用 threading.Event + 更可靠的超时检测机制，超时后自动清理线程资源。
    解决了原版线程超时后残留导致后续调用卡死的问题。
    适用于 LLM 调用等可能长时间阻塞的操作。

    Args:
        func: 要执行的函数
        args: 位置参数元组
        kwargs: 关键字参数字典
        timeout: 超时时间（秒），默认 120

    Returns:
        object: 函数执行结果

    Raises:
        _TimeoutError: 超时后抛出
        Exception: 函数执行过程中的其他异常
    """
    args = args or ()
    kwargs = kwargs or {}

    result = [None]
    exception = [None]
    completed = threading.Event()

    def worker():
        try:
            result[0] = func(*args, **kwargs)
            completed.set()
        except Exception as e:
            exception[0] = e
            completed.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # 等待完成或超时
    finished = completed.wait(timeout)

    if not finished:
        # 超时：线程仍在运行（daemon=True 会在主线程退出时自动终止）
        raise _TimeoutError(f"函数执行超时 ({timeout}秒)")

    if exception[0]:
        raise exception[0]

    return result[0]


# =====================================================================
# v34.0 新增：交互式输入超时保护
# =====================================================================
def _input_with_timeout(prompt: str = "", timeout: int = 300) -> str:
    """
    带超时保护的交互式输入函数。

    使用 threading 实现输入超时控制，防止 stdin 阻塞导致程序永久卡死。
    适用于交互式命令行模式下的用户输入场景。

    Args:
        prompt: 输入提示文本
        timeout: 超时时间（秒），默认 300 秒（5分钟）

    Returns:
        str: 用户输入的文本，超时则返回空字符串

    Raises:
        _TimeoutError: 输入超时后抛出
    """
    result = [None]
    completed = threading.Event()

    def worker():
        try:
            result[0] = input(prompt)
            completed.set()
        except (EOFError, KeyboardInterrupt):
            # EOF 或 Ctrl+C 视为取消
            completed.set()
        except Exception:
            result[0] = ""
            completed.set()

    input_thread = threading.Thread(target=worker, daemon=True)
    input_thread.start()

    finished = completed.wait(timeout)

    if not finished:
        raise _TimeoutError(f"用户输入超时 ({timeout}秒)")

    return result[0] or ""
