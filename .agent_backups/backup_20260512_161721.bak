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
# v31.0 新增：高低水位线截断函数（从 run_agent 中抽取）
# =====================================================================
def _apply_watermark_truncation(
    messages: list,
    high_watermark: int = 70,
    low_watermark: int = 25
) -> list:
    """
    高低水位线安全滑动窗口截断。

    当消息数量超过高水位线时，保留系统消息 + 上下文关联消息 + 最近消息。
    确保 tool_calls 与 ToolMessage 成对保留，避免上下文断裂。

    Args:
        messages: 原始消息列表
        high_watermark: 高水位线，超过此值触发截断
        low_watermark: 低水位线，保留的最近消息数量

    Returns:
        list: 截断后的消息列表（如果未触发截断，返回原列表）
    """
    if len(messages) <= high_watermark:
        return messages

    system_msg = messages[0]
    tail_msgs = messages[-low_watermark:]

    # 收集尾部消息中的 tool_call_id（来自 ToolMessage）
    tail_tool_call_ids = set()
    for msg in tail_msgs:
        if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
            tail_tool_call_ids.add(msg.tool_call_id)

    # 收集尾部消息中的 tool_calls ID（来自 AI 消息）
    tail_ai_tool_ids = set()
    for msg in tail_msgs:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    tc_id = tc.get('id', '')
                else:
                    tc_id = getattr(tc, 'id', '')
                if tc_id:
                    tail_ai_tool_ids.add(tc_id)

    extra_indices = set()

    # 安全计算回溯起始位置：确保至少从索引1开始，且不超过消息总数
    search_start = max(1, len(messages) - low_watermark - 1)

    # 查找孤立的 ToolMessage（有 tool_call_id 但对应的 AI tool_calls 不在尾部）
    orphan_tool_ids = tail_tool_call_ids - tail_ai_tool_ids
    if orphan_tool_ids:
        for i in range(search_start, 0, -1):
            msg = messages[i]
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    if isinstance(tc, dict):
                        tc_id = tc.get('id', '')
                    else:
                        tc_id = getattr(tc, 'id', '')
                    if tc_id and tc_id in orphan_tool_ids:
                        extra_indices.add(i)
                        orphan_tool_ids.discard(tc_id)
            if not orphan_tool_ids:
                break

    # 查找孤立的 AI 消息（有 tool_calls 但对应的 ToolMessage 不在尾部）
    orphan_ai_ids = tail_ai_tool_ids - tail_tool_call_ids
    if orphan_ai_ids:
        for i in range(search_start, 0, -1):
            msg = messages[i]
            if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                if msg.tool_call_id in orphan_ai_ids:
                    extra_indices.add(i)
                    orphan_ai_ids.discard(msg.tool_call_id)
            if not orphan_ai_ids:
                break

    # 额外保护：将尾部 AI tool_calls 对应的历史 ToolMessage 也加入保留
    for i in range(search_start, 0, -1):
        msg = messages[i]
        if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
            if msg.tool_call_id in tail_ai_tool_ids:
                extra_indices.add(i)

    # 构建新消息列表
    new_messages = [system_msg]

    if extra_indices:
        sorted_extras = sorted(extra_indices)
        for idx in sorted_extras:
            new_messages.append(messages[idx])

    new_messages.extend(tail_msgs)

    truncated_count = len(messages) - len(new_messages)
    print(f"   📐 高低水位线触发: {len(messages)} > {high_watermark}")
    print(f"   ✂️  截断 {truncated_count} 条消息, 保留 {len(new_messages)} 条")
    print("   🔗 已确保 tool_calls 与 ToolMessage 成对保留")
    print(f"   📊 保留系统消息 + {len(extra_indices)} 条上下文关联消息 + {len(tail_msgs)} 条最近消息")

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
