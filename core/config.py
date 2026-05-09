"""
=====================================================================
 🔒 安全策略与全局配置
=====================================================================
"""

import os
import sys
import re
import logging
from typing import List

# =====================================================================
# 📋 日志配置
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Agent")

# =====================================================================
# 🔒 安全策略与全局配置
# =====================================================================
# 安全基目录：所有文件操作限制在此目录及其子目录内
SAFE_BASE_DIR: str = os.path.abspath(os.getcwd())

# 高危命令黑名单：匹配到这些模式的操作将被拦截
DANGEROUS_COMMANDS: List[str] = [
    r"rm\s+-r", r"rm\s+-f", r"del\s+/s", r"del\s+/q", r"rmdir\s+/s",
    r"format\s+", r"mkfs", r"diskpart", r"dd\s+if=", r"sudo\s+", r"su\s+",
    r"chmod\s+-R\s+777", r"chown\s+-R", r"killall", r"shutdown", r"reboot",
    r"init\s+0", r"reg\s+delete", r"reg\s+add", r">\s+/dev/sd", r"mkfs\.",
]

# 输出截断长度（字符数）
MAX_OUTPUT_LENGTH: int = 20000
# 工具调用最大重试次数
MAX_RETRIES: int = 3
# 网络请求超时时间（秒）
SEARCH_TIMEOUT: int = 15
# Agent 最大循环步数
DEFAULT_MAX_STEPS: int = 500
# LLM 调用超时时间（秒）- v31.0 新增
LLM_TIMEOUT: int = 120
# 最大重试延迟（秒）- v31.0 新增
MAX_RETRY_DELAY: int = 30

# =====================================================================
# pip_install 专属配置
# =====================================================================
PIP_PYTHON_EXE = r"D:\ProgramData\anaconda3\envs\ai_agent\python.exe"
PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_MAX_RETRIES = 3

# =====================================================================
# Git 工具配置
# =====================================================================
GIT_EXECUTABLE = ""
GIT_ENV_CACHED = {}

# =====================================================================
# file_backup_tool 配置
# =====================================================================
BACKUP_DIR: str = os.path.join(SAFE_BASE_DIR, ".agent_backups")
