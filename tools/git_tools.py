"""
=====================================================================
 🗃️ Git 版本控制工具集
 包含：git_init_repo, git_create_branch, git_commit,
       git_diff, git_status, git_log, git_checkout, git_branch_list
=====================================================================
"""

import os
import sys
import subprocess
from typing import Optional

from langchain_core.tools import tool

from core.config import SAFE_BASE_DIR, GIT_EXECUTABLE, GIT_ENV_CACHED, logger
from core.utils import _safe_path_check, _decode_terminal_bytes


# =====================================================================
# Git 辅助函数
# =====================================================================
def _find_git() -> str:
    """查找系统 git 可执行文件路径"""
    if GIT_EXECUTABLE:
        return GIT_EXECUTABLE
    for candidate in ["git", "git.exe"]:
        try:
            proc = subprocess.run([candidate, "--version"], capture_output=True, timeout=5)
            if proc.returncode == 0:
                return candidate
        except Exception:
            continue
    return "git"


def _get_git_env() -> dict:
    """获取 Git 环境变量"""
    if GIT_ENV_CACHED:
        return GIT_ENV_CACHED
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _run_git(args: list, repo_path: str = "") -> str:
    """执行 Git 命令"""
    git_exe = _find_git()
    cmd = [git_exe] + args
    if repo_path:
        cwd = os.path.abspath(repo_path)
    else:
        cwd = SAFE_BASE_DIR

    try:
        proc = subprocess.run(
            cmd, capture_output=True, timeout=30, text=True,
            cwd=cwd, env=_get_git_env()
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if proc.returncode != 0:
            return f"Git 错误: {stderr or stdout}"
        return stdout or "(无输出)"
    except subprocess.TimeoutExpired:
        return "Git 命令执行超时 (30秒)"
    except FileNotFoundError:
        return "Git 未安装或不在 PATH 中。请安装 Git: https://git-scm.com/"
    except Exception as e:
        return f"Git 命令执行失败: {e}"


# =====================================================================
# 🚀 git_init_repo
# =====================================================================
@tool
def git_init_repo(repo_path: str = "") -> str:
    """
    在指定目录初始化一个新的 Git 仓库（git init）。

    Args:
        repo_path: 仓库路径，默认当前目录

    Returns:
        str: 初始化结果
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    os.makedirs(target, exist_ok=True)
    result = _run_git(["init"], repo_path=target)
    return f"Git 仓库初始化: {target}\n{result}"


# =====================================================================
# 🌿 git_create_branch
# =====================================================================
@tool
def git_create_branch(branch_name: str, repo_path: str = "") -> str:
    """
    创建并切换到新分支（git checkout -b）。
    如果分支已存在，则直接切换到该分支。

    Args:
        branch_name: 分支名称
        repo_path: 仓库路径，默认当前目录

    Returns:
        str: 分支操作结果
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    # 检查分支是否已存在
    branches = _run_git(["branch", "--list", branch_name], repo_path=target)
    if branch_name in branches:
        result = _run_git(["checkout", branch_name], repo_path=target)
        return f"切换到已有分支: {branch_name}\n{result}"
    else:
        result = _run_git(["checkout", "-b", branch_name], repo_path=target)
        return f"创建并切换到新分支: {branch_name}\n{result}"


# =====================================================================
# 💾 git_commit
# =====================================================================
@tool
def git_commit(message: str, repo_path: str = "", auto_add: bool = True) -> str:
    """
    提交当前更改到 Git 仓库（git add + git commit）。

    Args:
        message: 提交信息
        repo_path: 仓库路径，默认当前目录
        auto_add: 是否自动暂存所有更改，默认True

    Returns:
        str: 提交结果
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    if auto_add:
        add_result = _run_git(["add", "-A"], repo_path=target)
        if "错误" in add_result:
            return f"暂存失败: {add_result}"

    result = _run_git(["commit", "-m", message], repo_path=target)
    return f"提交: {message}\n{result}"


# =====================================================================
# 📊 git_diff
# =====================================================================
@tool
def git_diff(repo_path: str = "", file_path: str = "", staged: bool = False) -> str:
    """
    查看 Git 工作区与暂存区/HEAD 的差异（git diff）。

    Args:
        repo_path: 仓库路径，默认当前目录
        file_path: 指定文件路径（可选）
        staged: 是否查看已暂存的差异，默认False

    Returns:
        str: 差异内容
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    args = ["diff"]
    if staged:
        args.append("--staged")
    if file_path:
        args.append(file_path)

    result = _run_git(args, repo_path=target)
    if not result or result == "(无输出)":
        return "无差异内容。"
    return result


# =====================================================================
# 📋 git_status
# =====================================================================
@tool
def git_status(repo_path: str = "") -> str:
    """
    查看 Git 仓库当前状态（git status）。

    Args:
        repo_path: 仓库路径，默认当前目录

    Returns:
        str: 仓库状态
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    return _run_git(["status"], repo_path=target)


# =====================================================================
# 📜 git_log
# =====================================================================
@tool
def git_log(repo_path: str = "", max_count: int = 10, branch: str = "") -> str:
    """
    查看 Git 提交历史（git log）。

    Args:
        repo_path: 仓库路径，默认当前目录
        max_count: 最大显示条数，默认10
        branch: 指定分支（可选）

    Returns:
        str: 提交历史
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    args = ["log", f"--max-count={max_count}", "--oneline", "--graph"]
    if branch:
        args.append(branch)

    return _run_git(args, repo_path=target)


# =====================================================================
# 🔀 git_checkout
# =====================================================================
@tool
def git_checkout(branch_name: str, repo_path: str = "") -> str:
    """
    切换到指定分支（git checkout）。
    如果分支不存在则报错提示。

    Args:
        branch_name: 分支名称
        repo_path: 仓库路径，默认当前目录

    Returns:
        str: 切换结果
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    return _run_git(["checkout", branch_name], repo_path=target)


# =====================================================================
# 📋 git_branch_list
# =====================================================================
@tool
def git_branch_list(repo_path: str = "") -> str:
    """
    列出所有本地分支（git branch）。
    当前分支会用 * 标记。

    Args:
        repo_path: 仓库路径，默认当前目录

    Returns:
        str: 分支列表
    """
    target = os.path.abspath(repo_path) if repo_path else SAFE_BASE_DIR
    if not _safe_path_check(target):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    return _run_git(["branch"], repo_path=target)
