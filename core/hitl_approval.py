"""
=====================================================================
 🤝 HITL (Human-In-The-Loop) 人工审批模块
 提供 request_human_approval 函数，用于在执行高危操作前请求人工确认。

 设计模式：策略模式
 - NoneApproval：免审批模式，所有操作直接放行
 - DangerousOnlyApproval：高危审批模式，只审批高危命令

 环境检测：
 - 自动检测是否在终端环境（sys.stdin.isatty()）
 - 非终端环境（如 Web UI）自动使用免审批模式

 超时保护：
 - 使用 threading.Timer 实现跨平台超时输入
 - 超时后默认拒绝（返回 "REJECTED"）
=====================================================================
"""

import sys
import re
import threading
import logging
from typing import List, Optional

from core.config import DANGEROUS_COMMANDS, APPROVAL_MODE, ENABLE_HITL

logger = logging.getLogger("Agent")

# =====================================================================
# 📋 常量定义
# =====================================================================
# 审批超时时间（秒）
APPROVAL_TIMEOUT: int = 60

# 扩展高危命令关键词（用于正则匹配）
EXTRA_DANGEROUS_KEYWORDS: List[str] = [
    r"passwd", r"kill\b", r"pkill", r"systemctl", r"docker",
    r"mysql", r"drop\s+", r"truncate\s+", r"alter\s+",
    r"wget\b", r"curl\b",
]

# =====================================================================
# 🧠 策略基类与实现
# =====================================================================


class ApprovalStrategy:
    """审批策略基类"""

    def approve(self, tool_name: str, context: dict) -> str:
        """
        执行审批逻辑。

        Args:
            tool_name: 要执行的工具名称
            context: 上下文信息字典

        Returns:
            str: "ALLOW" / "REJECTED" / "FEEDBACK:xxx"
        """
        raise NotImplementedError


class NoneApproval(ApprovalStrategy):
    """策略A：免审批模式 - 所有操作直接放行"""

    def approve(self, tool_name: str, context: dict) -> str:
        return "ALLOW"


class DangerousOnlyApproval(ApprovalStrategy):
    """策略B：高危审批模式 - 只审批高危命令"""

    def approve(self, tool_name: str, context: dict) -> str:
        # 提取命令内容进行高危判断
        command = self._extract_command(tool_name, context)

        if not self._is_dangerous(command):
            # 非高危命令，直接放行
            return "ALLOW"

        # 高危命令，弹出审批提示
        return self._prompt_approval(tool_name, context)

    def _extract_command(self, tool_name: str, context: dict) -> str:
        """
        从上下文中提取要执行的命令字符串。

        优先从 context 中提取 command 字段，其次尝试拼接关键参数。
        """
        # 直接从 context 中提取
        command = context.get("command", "")
        if command:
            return command

        # 尝试从其他字段拼接
        parts = []
        for key in ("tool_name", "args", "kwargs", "params"):
            val = context.get(key)
            if val:
                parts.append(str(val))

        return " ".join(parts)

    def _is_dangerous(self, command: str) -> bool:
        """
        判断命令是否为高危命令。

        使用 config.DANGEROUS_COMMANDS 中的正则模式进行匹配，
        同时匹配扩展的高危关键词列表。
        """
        if not command:
            return False

        # 合并所有高危模式
        all_patterns = list(DANGEROUS_COMMANDS) + EXTRA_DANGEROUS_KEYWORDS

        for pattern in all_patterns:
            try:
                if re.search(pattern, command, re.IGNORECASE):
                    logger.debug(
                        "[高危检测] 命令 '%s' 匹配到高危模式: %s",
                        command,
                        pattern,
                    )
                    return True
            except re.error:
                # 忽略无效的正则表达式
                continue

        return False

    def _prompt_approval(self, tool_name: str, context: dict) -> str:
        """
        弹出审批提示，等待用户输入。

        使用 threading.Timer 实现超时保护，超时后默认拒绝。
        """
        # 构建上下文摘要
        context_summary = "\n".join(
            ["    %s: %s" % (k, v) for k, v in context.items()]
        )

        print("\n" + "=" * 60)
        print("⚠️  高危操作审批 - [%s]" % tool_name)
        print("-" * 60)
        print("  上下文信息:")
        print(context_summary)
        print("-" * 60)
        print("  [Y] 允许执行  |  [N] 拒绝执行  |  输入其他内容作为修改意见")
        print("  ⏱️  超时时间: %d 秒" % APPROVAL_TIMEOUT)
        print("=" * 60)

        # 使用 threading.Timer 实现超时输入
        user_input_container: List[Optional[str]] = [None]
        input_timer: Optional[threading.Timer] = None

        def _timeout_handler():
            """超时处理：设置超时标记"""
            user_input_container[0] = "__TIMEOUT__"
            print("\n[审批] ⏱️  输入超时，默认拒绝。")

        def _get_input():
            """在子线程中获取用户输入"""
            try:
                val = input(">>> ").strip()
                user_input_container[0] = val
            except (EOFError, KeyboardInterrupt):
                user_input_container[0] = "__INTERRUPT__"

        # 启动超时计时器
        input_timer = threading.Timer(APPROVAL_TIMEOUT, _timeout_handler)
        input_timer.daemon = True
        input_timer.start()

        # 等待用户输入（在主线程中阻塞）
        _get_input()

        # 取消计时器（如果输入在超时前到达）
        if input_timer.is_alive():
            input_timer.cancel()

        user_input = user_input_container[0]

        # 处理超时/中断
        if user_input == "__TIMEOUT__":
            return "REJECTED"
        if user_input == "__INTERRUPT__":
            print("\n[审批] 输入中断，默认拒绝。")
            return "REJECTED"

        # 处理用户输入
        if not user_input:
            print("[审批] 输入为空，默认拒绝。")
            return "REJECTED"

        if user_input.upper() == "Y":
            print("[审批] ✅ 已允许执行 [%s]" % tool_name)
            return "ALLOW"
        elif user_input.upper() == "N":
            print("[审批] ❌ 已拒绝执行 [%s]" % tool_name)
            return "REJECTED"
        else:
            print("[审批] 💬 收到修改意见: %s" % user_input)
            return "FEEDBACK:%s" % user_input


# =====================================================================
# 🔧 策略工厂与全局状态
# =====================================================================

# 当前使用的审批策略实例
_current_strategy: ApprovalStrategy = DangerousOnlyApproval()


def _create_strategy(mode: str) -> ApprovalStrategy:
    """
    根据模式名称创建对应的审批策略实例。

    Args:
        mode: 审批模式名称

    Returns:
        ApprovalStrategy: 对应的策略实例

    Raises:
        ValueError: 未知的审批模式
    """
    strategy_map = {
        "none": NoneApproval,
        "dangerous_only": DangerousOnlyApproval,
    }
    cls = strategy_map.get(mode)
    if cls is None:
        raise ValueError(
            "未知的审批模式 '%s'，可选值: %s"
            % (mode, ", ".join(sorted(strategy_map.keys())))
        )
    return cls()


def set_approval_strategy(mode: str) -> None:
    """
    设置审批策略。

    同时更新 config.APPROVAL_MODE 和本模块的策略实例。

    Args:
        mode: 审批模式，可选 "none" 或 "dangerous_only"
    """
    global _current_strategy
    from core.config import set_approval_mode as set_config_mode

    # 同步更新 config 中的模式
    set_config_mode(mode)

    # 创建并切换策略实例
    _current_strategy = _create_strategy(mode)
    logger.info("审批策略已切换为: %s", mode)


def is_dangerous_command(command: str) -> bool:
    """
    判断命令是否为高危命令。

    使用 config.DANGEROUS_COMMANDS 中的正则模式进行匹配。

    Args:
        command: 要判断的命令字符串

    Returns:
        bool: 是否为高危命令
    """
    if not command:
        return False

    all_patterns = list(DANGEROUS_COMMANDS) + EXTRA_DANGEROUS_KEYWORDS

    for pattern in all_patterns:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        except re.error:
            continue

    return False


# =====================================================================
# 🚀 核心接口（保持兼容）
# =====================================================================


def request_human_approval(tool_name: str, context: dict) -> str:
    """
    请求人工审批。

    根据当前审批策略和运行环境自动选择审批方式：
    - 非终端环境（如 Web UI）→ 自动使用免审批模式
    - 终端环境 → 根据 APPROVAL_MODE 选择对应策略

    Args:
        tool_name: 要执行的工具名称（如 "write_local_file"）
        context: 上下文信息字典，包含工具调用的关键参数

    Returns:
        str: 审批结果
            - "ALLOW" - 用户允许执行
            - "REJECTED" - 用户拒绝执行
            - "FEEDBACK:xxx" - 用户提供了修改意见
    """
    # 检测运行环境：非终端环境自动使用免审批模式
    if not sys.stdin.isatty():
        logger.info("[审批] 非终端环境（isatty=False），自动使用免审批模式")
        return "ALLOW"

    # 如果 ENABLE_HITL 为 False，直接放行（兼容旧配置）
    if not ENABLE_HITL:
        return "ALLOW"

    # 根据当前策略执行审批
    return _current_strategy.approve(tool_name, context)


# =====================================================================
# 🔄 初始化：根据 config 中的 APPROVAL_MODE 设置初始策略
# =====================================================================

# 模块加载时自动初始化策略
try:
    _current_strategy = _create_strategy(APPROVAL_MODE)
    logger.info("审批策略初始化完成，当前模式: %s", APPROVAL_MODE)
except ValueError as e:
    logger.warning("审批策略初始化失败: %s，使用默认策略", e)
    _current_strategy = DangerousOnlyApproval()
