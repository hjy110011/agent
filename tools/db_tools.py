"""
=====================================================================
 🗄️ 数据库探查工具集
 包含：inspect_database（支持 SQLite 和 MySQL）
=====================================================================
"""

import os
import sys
import sqlite3
from typing import Optional

from langchain_core.tools import tool

from core.config import SAFE_BASE_DIR, logger
from core.utils import _safe_path_check


# =====================================================================
# SQLite 探查
# =====================================================================
def _inspect_sqlite(sqlite_path: str) -> str:
    """
    探查 SQLite 数据库。

    查出所有表名、表结构（列名、类型、约束）、行数。

    Args:
        sqlite_path: SQLite 数据库文件路径

    Returns:
        str: 数据库结构描述
    """
    abs_path = os.path.abspath(sqlite_path)
    if not _safe_path_check(abs_path):
        return f"安全拦截：禁止越权操作！仅限 {SAFE_BASE_DIR} 及子目录。"

    if not os.path.exists(abs_path):
        return f"数据库文件不存在: {abs_path}"

    try:
        conn = sqlite3.connect(abs_path)
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return f"数据库 '{abs_path}' 中没有任何表。"

        result_parts = [
            f"数据库: {abs_path}",
            f"共 {len(tables)} 个表",
            "=" * 60,
        ]

        for table_name in tables:
            result_parts.append(f"\n📋 表: {table_name}")

            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            result_parts.append(f"   列数: {len(columns)}")
            result_parts.append(f"   {'列名':<20} {'类型':<15} {'非空':<6} {'主键':<6} {'默认值':<15}")
            result_parts.append(f"   {'-'*62}")

            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                result_parts.append(
                    f"   {col_name:<20} {str(col_type):<15} "
                    f"{'YES' if not_null else '':<6} "
                    f"{'PK' if is_pk else '':<6} "
                    f"{str(default_val) if default_val else '':<15}"
                )

            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            row_count = cursor.fetchone()[0]
            result_parts.append(f"   行数: {row_count}")

        conn.close()
        return "\n".join(result_parts)

    except sqlite3.Error as e:
        return f"SQLite 错误: {e}"
    except Exception as e:
        return f"探查失败: {e}"


# =====================================================================
# MySQL 探查
# =====================================================================
def _inspect_mysql(host: str, database: str, user: str, password: str, port: int = 3306) -> str:
    """
    探查 MySQL 数据库。

    查出所有表名、表结构（列名、类型、约束）、行数。

    Args:
        host: MySQL 主机地址
        database: 数据库名
        user: 用户名
        password: 密码
        port: 端口号，默认3306

    Returns:
        str: 数据库结构描述
    """
    try:
        import pymysql
    except ImportError:
        return "需要安装 pymysql: pip install pymysql"

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            connect_timeout=10
        )
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return f"数据库 '{database}' 中没有任何表。"

        result_parts = [
            f"数据库: {database} @ {host}:{port}",
            f"共 {len(tables)} 个表",
            "=" * 60,
        ]

        for table_name in tables:
            result_parts.append(f"\n📋 表: {table_name}")

            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()

            result_parts.append(f"   列数: {len(columns)}")
            result_parts.append(f"   {'列名':<20} {'类型':<20} {'空':<6} {'键':<6} {'默认值':<15} {'额外':<15}")
            result_parts.append(f"   {'-'*82}")

            for col in columns:
                col_name, col_type, nullable, key, default_val, extra = col
                result_parts.append(
                    f"   {col_name:<20} {str(col_type):<20} "
                    f"{'YES' if nullable == 'YES' else 'NO':<6} "
                    f"{key if key else '':<6} "
                    f"{str(default_val) if default_val else 'NULL':<15} "
                    f"{extra if extra else '':<15}"
                )

            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            result_parts.append(f"   行数: {row_count}")

        conn.close()
        return "\n".join(result_parts)

    except Exception as e:
        return f"MySQL 连接失败: {e}"


# =====================================================================
# 🔍 inspect_database
# =====================================================================
@tool
def inspect_database(
    db_type: str = "sqlite",
    host: str = "localhost",
    port: int = 3306,
    database: str = "",
    user: str = "root",
    password: str = "",
    sqlite_path: str = ""
) -> str:
    """
    自动连接 SQLite/MySQL 数据库，查出所有表名和表结构。

    Args:
        db_type: 数据库类型，可选 "sqlite" 或 "mysql"，默认 "sqlite"
        host: MySQL 主机地址（仅 MySQL 需要）
        port: MySQL 端口号（仅 MySQL 需要），默认3306
        database: MySQL 数据库名（仅 MySQL 需要）
        user: MySQL 用户名（仅 MySQL 需要），默认 "root"
        password: MySQL 密码（仅 MySQL 需要）
        sqlite_path: SQLite 数据库文件路径（仅 SQLite 需要）

    Returns:
        str: 数据库结构描述
    """
    if db_type == "sqlite":
        if not sqlite_path:
            return "请提供 sqlite_path 参数（SQLite 数据库文件路径）。"
        return _inspect_sqlite(sqlite_path)

    elif db_type == "mysql":
        if not all([host, database, user]):
            return "请提供完整的 MySQL 连接参数：host, database, user, password。"
        return _inspect_mysql(host, database, user, password, port)

    else:
        return f"不支持的数据库类型: '{db_type}'。仅支持 'sqlite' 和 'mysql'。"
