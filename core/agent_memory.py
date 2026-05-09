"""
=====================================================================
 🧠 AgentMemory 类 (v16.0 新增, v17.0 修复 Bug)
=====================================================================
功能概述：
  统一管理所有"压缩存档"操作，支持自动压缩摘要、分类存储、版本追踪。
  将关键信息存入 agent_history_archive/ 目录供 agent 随时调取。

核心能力：
  - 自动压缩长文本为摘要（保留开头+结尾关键信息）
  - 按类型分类存储（step, tool, logic, config, error, snapshot）
  - 版本追踪（每次存档自动递增 ID）
  - 支持按 ID、键名、分类、步骤号检索
  - 自动清理旧存档（超过阈值自动触发）
=====================================================================
"""

import os
import json
from typing import Optional
from datetime import datetime

from .config import SAFE_BASE_DIR
from .utils import _format_size


class AgentMemory:
    """
    Agent 记忆管理器。

    负责将关键信息压缩存档到本地 agent_history_archive/ 目录，
    支持自动摘要压缩、分类存储、版本追踪和灵活检索。

    使用示例：
        memory = AgentMemory()
        memory.archive(category="logic", key="my_key", content="...")
        result = memory.retrieve(key="my_key", mode="summary")

    属性:
        ARCHIVE_DIR (str): 存档目录路径
        MEMORY_INDEX_FILE (str): 记忆索引文件路径
    """

    # 存档目录：位于安全基目录下的 agent_history_archive 文件夹
    ARCHIVE_DIR: str = os.path.join(SAFE_BASE_DIR, "agent_history_archive")
    # 索引文件：记录所有存档条目的元数据
    MEMORY_INDEX_FILE: str = os.path.join(ARCHIVE_DIR, "memory_index.json")

    def __init__(self):
        """
        初始化记忆管理器。

        确保存档目录和索引文件存在。如果索引文件不存在，则创建新的空索引。
        """
        os.makedirs(self.ARCHIVE_DIR, exist_ok=True)
        if not os.path.exists(self.MEMORY_INDEX_FILE):
            self._write_index({
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "entries": [],
                "next_id": 1
            })

    # ------------------------------------------------------------------
    # 索引读写（内部方法）
    # ------------------------------------------------------------------
    def _read_index(self) -> dict:
        """
        读取记忆索引文件。

        从 MEMORY_INDEX_FILE 中读取 JSON 格式的索引数据。
        如果文件损坏或不存在，返回一个全新的空索引。

        Returns:
            dict: 包含 entries（列表）和 next_id（整数）的索引字典
        """
        try:
            with open(self.MEMORY_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "entries": [],
                "next_id": 1
            }

    def _write_index(self, data: dict) -> None:
        """
        写入记忆索引文件。

        将索引数据以 JSON 格式写入 MEMORY_INDEX_FILE。

        Args:
            data: 包含 entries 和 next_id 的索引字典
        """
        with open(self.MEMORY_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 文本压缩摘要
    # ------------------------------------------------------------------
    def compress_summary(self, text: str, max_summary_len: int = 300) -> str:
        """
        将长文本压缩为摘要。

        压缩策略：保留开头关键信息 + 中间省略标记 + 结尾关键信息。
        如果文本长度不超过 max_summary_len，则直接返回原文。

        Args:
            text: 要压缩的原始文本
            max_summary_len: 摘要最大长度（字符数），默认 300

        Returns:
            str: 压缩后的摘要文本
        """
        if len(text) <= max_summary_len:
            return text

        # 开头保留一半长度，结尾保留三分之一长度
        head_len = max_summary_len // 2
        tail_len = max_summary_len // 3

        head = text[:head_len]
        tail = text[-tail_len:]

        return (
            f"{head}\n\n"
            f"... [中间省略 {len(text) - head_len - tail_len} 字符] ...\n\n"
            f"{tail}"
        )

    # ------------------------------------------------------------------
    # 存档操作
    # ------------------------------------------------------------------
    def archive(
        self,
        category: str,
        key: str,
        content: str,
        step: int = 0,
        metadata: Optional[dict] = None
    ) -> str:
        """
        将内容压缩存档到本地文件系统。

        存档流程：
        1. 读取索引，分配新的条目 ID
        2. 生成内容摘要
        3. 写入摘要文件（JSON 格式）和完整内容文件（TXT 格式）
        4. 更新索引
        5. 如果条目数超过阈值，自动触发清理

        Args:
            category: 分类（step, tool, logic, config, error, snapshot）
            key: 存档键名，用于后续检索
            content: 要存档的内容（长文本会自动压缩摘要）
            step: 当前步骤号，用于追踪进度
            metadata: 附加元数据字典

        Returns:
            str: 存档结果描述，包含 ID、分类、键名、步骤、字数统计
        """
        index = self._read_index()
        entry_id = index["next_id"]
        index["next_id"] += 1

        timestamp = datetime.now().isoformat()

        # 生成摘要
        summary = self.compress_summary(content)

        # 构建存档条目元数据
        entry = {
            "id": entry_id,
            "category": category,
            "key": key,
            "step": step,
            "timestamp": timestamp,
            "summary_len": len(summary),
            "full_len": len(content),
            "summary_file": f"entry_{entry_id:04d}_summary.json",
            "full_file": f"entry_{entry_id:04d}_full.txt",
            "metadata": metadata or {}
        }

        # 写入摘要文件（JSON 格式，包含关键信息）
        summary_data = {
            "id": entry_id,
            "category": category,
            "key": key,
            "step": step,
            "timestamp": timestamp,
            "summary": summary,
            "metadata": metadata or {}
        }
        summary_path = os.path.join(self.ARCHIVE_DIR, entry["summary_file"])
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        # 写入完整内容文件（纯文本格式）
        full_path = os.path.join(self.ARCHIVE_DIR, entry["full_file"])
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 更新索引
        index["entries"].append(entry)
        self._write_index(index)

        # 自动清理：如果条目数超过阈值，自动触发清理
        AUTO_CLEANUP_THRESHOLD = 500
        if len(index["entries"]) > AUTO_CLEANUP_THRESHOLD:
            self.cleanup(max_entries=300)

        return (
            f"✅ 存档成功 [ID={entry_id:04d}] | "
            f"分类: {category} | 键: {key} | "
            f"步骤: {step} | "
            f"摘要: {len(summary)}字 / 全文: {len(content)}字"
        )

    # ------------------------------------------------------------------
    # 检索操作
    # ------------------------------------------------------------------
    def retrieve(
        self,
        entry_id: Optional[int] = None,
        key: str = "",
        category: str = "",
        step: int = -1,
        mode: str = "summary"
    ) -> str:
        """
        检索存档内容。

        支持按 ID 精确检索、按键名模糊检索、按分类筛选、按步骤号筛选。
        四种筛选条件可以组合使用。

        Args:
            entry_id: 按存档 ID 精确检索（None 表示不使用此条件）
            key: 按键名模糊检索（空字符串表示不限制）
            category: 按分类筛选（空字符串表示不限制）
            step: 按步骤号筛选（-1 表示不限制）
            mode: 返回模式
                - "summary": 返回摘要（默认）
                - "full": 返回完整内容
                - "list": 仅列出匹配项，不返回内容

        Returns:
            str: 检索结果文本
        """
        index = self._read_index()
        entries = index["entries"]

        if not entries:
            return "📭 存档为空，尚无任何存档记录。"

        # 筛选匹配的条目
        matched = []
        for e in entries:
            # ID 精确匹配
            if entry_id is not None and e["id"] != entry_id:
                continue
            # 键名模糊匹配（不区分大小写）
            if key and key.lower() not in e["key"].lower():
                continue
            # 分类精确匹配
            if category and e["category"] != category:
                continue
            # 步骤精确匹配
            if step >= 0 and e["step"] != step:
                continue
            matched.append(e)

        if not matched:
            filters = []
            if entry_id is not None:
                filters.append(f"ID={entry_id}")
            if key:
                filters.append(f"key包含'{key}'")
            if category:
                filters.append(f"分类={category}")
            if step >= 0:
                filters.append(f"步骤={step}")
            filter_str = ", ".join(filters) if filters else "全部"
            return f"🔍 未找到匹配的存档记录。筛选条件: {filter_str}"

        # mode="list": 列出匹配项（支持分页，最多显示 50 条）
        if mode == "list":
            MAX_LIST_ITEMS = 50
            lines = ["📋 存档匹配列表:", "=" * 50]

            display_matched = matched[:MAX_LIST_ITEMS]
            for e in display_matched:
                lines.append(
                    f"  [{e['id']:04d}] {e['category']:10s} | "
                    f"步骤{e['step']:3d} | {e['key']:30s} | "
                    f"{e['summary_len']}字摘要 / {e['full_len']}字全文"
                )

            total = len(matched)
            if total > MAX_LIST_ITEMS:
                lines.append(f"\n... 还有 {total - MAX_LIST_ITEMS} 条未显示")
            lines.append(f"\n共 {total} 条匹配")
            return "\n".join(lines)

        # mode="summary" 或 "full": 读取具体内容
        result_parts = []
        for e in matched:
            if mode == "full":
                # 读取完整内容文件
                full_path = os.path.join(self.ARCHIVE_DIR, e["full_file"])
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        full_content = f.read()
                except FileNotFoundError:
                    full_content = "(完整内容文件丢失)"

                result_parts.append(
                    f"📖 存档 [ID={e['id']:04d}] 完整内容\n"
                    f"   分类: {e['category']} | 键: {e['key']} | 步骤: {e['step']}\n"
                    f"   {'=' * 50}\n"
                    f"{full_content}"
                )
            else:
                # 读取摘要文件（JSON 格式）
                summary_path = os.path.join(self.ARCHIVE_DIR, e["summary_file"])
                try:
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                    summary_text = summary_data.get("summary", "(摘要内容丢失)")
                except (FileNotFoundError, json.JSONDecodeError):
                    summary_text = "(摘要文件丢失)"

                result_parts.append(
                    f"📖 存档 [ID={e['id']:04d}] 摘要\n"
                    f"   分类: {e['category']} | 键: {e['key']} | 步骤: {e['step']}\n"
                    f"   {'=' * 50}\n"
                    f"{summary_text}"
                )

        return "\n\n---\n\n".join(result_parts)

    # ------------------------------------------------------------------
    # 列出所有分类统计
    # ------------------------------------------------------------------
    def list_categories(self) -> str:
        """
        列出所有存档分类及其条目数。

        统计信息包括：
        - 每个分类的条目数量
        - 每个分类的最新步骤号
        - 总记录数和分类数
        - 存储占用（摘要和全文分别统计）

        Returns:
            str: 分类统计报告文本
        """
        index = self._read_index()
        entries = index["entries"]

        if not entries:
            return "📭 存档为空。"

        # 按分类统计
        categories = {}
        for e in entries:
            cat = e["category"]
            if cat not in categories:
                categories[cat] = {"count": 0, "latest_step": 0}
            categories[cat]["count"] += 1
            categories[cat]["latest_step"] = max(
                categories[cat]["latest_step"], e["step"]
            )

        lines = ["📊 存档分类统计:", "=" * 50]
        for cat, info in sorted(categories.items()):
            lines.append(
                f"  📁 {cat:15s} | {info['count']:3d} 条 | "
                f"最新步骤: {info['latest_step']}"
            )
        lines.append(f"\n共 {len(entries)} 条记录, {len(categories)} 个分类")

        # 计算存储占用
        total_summary_size = 0
        total_full_size = 0
        for e in entries:
            for fname in [e["summary_file"], e["full_file"]]:
                fpath = os.path.join(self.ARCHIVE_DIR, fname)
                try:
                    if os.path.exists(fpath):
                        if "summary" in fname:
                            total_summary_size += os.path.getsize(fpath)
                        else:
                            total_full_size += os.path.getsize(fpath)
                except Exception:
                    pass
        lines.append(
            f"存储占用: 摘要 {_format_size(total_summary_size)} / "
            f"全文 {_format_size(total_full_size)}"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 清理旧存档
    # ------------------------------------------------------------------
    def cleanup(self, max_entries: int = 200) -> str:
        """
        清理超出数量限制的旧存档。

        自动保留最新的 max_entries 条记录，删除更早的记录。
        同时删除对应的摘要文件和完整内容文件。

        Args:
            max_entries: 保留的最大条目数，默认 200

        Returns:
            str: 清理结果描述
        """
        index = self._read_index()
        entries = index["entries"]

        if len(entries) <= max_entries:
            return (
                f"ℹ️ 存档数量 ({len(entries)}) 未超过限制 "
                f"({max_entries})，无需清理。"
            )

        # 按 ID 排序（ID 越大越新）
        entries.sort(key=lambda e: e["id"])
        to_remove = entries[:-max_entries]
        to_keep = entries[-max_entries:]

        # 删除旧存档的文件
        removed_count = 0
        removed_size = 0
        for e in to_remove:
            for fname in [e["summary_file"], e["full_file"]]:
                fpath = os.path.join(self.ARCHIVE_DIR, fname)
                try:
                    if os.path.exists(fpath):
                        removed_size += os.path.getsize(fpath)
                        os.remove(fpath)
                        removed_count += 1
                except Exception:
                    pass

        # 更新索引（只保留最新的条目）
        index["entries"] = to_keep
        self._write_index(index)

        size_str = _format_size(removed_size)
        return (
            f"✅ 清理完成: 移除 {len(to_remove)} 条旧存档, "
            f"删除 {removed_count} 个文件 ({size_str}), "
            f"保留 {len(to_keep)} 条"
        )


# =====================================================================
# 🌐 全局 AgentMemory 实例
# =====================================================================
# 所有记忆管理工具共享同一个 AgentMemory 实例
_agent_memory = AgentMemory()
