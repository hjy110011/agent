"""
=====================================================================
 📊 数据格式处理工具集
 包含：data_format_tool, file_backup_tool, code_format_tool
=====================================================================
"""

import os
import sys
import json
import csv
import io
import ast
import time
import difflib
import subprocess
import tempfile
from typing import Optional

from langchain_core.tools import tool

from core.config import SAFE_BASE_DIR, BACKUP_DIR, logger
from core.utils import _safe_path_check, _format_size
from core.hitl_approval import request_human_approval


# =====================================================================
# 📊 data_format_tool
# =====================================================================

def _parse_csv_line(line: str) -> list:
    """解析单行 CSV"""
    reader = csv.reader(io.StringIO(line))
    return next(reader)


def _json_query(data, query_path: str):
    """按点号路径查询 JSON 数据"""
    if not query_path:
        return data
    parts = query_path.split('.')
    current = data
    for part in parts:
        if '[' in part and ']' in part:
            name, idx_str = part.split('[')
            idx = int(idx_str.rstrip(']'))
            if name:
                current = current[name][idx]
            else:
                current = current[idx]
        else:
            if isinstance(current, dict):
                current = current[part]
            else:
                return None
    return current


def _json_to_yaml(data, indent: int = 2) -> str:
    """JSON 转 YAML"""
    lines = []

    def _serialize(obj, depth=0):
        prefix = " " * (depth * indent)
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    _serialize(val, depth + 1)
                else:
                    if isinstance(val, str):
                        if '\n' in val:
                            lines.append(f"{prefix}{key}: |")
                            for line in val.split('\n'):
                                lines.append(f"{prefix}{' ' * indent}{line}")
                        else:
                            lines.append(f"{prefix}{key}: {val}")
                    elif val is None:
                        lines.append(f"{prefix}{key}: null")
                    elif isinstance(val, bool):
                        lines.append(f"{prefix}{key}: {str(val).lower()}")
                    else:
                        lines.append(f"{prefix}{key}: {val}")
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    _serialize(item, depth + 1)
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{obj}")

    _serialize(data)
    return '\n'.join(lines)


def _json_to_csv(data) -> str:
    """JSON 转 CSV"""
    output = io.StringIO()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    elif isinstance(data, dict):
        writer = csv.writer(output)
        for key, val in data.items():
            writer.writerow([key, val])
    return output.getvalue()


def _csv_query(data: str, query_path: str = ""):
    """CSV 查询"""
    reader = csv.DictReader(io.StringIO(data))
    rows = list(reader)
    if not query_path:
        return rows
    # 按列名查询
    if query_path in (reader.fieldnames or []):
        return [row[query_path] for row in rows]
    # 按行号查询
    try:
        idx = int(query_path)
        if 0 <= idx < len(rows):
            return rows[idx]
    except ValueError:
        pass
    return rows


@tool
def data_format_tool(
    action: str = "parse",
    data_format: str = "json",
    input_data: str = "",
    query_path: str = "",
    indent: int = 2,
    file_path: str = ""
) -> str:
    """
    一站式数据格式处理工具，支持 JSON/CSV/YAML 三种格式。

    功能：
    - parse: 解析并验证数据格式，返回格式化后的内容
    - validate: 仅验证数据格式是否正确
    - format: 美化格式化数据（缩进控制）
    - query: 按路径查询/提取数据（JSON 支持点号路径如 "data.items[0].name"）
    - convert: 格式互转（JSON ↔ CSV, JSON ↔ YAML）

    Args:
        action: 操作类型（parse/validate/format/query/convert），默认parse
        data_format: 数据格式（json/csv/yaml），默认json
        input_data: 要处理的原始数据字符串
        query_path: 查询路径（仅 query 操作使用）
        indent: 格式化缩进空格数，默认2
        file_path: 从文件读取数据（可选）

    Returns:
        str: 处理结果
    """
    valid_actions = ["parse", "validate", "format", "query", "convert"]
    valid_formats = ["json", "csv", "yaml"]

    if action not in valid_actions:
        return f"无效的 action: '{action}'。可选值: {', '.join(valid_actions)}"
    if data_format not in valid_formats:
        return f"无效的 data_format: '{data_format}'。可选值: {', '.join(valid_formats)}"

    # 从文件读取
    source = input_data
    source_desc = "直接输入"
    if file_path:
        abs_path = os.path.abspath(file_path)
        if not _safe_path_check(abs_path):
            return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"
        if not os.path.exists(abs_path):
            return f"文件不存在: {abs_path}"
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            source_desc = f"文件: {abs_path}"
        except Exception as e:
            return f"读取文件失败: {e}"

    if not source or not source.strip():
        return "数据内容为空！请提供 input_data 或 file_path。"

    result_parts = [
        f"数据格式处理报告",
        f"   操作: {action} | 格式: {data_format} | 来源: {source_desc}",
        "=" * 60,
    ]

    # ---------------------------------------------------------------
    # parse: 解析并验证
    # ---------------------------------------------------------------
    if action == "parse":
        try:
            if data_format == "json":
                parsed = json.loads(source)
                formatted = json.dumps(parsed, ensure_ascii=False, indent=indent)
                result_parts.append("JSON 解析成功！")
                result_parts.append(formatted)
            elif data_format == "csv":
                reader = csv.DictReader(io.StringIO(source))
                rows = list(reader)
                result_parts.append(f"CSV 解析成功！共 {len(rows)} 行数据")
                result_parts.append(f"列名: {', '.join(reader.fieldnames or [])}")
                for i, row in enumerate(rows[:10]):
                    result_parts.append(f"  行{i}: {row}")
                if len(rows) > 10:
                    result_parts.append(f"  ... 还有 {len(rows) - 10} 行")
            elif data_format == "yaml":
                try:
                    import yaml
                    parsed = yaml.safe_load(source)
                    formatted = yaml.dump(parsed, default_flow_style=False,
                                          allow_unicode=True, indent=indent)
                    result_parts.append("YAML 解析成功！")
                    result_parts.append(formatted)
                except ImportError:
                    result_parts.append("需要安装 PyYAML: pip install pyyaml")
                    result_parts.append(f"原始内容:\n{source}")
        except Exception as e:
            return f"解析失败: {e}"

    # ---------------------------------------------------------------
    # validate: 仅验证
    # ---------------------------------------------------------------
    elif action == "validate":
        try:
            if data_format == "json":
                json.loads(source)
                result_parts.append("✅ JSON 格式正确！")
            elif data_format == "csv":
                reader = csv.DictReader(io.StringIO(source))
                rows = list(reader)
                result_parts.append(f"✅ CSV 格式正确！共 {len(rows)} 行")
            elif data_format == "yaml":
                try:
                    import yaml
                    yaml.safe_load(source)
                    result_parts.append("✅ YAML 格式正确！")
                except ImportError:
                    result_parts.append("需要安装 PyYAML 才能验证 YAML 格式")
        except Exception as e:
            return f"❌ 格式验证失败: {e}"

    # ---------------------------------------------------------------
    # format: 美化格式化
    # ---------------------------------------------------------------
    elif action == "format":
        try:
            if data_format == "json":
                parsed = json.loads(source)
                formatted = json.dumps(parsed, ensure_ascii=False, indent=indent)
                result_parts.append(f"JSON 格式化完成 (缩进: {indent})")
                result_parts.append(formatted)
            elif data_format == "csv":
                reader = csv.reader(io.StringIO(source))
                output = io.StringIO()
                writer = csv.writer(output)
                for row in reader:
                    writer.writerow(row)
                result_parts.append("CSV 格式化完成")
                result_parts.append(output.getvalue())
            elif data_format == "yaml":
                try:
                    import yaml
                    parsed = yaml.safe_load(source)
                    formatted = yaml.dump(parsed, default_flow_style=False,
                                          allow_unicode=True, indent=indent)
                    result_parts.append(f"YAML 格式化完成 (缩进: {indent})")
                    result_parts.append(formatted)
                except ImportError:
                    result_parts.append("需要安装 PyYAML")
        except Exception as e:
            return f"格式化失败: {e}"

    # ---------------------------------------------------------------
    # query: 按路径查询
    # ---------------------------------------------------------------
    elif action == "query":
        if not query_path:
            return "query 操作需要提供 query_path 参数！"
        try:
            if data_format == "json":
                parsed = json.loads(source)
                result = _json_query(parsed, query_path)
                formatted = json.dumps(result, ensure_ascii=False, indent=indent)
                result_parts.append(f"JSON 查询: {query_path}")
                result_parts.append(formatted)
            elif data_format == "csv":
                result = _csv_query(source, query_path)
                result_parts.append(f"CSV 查询: {query_path}")
                result_parts.append(str(result))
            elif data_format == "yaml":
                try:
                    import yaml
                    parsed = yaml.safe_load(source)
                    result = _json_query(parsed, query_path)
                    formatted = yaml.dump(result, default_flow_style=False, allow_unicode=True)
                    result_parts.append(f"YAML 查询: {query_path}")
                    result_parts.append(formatted)
                except ImportError:
                    result_parts.append("需要安装 PyYAML")
        except Exception as e:
            return f"查询失败: {e}"

    # ---------------------------------------------------------------
    # convert: 格式互转
    # ---------------------------------------------------------------
    elif action == "convert":
        target_format = query_path if query_path else "yaml"
        if target_format not in valid_formats:
            return f"无效的目标格式: '{target_format}'。可选值: {', '.join(valid_formats)}"
        if target_format == data_format:
            return f"源格式和目标格式相同 ({data_format})，无需转换。"

        try:
            # 先解析源格式
            if data_format == "json":
                parsed = json.loads(source)
            elif data_format == "csv":
                reader = csv.DictReader(io.StringIO(source))
                parsed = list(reader)
            elif data_format == "yaml":
                try:
                    import yaml
                    parsed = yaml.safe_load(source)
                except ImportError:
                    return "需要安装 PyYAML 才能处理 YAML 格式"

            # 再转换为目标格式
            if target_format == "json":
                result = json.dumps(parsed, ensure_ascii=False, indent=indent)
                result_parts.append(f"转换: {data_format.upper()} → JSON")
                result_parts.append(result)
            elif target_format == "csv":
                result = _json_to_csv(parsed)
                result_parts.append(f"转换: {data_format.upper()} → CSV")
                result_parts.append(result)
            elif target_format == "yaml":
                result = _json_to_yaml(parsed, indent)
                result_parts.append(f"转换: {data_format.upper()} → YAML")
                result_parts.append(result)
        except Exception as e:
            return f"转换失败: {e}"

    return "\n".join(result_parts)


# =====================================================================
# 📂 file_backup_tool
# =====================================================================
@tool
def file_backup_tool(
    action: str = "backup",
    file_path: str = "",
    version: str = "",
    output_path: str = ""
) -> str:
    """
    文件备份与恢复工具。支持创建备份、列出版本、恢复文件、对比差异。

    功能：
    - backup: 创建文件备份（带时间戳），自动保留历史版本
    - list: 列出指定文件的所有备份版本
    - restore: 恢复到指定版本
    - diff: 对比当前文件与指定版本的差异

    Args:
        action: 操作类型（backup/list/restore/diff），默认backup
        file_path: 要操作的文件路径（必填）
        version: 版本标识（restore/diff 操作时必填）
        output_path: 恢复时指定输出路径（可选）

    Returns:
        str: 操作结果
    """
    if not file_path:
        return "请提供 file_path 参数！"

    target_path = os.path.abspath(file_path)
    if not _safe_path_check(target_path):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    if action == "backup":
        if not os.path.exists(target_path):
            return f"文件不存在: {target_path}"

        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        bak_name = f"backup_{timestamp}.bak"
        bak_path = os.path.join(BACKUP_DIR, bak_name)

        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f_src:
                content = f_src.read()
            with open(bak_path, 'w', encoding='utf-8') as f_bak:
                f_bak.write(content)

            file_size = os.path.getsize(bak_path)
            size_str = _format_size(file_size)

            return (
                f"备份成功！\n"
                f"   文件: {target_path}\n"
                f"   备份: {bak_path}\n"
                f"   版本: {timestamp}\n"
                f"   大小: {size_str}"
            )
        except Exception as e:
            return f"备份失败: {e}"

    elif action == "list":
        os.makedirs(BACKUP_DIR, exist_ok=True)
        all_backups = sorted([
            f for f in os.listdir(BACKUP_DIR) if f.endswith('.bak')
        ])

        if not all_backups:
            return f"文件 '{target_path}' 没有备份版本。"

        result_parts = [
            f"备份版本列表: {target_path}",
            "=" * 60,
        ]
        for i, bak in enumerate(all_backups):
            bak_path = os.path.join(BACKUP_DIR, bak)
            try:
                file_size = os.path.getsize(bak_path)
                size_str = _format_size(file_size)
                ts = bak.replace("backup_", "").replace(".bak", "")
                time_str = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
                result_parts.append(f"  [{i}] 版本: {ts}  |  大小: {size_str}  |  修改时间: {time_str}")
            except Exception:
                result_parts.append(f"  [{i}] 版本: {bak}  |  (无法读取)")

        result_parts.append(f"\n共 {len(all_backups)} 个备份版本")
        return "\n".join(result_parts)

    elif action == "restore":
        # ⚠️ 高危操作：文件恢复会覆盖目标文件，需要人工审批
        approval = request_human_approval(
            "文件恢复(file_backup_tool.restore)",
            {"description": f"将备份版本恢复到: {target_path}"}
        )
        if not approval:
            return "❌ 操作已取消：未获得人工审批。"

        if not version:
            return "restore 操作需要提供 version 参数！请使用 list 查看可用版本。"

        os.makedirs(BACKUP_DIR, exist_ok=True)
        all_backups = sorted([
            f for f in os.listdir(BACKUP_DIR) if f.endswith('.bak')
        ])

        if not all_backups:
            return f"文件 '{target_path}' 没有可恢复的备份。"

        target_backup = None
        try:
            idx = int(version)
            if 0 <= idx < len(all_backups):
                target_backup = all_backups[idx]
        except ValueError:
            for bak in all_backups:
                if version in bak:
                    target_backup = bak
                    break

        if not target_backup:
            versions_str = "\n".join(
                f"  [{i}] {bak.replace('backup_', '').replace('.bak', '')}"
                for i, bak in enumerate(all_backups[:20])
            )
            return (
                f"未找到版本 '{version}'。\n"
                f"可用版本 (前20个):\n{versions_str}"
            )

        backup_path = os.path.join(BACKUP_DIR, target_backup)
        try:
            with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f_src:
                backup_content = f_src.read()

            restore_path = output_path if output_path else target_path
            restore_path = os.path.abspath(restore_path)

            if not _safe_path_check(restore_path):
                return f"安全拦截：恢复目标路径越权！仅限 {SAFE_BASE_DIR} 及子目录。"

            os.makedirs(os.path.dirname(restore_path) or '.', exist_ok=True)
            with open(restore_path, 'w', encoding='utf-8') as f_dst:
                f_dst.write(backup_content)

            file_size = os.path.getsize(restore_path)
            size_str = _format_size(file_size)
            ts = target_backup.replace("backup_", "").replace(".bak", "")

            return (
                f"恢复成功！\n"
                f"   恢复自版本: {ts}\n"
                f"   恢复至: {restore_path}\n"
                f"   大小: {size_str}"
            )
        except Exception as e:
            return f"恢复失败: {e}"

    elif action == "diff":
        if not version:
            return "diff 操作需要提供 version 参数！请使用 list 查看可用版本。"

        os.makedirs(BACKUP_DIR, exist_ok=True)
        all_backups = sorted([
            f for f in os.listdir(BACKUP_DIR) if f.endswith('.bak')
        ])

        if not all_backups:
            return f"文件 '{target_path}' 没有备份可对比。"

        target_backup = None
        try:
            idx = int(version)
            if 0 <= idx < len(all_backups):
                target_backup = all_backups[idx]
        except ValueError:
            for bak in all_backups:
                if version in bak:
                    target_backup = bak
                    break

        if not target_backup:
            return f"未找到版本 '{version}'。"

        backup_path = os.path.join(BACKUP_DIR, target_backup)
        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_lines = f.readlines()
            with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
                backup_lines = f.readlines()

            ts = target_backup.replace("backup_", "").replace(".bak", "")
            result_parts = [
                f"文件差异对比: {target_path}",
                f"   对比版本: {ts} (备份) vs 当前文件",
                "=" * 60,
            ]

            diff = list(difflib.unified_diff(
                backup_lines, current_lines,
                fromfile=f"备份版本 ({ts})",
                tofile="当前文件",
                lineterm=''
            ))

            if not diff:
                result_parts.append("文件无差异，与备份版本完全一致。")
            else:
                added = sum(1 for line in diff if line.startswith(
                    '+') and not line.startswith('+++'))
                removed = sum(1 for line in diff if line.startswith('-')
                              and not line.startswith('---'))
                result_parts.append(f"变更统计: +{added} 行 / -{removed} 行")
                result_parts.append("-" * 60)

                MAX_DIFF_LINES = 100
                for line in diff[:MAX_DIFF_LINES]:
                    result_parts.append(line)
                if len(diff) > MAX_DIFF_LINES:
                    result_parts.append(f"\n... 还有 {len(diff) - MAX_DIFF_LINES} 行差异未显示")

            return "\n".join(result_parts)
        except Exception as e:
            return f"对比失败: {e}"

    return "未知错误。"


# =====================================================================
# ✨ code_format_tool
# =====================================================================
@tool
def code_format_tool(
    action: str = "format",
    file_path: str = "",
    code_text: str = "",
    line_length: int = 100,
    indent_width: int = 4
) -> str:
    """
    代码格式化与质量检查工具。支持 Python 代码自动格式化、flake8 质量检查、代码指标统计。

    功能：
    - format: 使用 autopep8 自动格式化 Python 代码（可配置行长度、缩进）
    - check: 使用 flake8 进行代码质量检查（显示错误行号、类别、描述）
    - stats: 统计代码指标（总行数、代码行、注释行、空行、函数数、类数、圈复杂度）

    Args:
        action: 操作类型（format/check/stats），默认format
        file_path: 要操作的 Python 文件路径
        code_text: 要处理的代码文本
        line_length: 格式化时的最大行长度，默认100
        indent_width: 缩进空格数，默认4

    Returns:
        str: 处理结果
    """
    valid_actions = ["format", "check", "stats"]
    if action not in valid_actions:
        return f"无效的 action: '{action}'。可选值: {', '.join(valid_actions)}"

    source_code = code_text
    source_desc = "直接输入"
    if file_path:
        abs_path = os.path.abspath(file_path)
        if not _safe_path_check(abs_path):
            return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"
        if not os.path.exists(abs_path):
            return f"文件不存在: {abs_path}"
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            source_desc = f"文件: {abs_path}"
        except Exception as e:
            return f"读取文件失败: {e}"

    if not source_code or not source_code.strip():
        return "代码内容为空！请提供 file_path 或 code_text。"

    result_parts = [
        "代码格式化与质量检查报告",
        f"   操作: {action} | 来源: {source_desc}",
        "=" * 60,
    ]

    # ---------------------------------------------------------------
    # format: 自动格式化
    # ---------------------------------------------------------------
    if action == "format":
        try:
            import autopep8
        except ImportError:
            result_parts.append("autopep8 未安装，尝试自动安装...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "autopep8",
                     "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                    capture_output=True, timeout=60
                )
                import autopep8
                result_parts.append("autopep8 安装成功！")
            except Exception:
                result_parts.append("autopep8 安装失败，使用内置基础格式化...")
                try:
                    tree = ast.parse(source_code)
                    formatted = ast.unparse(tree)
                    result_parts.append("基础格式化完成（使用 ast.unparse）")
                except SyntaxError as e:
                    return f"代码语法错误，无法格式化: {e}"

                if file_path:
                    # ⚠️ 高危操作：格式化会覆盖源文件，需要人工审批
                    approval = request_human_approval(
                        "代码格式化(code_format_tool.format)",
                        {"description": f"将基础格式化后的代码写入: {abs_path}"}
                    )
                    if not approval:
                        result_parts.append("❌ 操作已取消：未获得人工审批，文件未更新。")
                    else:
                        try:
                            with open(abs_path, 'w', encoding='utf-8') as f:
                                f.write(formatted)
                            result_parts.append(f"已写入文件: {abs_path}")
                        except Exception as e:
                            return f"写入文件失败: {e}"
                result_parts.append("-" * 60)
                result_parts.append(formatted)
                return "\n".join(result_parts)

        try:
            formatted = autopep8.fix_code(
                source_code,
                options={
                    'max_line_length': line_length,
                    'indent_size': indent_width,
                }
            )

            changes = (source_code != formatted)
            if changes:
                orig_lines = source_code.split('\n')
                new_lines = formatted.split('\n')
                changed_lines = sum(1 for a, b in zip(orig_lines, new_lines) if a != b)
                result_parts.append("格式化完成！")
                result_parts.append(f"   行长度限制: {line_length}")
                result_parts.append(f"   缩进宽度: {indent_width}")
                result_parts.append(f"   变更行数: {changed_lines}/{len(orig_lines)} 行")
            else:
                result_parts.append("代码已符合规范，无需修改。")

            if file_path and changes:
                # ⚠️ 高危操作：格式化会覆盖源文件，需要人工审批
                approval = request_human_approval(
                    "代码格式化(code_format_tool.format)",
                    {"description": f"将格式化后的代码写入: {abs_path}"}
                )
                if not approval:
                    result_parts.append("❌ 操作已取消：未获得人工审批，文件未更新。")
                else:
                    try:
                        with open(abs_path, 'w', encoding='utf-8') as f:
                            f.write(formatted)
                        result_parts.append(f"已更新文件: {abs_path}")
                    except Exception as e:
                        return f"写入文件失败: {e}"

            result_parts.append("-" * 60)
            result_parts.append(formatted)
            return "\n".join(result_parts)

        except SyntaxError as e:
            return f"代码语法错误，无法格式化: {e}"
        except Exception as e:
            return f"格式化失败: {e}"

    # ---------------------------------------------------------------
    # check: flake8 质量检查
    # ---------------------------------------------------------------
    elif action == "check":
        try:
            ast.parse(source_code)
            result_parts.append("ast.parse() 语法检查通过")
        except SyntaxError as e:
            return f"语法错误: {e}"

        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
                f.write(source_code)
                tmp_file = f.name

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "flake8", tmp_file,
                     "--max-line-length", str(line_length)],
                    capture_output=True, timeout=30, text=True
                )
                flake8_output = proc.stdout.strip() or proc.stderr.strip()
            except Exception:
                flake8_output = ""

            if not flake8_output:
                result_parts.append("flake8 检查通过，无代码规范问题！")
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

                result_parts.append(f"\n共发现 {error_count} 个问题")
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
            return f"flake8 检查失败: {e}"
        finally:
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.unlink(tmp_file)
                except Exception:
                    pass

        return "\n".join(result_parts)

    # ---------------------------------------------------------------
    # stats: 代码指标统计
    # ---------------------------------------------------------------
    elif action == "stats":
        lines = source_code.split('\n')
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        docstring_lines = 0
        in_docstring = False

        try:
            tree = ast.parse(source_code)
            func_count = sum(1 for node in ast.walk(tree)
                             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
            class_count = sum(1 for node in ast.walk(tree)
                              if isinstance(node, ast.ClassDef))
            complexity = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                     ast.ExceptHandler, ast.Assert)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1 if hasattr(node, 'values') else 0
        except SyntaxError:
            func_count = 0
            class_count = 0
            complexity = 0

        for line in lines:
            stripped = line.strip()
            if in_docstring:
                docstring_lines += 1
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = False
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_lines += 1
                if stripped.count('"""') == 1 and stripped.count("'''") == 1:
                    in_docstring = True
                continue
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1

        result_parts.append("代码指标统计")
        result_parts.append("-" * 60)
        result_parts.append(f"  总行数:       {total_lines:>6}")
        if total_lines > 0:
            result_parts.append(
                f"  代码行:       {code_lines:>6}  ({code_lines/total_lines*100:.1f}%)")
            result_parts.append(
                f"  注释行:       {comment_lines:>6}  ({comment_lines/total_lines*100:.1f}%)")
            result_parts.append(
                f"  文档字符串行: {docstring_lines:>6}  ({docstring_lines/total_lines*100:.1f}%)")
            result_parts.append(
                f"  空行:         {blank_lines:>6}  ({blank_lines/total_lines*100:.1f}%)")
        result_parts.append(f"  函数数:       {func_count:>6}")
        result_parts.append(f"  类数:         {class_count:>6}")
        result_parts.append(f"  圈复杂度:     {complexity:>6}")
        result_parts.append("-" * 60)

        score = 100
        if total_lines > 0:
            comment_ratio = (comment_lines + docstring_lines) / total_lines
            if comment_ratio < 0.05:
                score -= 15
            elif comment_ratio < 0.1:
                score -= 5
            if blank_lines / total_lines < 0.05:
                score -= 10
            if func_count > 0 and complexity / func_count > 5:
                score -= 10
            elif func_count > 0 and complexity / func_count > 3:
                score -= 5

        score = max(0, min(100, score))
        if score >= 90:
            grade = "优秀"
        elif score >= 75:
            grade = "良好"
        elif score >= 60:
            grade = "一般"
        else:
            grade = "需改进"
        result_parts.append(f"  代码质量评分: {score}/100 {grade}")

        return "\n".join(result_parts)

    return "未知错误。"
