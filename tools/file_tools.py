"""
=====================================================================
 📂 文件操作工具集
 包含：read_local_file, read_file_by_lines, write_local_file,
       run_terminal_command, list_directory_tree, pip_install,
       check_python_syntax, search_code_ast, grep_search
=====================================================================
"""

import os
import sys
import ast
import json
import time
import chardet
import subprocess
from typing import Optional
from pathlib import Path

from langchain_core.tools import tool

from core.config import (
    SAFE_BASE_DIR, DANGEROUS_COMMANDS, MAX_OUTPUT_LENGTH,
    SEARCH_TIMEOUT, PIP_PYTHON_EXE, PIP_INDEX_URL, PIP_MAX_RETRIES,
    logger
)
from core.utils import (
    _truncate_output, _safe_path_check, _decode_terminal_bytes,
    _format_size, _TimeoutError, _execute_with_timeout
)


# =====================================================================
# 🔍 编码检测
# =====================================================================
def _detect_file_encoding(file_path: str) -> str:
    """
    检测文件编码。

    使用 chardet 库自动检测文件编码，支持 UTF-8/GBK/GB2312/GB18030 等。
    如果检测失败，回退到 'utf-8'。

    Args:
        file_path: 文件路径

    Returns:
        str: 检测到的编码名称
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        encoding = encoding.lower().replace('-', '')
        if encoding in ['utf8', 'utf-8', 'ascii']:
            return 'utf-8'
        if encoding in ['gb2312', 'gbk', 'gb18030', 'gb2312']:
            return 'gbk'
        return 'utf-8'
    except Exception:
        return 'utf-8'


# =====================================================================
# 📖 read_local_file
# =====================================================================
@tool
def read_local_file(file_path: str) -> str:
    """
    读取本地文件全文。

    自动检测编码（UTF-8/GBK/GB2312/GB18030等），返回文件信息预览。
    注意：如果文件超过 8000 字符会被截断。大文件请使用 read_file_by_lines。

    Args:
        file_path: 要读取的文件路径

    Returns:
        str: 文件内容及信息预览
    """
    abs_path = os.path.abspath(file_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权读取！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"文件不存在: {abs_path}"

    try:
        file_size = os.path.getsize(abs_path)
        size_str = _format_size(file_size)

        if file_size > 500 * 1024:
            return (
                f"文件过大 ({size_str})，建议使用 read_file_by_lines 按行读取。\n"
                f"文件路径: {abs_path}"
            )

        encoding = _detect_file_encoding(abs_path)

        with open(abs_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

        lines = content.split('\n')
        line_count = len(lines)

        MAX_CHARS = 8000
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS] + f"\n\n... [内容过长，已截断至 {MAX_CHARS} 字符]"

        return (
            f"文件: {abs_path}\n"
            f"大小: {size_str}  |  行数: {line_count}  |  编码: {encoding}\n"
            f"{'=' * 60}\n"
            f"{content}"
        )
    except Exception as e:
        return f"读取失败: {e}"


# =====================================================================
# 📖 read_file_by_lines
# =====================================================================
@tool
def read_file_by_lines(
    file_path: str,
    start_line: int = 1,
    end_line: int = 100
) -> str:
    """
    专读大文件，按行号范围读取。

    自动检测编码，智能行号校验，底部有"下一页"导航提示。

    Args:
        file_path: 文件路径
        start_line: 起始行号（从1开始），默认1
        end_line: 结束行号（包含），默认100

    Returns:
        str: 指定行范围的内容及文件信息
    """
    abs_path = os.path.abspath(file_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权读取！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"文件不存在: {abs_path}"

    try:
        file_size = os.path.getsize(abs_path)
        size_str = _format_size(file_size)
        encoding = _detect_file_encoding(abs_path)

        with open(abs_path, 'r', encoding=encoding, errors='replace') as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)

        # 智能行号校验
        if start_line < 1:
            start_line = 1
        if end_line > total_lines:
            end_line = total_lines
        if start_line > total_lines:
            return f"起始行号 {start_line} 超出文件总行数 {total_lines}。"

        if end_line - start_line > 500:
            return (
                f"请求行数过多 ({end_line - start_line + 1})，建议缩小范围（最多500行）。\n"
                f"文件总行数: {total_lines}"
            )

        selected = all_lines[start_line - 1:end_line]
        content = ''.join(selected).rstrip('\n')

        # 导航提示
        nav_parts = []
        if end_line < total_lines:
            nav_parts.append(f"下一页: read_file_by_lines(start_line={end_line + 1}, end_line={min(end_line + 100, total_lines)})")
        nav_parts.append(f"共 {total_lines} 行，当前显示 {start_line}-{end_line} 行")

        return (
            f"文件: {abs_path}\n"
            f"大小: {size_str}  |  总行数: {total_lines}  |  编码: {encoding}\n"
            f"读取范围: 第 {start_line} - {end_line} 行 (共 {end_line - start_line + 1} 行)\n"
            f"{'=' * 60}\n"
            f"{content}\n"
            f"{'=' * 60}\n"
            f"{'  |  '.join(nav_parts)}"
        )
    except Exception as e:
        return f"读取失败: {e}"


# =====================================================================
# ✍️ write_local_file
# =====================================================================
@tool
def write_local_file(file_path: str, content: str) -> str:
    """
    修改或创建文件。会自动新建目标文件夹。

    安全保护：
    - 禁止越权写入（仅限 SAFE_BASE_DIR 及子目录）
    - 自动备份原文件（.bak）
    - 超大文件保护（超过 50MB 拒绝写入）
    - 自动创建父目录

    Args:
        file_path: 要写入的文件路径
        content: 要写入的文件内容

    Returns:
        str: 写入结果描述
    """
    abs_path = os.path.abspath(file_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权写入！仅限 {SAFE_BASE_DIR} 及子目录。"

    # 超大文件保护
    if len(content) > 50 * 1024 * 1024:
        return "拒绝写入：内容超过 50MB 限制。"

    try:
        os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)

        # 自动备份原文件
        if os.path.exists(abs_path):
            bak_path = abs_path + '.bak'
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f_src:
                    bak_content = f_src.read()
                with open(bak_path, 'w', encoding='utf-8') as f_bak:
                    f_bak.write(bak_content)
            except Exception:
                pass

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = os.path.getsize(abs_path)
        size_str = _format_size(file_size)
        line_count = content.count('\n') + 1

        return (
            f"成功写入文件 {abs_path}\n"
            f"大小: {size_str}  |  行数: {line_count}"
        )
    except Exception as e:
        return f"写入失败: {e}"


# =====================================================================
# 💻 run_terminal_command
# =====================================================================
@tool
def run_terminal_command(command: str) -> str:
    """
    执行终端命令。返回标准输出和报错。

    安全保护：
    - 高危命令黑名单拦截
    - 超时保护（默认 30 秒）
    - 输出截断（默认 20000 字符）
    - 智能编码回退，绝不乱码

    Args:
        command: 要执行的终端命令

    Returns:
        str: 命令执行结果
    """
    # 高危命令检查
    import re
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return (
                f"安全拦截：高危命令被禁止！\n"
                f"匹配规则: {pattern}\n"
                f"命令: {command[:200]}"
            )

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=30,
        )

        stdout = _decode_terminal_bytes(proc.stdout)
        stderr = _decode_terminal_bytes(proc.stderr)

        result_parts = []
        if stdout:
            result_parts.append(stdout)
        if stderr:
            result_parts.append(f"[STDERR]\n{stderr}")

        result = '\n'.join(result_parts) if result_parts else "(无输出)"
        result = _truncate_output(result)

        return (
            f"命令: {command}\n"
            f"返回码: {proc.returncode}\n"
            f"{'=' * 60}\n"
            f"{result}"
        )
    except subprocess.TimeoutExpired:
        return f"命令执行超时 (30秒): {command[:200]}"
    except Exception as e:
        return f"命令执行失败: {e}"


# =====================================================================
# 📂 list_directory_tree
# =====================================================================
@tool
def list_directory_tree(
    root_path: str = ".",
    max_depth: int = 3,
    show_files: bool = True,
    show_dirs: bool = True,
    pattern: str = ""
) -> str:
    """
    递归列出目录结构树。

    支持深度控制、文件/文件夹过滤、通配符模式匹配。

    Args:
        root_path: 根目录路径，默认当前目录
        max_depth: 最大递归深度，默认3
        show_files: 是否显示文件，默认True
        show_dirs: 是否显示文件夹，默认True
        pattern: 通配符模式过滤（如 "*.py"），默认空表示全部

    Returns:
        str: 目录结构树文本
    """
    abs_path = os.path.abspath(root_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权访问！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"目录不存在: {abs_path}"
    if not os.path.isdir(abs_path):
        return f"路径不是目录: {abs_path}"

    import fnmatch

    lines = [f"目录结构: {abs_path}", f"最大深度: {max_depth}", "=" * 60]

    def _walk(dir_path, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
        except PermissionError:
            lines.append("  " * depth + "  [权限不足]")
            return

        for entry in entries:
            full_path = os.path.join(dir_path, entry)
            is_dir = os.path.isdir(full_path)

            # 过滤
            if is_dir and not show_dirs:
                continue
            if not is_dir and not show_files:
                continue
            if pattern and not is_dir:
                if not fnmatch.fnmatch(entry, pattern):
                    continue

            prefix = "  " * depth
            if is_dir:
                lines.append(f"{prefix}📁 {entry}/")
                _walk(full_path, depth + 1)
            else:
                try:
                    size = os.path.getsize(full_path)
                    size_str = _format_size(size)
                    lines.append(f"{prefix}📄 {entry}  ({size_str})")
                except Exception:
                    lines.append(f"{prefix}📄 {entry}")

    _walk(abs_path, 0)
    return "\n".join(lines)


# =====================================================================
# 🔧 pip_install
# =====================================================================
@tool
def pip_install(package_name: str, upgrade: bool = False) -> str:
    """
    专属依赖安装工具。

    强制调用指定 Python 环境的 pip，内置清华源镜像和自动重试机制。

    Args:
        package_name: 要安装的包名
        upgrade: 是否升级，默认False

    Returns:
        str: 安装结果
    """
    cmd = [PIP_PYTHON_EXE, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.extend([package_name, "--index-url", PIP_INDEX_URL])

    last_error = ""
    for attempt in range(1, PIP_MAX_RETRIES + 1):
        try:
            proc = subprocess.run(
                cmd, capture_output=True, timeout=120, text=True
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""

            if proc.returncode == 0:
                return (
                    f"安装成功: {package_name}\n"
                    f"{stdout[:1000]}"
                )
            else:
                last_error = stderr[:500] or stdout[:500]
                if attempt < PIP_MAX_RETRIES:
                    time.sleep(2)
        except subprocess.TimeoutExpired:
            last_error = "安装超时 (120秒)"
            if attempt < PIP_MAX_RETRIES:
                time.sleep(3)
        except Exception as e:
            last_error = str(e)
            if attempt < PIP_MAX_RETRIES:
                time.sleep(2)

    return f"安装失败 ({PIP_MAX_RETRIES}次重试): {last_error}"


# =====================================================================
# ✅ check_python_syntax
# =====================================================================
@tool
def check_python_syntax(file_path: str = "") -> str:
    """
    使用 ast.parse() + flake8 双重检查 Python 语法。

    Args:
        file_path: 要检查的 Python 文件路径

    Returns:
        str: 语法检查结果
    """
    if not file_path:
        return "请提供 file_path 参数。"

    abs_path = os.path.abspath(file_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"文件不存在: {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

    result_parts = [
        f"正在检查 Python 语法: {abs_path}",
        "=" * 60,
    ]

    # 第一阶段：ast.parse() 静态语法检查
    result_parts.append("")
    result_parts.append("【第一阶段】ast.parse() 静态语法检查")
    try:
        tree = ast.parse(source_code)
        func_count = sum(1 for node in ast.walk(tree)
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        class_count = sum(1 for node in ast.walk(tree)
                          if isinstance(node, ast.ClassDef))
        result_parts.append("   语法正确")
        result_parts.append(f"   统计: {len(source_code.split(chr(10)))} 行, {class_count} 个类, {func_count} 个函数")
    except SyntaxError as e:
        result_parts.append(f"   语法错误: {e}")
        return "\n".join(result_parts)

    # 第二阶段：flake8 代码规范检查
    result_parts.append("")
    result_parts.append("【第二阶段】flake8 代码规范检查")

    import tempfile
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
            f.write(source_code)
            tmp_file = f.name

        proc = subprocess.run(
            [sys.executable, "-m", "flake8", tmp_file, "--max-line-length", "100"],
            capture_output=True, timeout=30, text=True
        )
        flake8_output = proc.stdout.strip() or proc.stderr.strip()

        if not flake8_output:
            result_parts.append("   代码规范检查通过！无任何警告")
        else:
            lines = flake8_output.split('\n')
            error_count = 0
            error_categories = {}
            for line in lines:
                if not line.strip():
                    continue
                error_count += 1
                parts = line.split(':')
                if len(parts) >= 4:
                    line_no = parts[1].strip() if len(parts) > 1 else "?"
                    col_no = parts[2].strip() if len(parts) > 2 else "?"
                    code_msg = ':'.join(parts[3:]).strip()
                    code = code_msg.split()[0] if code_msg else "?"
                    cat = code[0] if code else "?"
                    error_categories[cat] = error_categories.get(cat, 0) + 1
                    result_parts.append(f"  行 {line_no:>4}:{col_no:<3}  {code_msg}")

            result_parts.append(f"\n   发现 {error_count} 个代码规范问题")
            if error_categories:
                cat_desc = []
                for cat, cnt in sorted(error_categories.items()):
                    cat_name = {
                        'E': '错误(Error)', 'W': '警告(Warning)',
                        'F': '逻辑错误', 'C': '复杂度',
                        'N': '命名', 'D': '文档'
                    }.get(cat, f'类别{cat}')
                    cat_desc.append(f"{cat_name}: {cnt}")
                result_parts.append(f"   分类: {', '.join(cat_desc)}")

    except Exception as e:
        result_parts.append(f"   flake8 检查失败: {e}")
    finally:
        if tmp_file and os.path.exists(tmp_file):
            try:
                os.unlink(tmp_file)
            except Exception:
                pass

    return "\n".join(result_parts)


# =====================================================================
# 🔍 search_code_ast
# =====================================================================
@tool
def search_code_ast(
    file_path: str,
    search_type: str = "all",
    search_name: str = "",
    case_sensitive: bool = False
) -> str:
    """
    使用 Python ast 模块深度解析 Python 源码。

    支持搜索类定义、函数名、变量等。

    Args:
        file_path: 要解析的 Python 文件路径
        search_type: 搜索类型（all/class/function/variable/import），默认all
        search_name: 按名称过滤（空字符串表示全部）
        case_sensitive: 是否区分大小写，默认False

    Returns:
        str: AST 解析结果
    """
    abs_path = os.path.abspath(file_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"文件不存在: {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"语法错误，无法解析: {e}"

    result_parts = [
        f"AST 解析: {abs_path}",
        f"搜索类型: {search_type}  |  名称过滤: '{search_name or '(全部)'}'",
        "=" * 60,
    ]

    def _match_name(name):
        if not search_name:
            return True
        if case_sensitive:
            return search_name in name
        return search_name.lower() in name.lower()

    found = False

    for node in ast.walk(tree):
        # 类定义
        if search_type in ("all", "class") and isinstance(node, ast.ClassDef):
            if _match_name(node.name):
                bases = [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases]
                result_parts.append(f"  class {node.name}({', '.join(bases)})  [行{node.lineno}]")
                found = True

        # 函数定义
        elif search_type in ("all", "function") and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _match_name(node.name):
                decorators = [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                deco_str = f"  @{', @'.join(decorators)} " if decorators else "  "
                result_parts.append(f"{deco_str}def {node.name}()  [行{node.lineno}]")
                found = True

        # 变量/赋值
        elif search_type in ("all", "variable") and isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _match_name(target.id):
                    result_parts.append(f"  {target.id} = ...  [行{node.lineno}]")
                    found = True

        # import
        elif search_type in ("all", "import") and isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _match_name(alias.name):
                        result_parts.append(f"  import {alias.name}  [行{node.lineno}]")
                        found = True
            else:
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    if _match_name(full_name):
                        result_parts.append(f"  from {module} import {alias.name}  [行{node.lineno}]")
                        found = True

    if not found:
        result_parts.append(f"  未找到匹配的 {search_type} 定义。")

    return "\n".join(result_parts)


# =====================================================================
# 🔍 grep_search
# =====================================================================
def _run_grep_powershell(pattern: str, file_pattern: str, root_dir: str, max_results: int) -> str:
    """使用 PowerShell Select-String 进行搜索（Windows 环境）"""
    cmd = [
        "powershell", "-Command",
        f"Get-ChildItem -Recurse -Filter '{file_pattern}' "
        f"-Path '{root_dir}' | Select-String -Pattern '{pattern}' "
        f"| Select-Object -First {max_results} "
        f"| ForEach-Object {{ $_.Path + ':' + $_.LineNumber + ':' + $_.Line }}"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=SEARCH_TIMEOUT, text=True)
        return proc.stdout.strip() or proc.stderr.strip()
    except Exception:
        return ""


@tool
def grep_search(
    pattern: str,
    file_pattern: str = "*.py",
    root_dir: str = "",
    max_results: int = 50,
    context_lines: int = 0,
    case_sensitive: bool = False,
    regex_mode: bool = False
) -> str:
    """
    使用系统 grep/findstr 快速搜索文本。

    Args:
        pattern: 要搜索的文本模式
        file_pattern: 文件通配符模式，默认 "*.py"
        root_dir: 搜索根目录，默认当前目录
        max_results: 最大结果数，默认50
        context_lines: 上下文行数，默认0
        case_sensitive: 是否区分大小写，默认False
        regex_mode: 是否使用正则表达式，默认False

    Returns:
        str: 搜索结果
    """
    search_dir = os.path.abspath(root_dir) if root_dir else SAFE_BASE_DIR
    if not _safe_path_check(search_dir):
        return f"安全拦截：禁止越权搜索！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(search_dir):
        return f"目录不存在: {search_dir}"

    result_parts = [
        f"搜索模式: '{pattern}'",
        f"文件模式: {file_pattern}  |  目录: {search_dir}",
        "=" * 60,
    ]

    # Windows 使用 PowerShell
    if sys.platform == "win32":
        output = _run_grep_powershell(pattern, file_pattern, search_dir, max_results)
        if output:
            lines = output.split('\n')[:max_results]
            for line in lines:
                if line.strip():
                    result_parts.append(f"  {line}")
            result_parts.append(f"\n共 {len(lines)} 条结果")
        else:
            result_parts.append("  未找到匹配内容。")
        return "\n".join(result_parts)

    # Linux/Mac 使用 grep
    flags = "-rn"
    if not case_sensitive:
        flags += "i"
    if regex_mode:
        grep_pattern = pattern
    else:
        grep_pattern = pattern
        flags += "F"

    if context_lines > 0:
        flags += f" -C {context_lines}"

    cmd = f"grep {flags} -m {max_results} '{grep_pattern}' --include='{file_pattern}' '{search_dir}'"

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, timeout=SEARCH_TIMEOUT, text=True)
        output = proc.stdout.strip() or proc.stderr.strip()
        if output:
            lines = output.split('\n')[:max_results]
            for line in lines:
                if line.strip():
                    result_parts.append(f"  {line}")
            result_parts.append(f"\n共 {len(lines)} 条结果")
        else:
            result_parts.append("  未找到匹配内容。")
    except subprocess.TimeoutExpired:
        result_parts.append("搜索超时。")
    except Exception as e:
        result_parts.append(f"搜索失败: {e}")

    return "\n".join(result_parts)
