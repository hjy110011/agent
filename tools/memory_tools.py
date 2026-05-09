"""
=====================================================================
 🧠 记忆管理工具集
 包含：agent_memory_archive, agent_memory_retrieve,
       archive_history_step, plan_progress
=====================================================================
"""

import os
import json
from datetime import datetime

from langchain_core.tools import tool

from core.config import SAFE_BASE_DIR, logger
from core.agent_memory import _agent_memory


# =====================================================================
# 📦 agent_memory_archive
# =====================================================================
@tool
def agent_memory_archive(
    key: str,
    content: str,
    category: str = "logic",
    step: int = 0,
    metadata_json: str = ""
) -> str:
    """
    将关键信息压缩存档到本地 agent_history_archive/ 目录。

    自动压缩长文本为摘要，保留完整内容供后续检索。
    支持分类（step/tool/logic/config/error/snapshot）。

    Args:
        key: 存档键名（如 "important_logic", "step3_result", "error_info"）
        content: 要存档的内容（长文本会自动压缩摘要，完整内容保留）
        category: 分类（step/tool/logic/config/error/snapshot），默认 "logic"
        step: 当前步骤号（用于追踪进度），默认 0
        metadata_json: 可选的附加元数据 JSON 字符串

    Returns:
        str: 存档结果描述
    """
    valid_categories = ["step", "tool", "logic", "config", "error", "snapshot"]
    if category not in valid_categories:
        return (
            f"无效的分类: '{category}'。可选值: {', '.join(valid_categories)}"
        )

    metadata = {}
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            return f"metadata_json 格式错误: {e}"

    return _agent_memory.archive(
        category=category,
        key=key,
        content=content,
        step=step,
        metadata=metadata
    )


# =====================================================================
# 📖 agent_memory_retrieve
# =====================================================================
@tool
def agent_memory_retrieve(
    entry_id: int = -1,
    key: str = "",
    category: str = "",
    step: int = -1,
    mode: str = "summary"
) -> str:
    """
    从 agent_history_archive/ 检索之前存档的关键信息。

    支持按ID、键名、分类、步骤检索。

    Args:
        entry_id: 按存档ID精确检索（-1 表示不使用此条件）
        key: 按键名模糊检索（空字符串表示不限制）
        category: 按分类筛选（空字符串表示不限制）
        step: 按步骤号筛选（-1 表示不限制）
        mode: 返回模式
            - "summary": 返回摘要（默认）
            - "full": 返回完整内容
            - "list": 仅列出匹配项，不返回内容

    Returns:
        str: 检索结果
    """
    valid_modes = ["summary", "full", "list"]
    if mode not in valid_modes:
        return f"无效的 mode: '{mode}'。可选值: {', '.join(valid_modes)}"

    return _agent_memory.retrieve(
        entry_id=entry_id if entry_id >= 0 else None,
        key=key,
        category=category,
        step=step,
        mode=mode
    )


# =====================================================================
# 🗃️ archive_history_step
# =====================================================================
@tool
def archive_history_step(
    step_name: str,
    original_logic: str,
    compressed_summary: str,
    step_number: int = 0
) -> str:
    """
    将 v14.0 新增功能的核心逻辑压缩提取为"快照"存档。

    压缩前的完整内容保留在本地 agent_history_archive/ 目录，
    供 agent 后续通过 agent_memory_retrieve 调取。

    Args:
        step_name: 步骤/功能名称
        original_logic: 压缩前的完整原始逻辑/代码/内容
        compressed_summary: 手动压缩提取后的核心摘要
        step_number: 步骤编号（用于排序和追踪）

    Returns:
        str: 存档结果
    """
    # 将完整内容存档
    full_result = _agent_memory.archive(
        category="snapshot",
        key=f"{step_name}_full",
        content=original_logic,
        step=step_number,
        metadata={"type": "history_step_full", "step_name": step_name}
    )

    # 将摘要存档
    summary_result = _agent_memory.archive(
        category="snapshot",
        key=f"{step_name}_summary",
        content=compressed_summary,
        step=step_number,
        metadata={"type": "history_step_summary", "step_name": step_name}
    )

    return (
        f"历史步骤快照存档完成！\n"
        f"   步骤名称: {step_name}\n"
        f"   步骤编号: {step_number}\n"
        f"   完整内容: {full_result}\n"
        f"   核心摘要: {summary_result}"
    )


# =====================================================================
# 📋 plan_progress
# =====================================================================
@tool
def plan_progress(
    task_name: str = "",
    steps: str = "",
    mark_completed: str = "",
    action: str = "status"
) -> str:
    """
    自动管理 plan.md 的读写和进度更新。

    封装了"读取→标记→写入"三步操作，一步到位。
    支持 create（创建）/ status（查看）/ mark（标记完成）/ update（更新）四种操作。

    Args:
        task_name: 任务名称（首次创建时必填）
        steps: 步骤清单，用换行符分隔（首次创建时必填）
        mark_completed: 要标记为已完成的步骤编号或名称
        action: 操作类型（create/status/mark/update），默认status

    Returns:
        str: 操作结果
    """
    plan_path = os.path.join(SAFE_BASE_DIR, "plan.md")

    # ---------------------------------------------------------------
    # create: 创建新的 plan.md
    # ---------------------------------------------------------------
    if action == "create":
        if not task_name or not steps:
            return "创建 plan.md 需要提供 task_name 和 steps 参数！"

        step_list = [s.strip() for s in steps.split('\n') if s.strip()]
        lines = [
            f"# 📋 任务计划: {task_name}",
            f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 步骤清单",
            "",
        ]
        for i, step_desc in enumerate(step_list, 1):
            lines.append(f"- [ ] **步骤{i}**: {step_desc}")

        lines.extend([
            "",
            "---",
            "## 进度概览",
            f"- 总步骤: {len(step_list)}",
            "- 已完成: 0",
            "- 进行中: 0",
            "- 未开始: 0",
        ])

        content = '\n'.join(lines)
        try:
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return (
                f"plan.md 创建成功！\n"
                f"   任务: {task_name}\n"
                f"   步骤数: {len(step_list)}\n"
                f"   路径: {plan_path}"
            )
        except Exception as e:
            return f"创建 plan.md 失败: {e}"

    # ---------------------------------------------------------------
    # status: 查看当前进度
    # ---------------------------------------------------------------
    elif action == "status":
        if not os.path.exists(plan_path):
            return "plan.md 不存在。请先使用 create 操作创建。"

        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"当前进度:\n{content}"
        except Exception as e:
            return f"读取 plan.md 失败: {e}"

    # ---------------------------------------------------------------
    # mark: 标记步骤为已完成
    # ---------------------------------------------------------------
    elif action == "mark":
        if not mark_completed:
            return "mark 操作需要提供 mark_completed 参数！"

        if not os.path.exists(plan_path):
            return "plan.md 不存在。请先使用 create 操作创建。"

        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 支持按编号或名称标记
            targets = [t.strip() for t in mark_completed.split(',')]
            marked_count = 0

            for target in targets:
                # 按编号标记: "1" 或 "步骤1"
                if target.isdigit() or target.startswith('步骤'):
                    step_num = target.replace('步骤', '').strip()
                    old = f"- [ ] **步骤{step_num}**:"
                    new = f"- [x] **步骤{step_num}**:"
                    if old in content:
                        content = content.replace(old, new)
                        marked_count += 1
                else:
                    # 按名称标记
                    old = f"- [ ] {target}"
                    new = f"- [x] {target}"
                    if old in content:
                        content = content.replace(old, new)
                        marked_count += 1
                    else:
                        old2 = f"- [ ] **{target}**"
                        new2 = f"- [x] **{target}**"
                        if old2 in content:
                            content = content.replace(old2, new2)
                            marked_count += 1

            # 更新进度概览
            total = content.count("- [") - content.count("- [x]") - content.count("- [ ]")
            # 重新统计
            total_steps = content.count("- [ ]") + content.count("- [x]")
            completed = content.count("- [x]")
            in_progress = 0
            not_started = total_steps - completed

            # 更新进度概览部分
            import re
            content = re.sub(
                r'- 总步骤: \d+',
                f'- 总步骤: {total_steps}',
                content
            )
            content = re.sub(
                r'- 已完成: \d+',
                f'- 已完成: {completed}',
                content
            )
            content = re.sub(
                r'- 进行中: \d+',
                f'- 进行中: {in_progress}',
                content
            )
            content = re.sub(
                r'- 未开始: \d+',
                f'- 未开始: {not_started}',
                content
            )

            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return (
                f"标记完成 {marked_count} 个步骤！\n"
                f"   总步骤: {total_steps}\n"
                f"   已完成: {completed}\n"
                f"   未开始: {not_started}"
            )
        except Exception as e:
            return f"标记步骤失败: {e}"

    # ---------------------------------------------------------------
    # update: 更新步骤描述
    # ---------------------------------------------------------------
    elif action == "update":
        if not os.path.exists(plan_path):
            return "plan.md 不存在。请先使用 create 操作创建。"

        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 追加新的步骤描述
            if steps:
                step_list = [s.strip() for s in steps.split('\n') if s.strip()]
                existing_count = content.count("- [")
                for i, step_desc in enumerate(step_list, existing_count + 1):
                    content = content.replace(
                        "## 步骤清单",
                        f"## 步骤清单\n\n- [ ] **步骤{i}**: {step_desc}",
                        1
                    ) if "## 步骤清单" in content else content

                # 更新进度概览
                total_steps = content.count("- [ ]") + content.count("- [x]")
                completed = content.count("- [x]")
                import re
                content = re.sub(r'- 总步骤: \d+', f'- 总步骤: {total_steps}', content)
                content = re.sub(r'- 已完成: \d+', f'- 已完成: {completed}', content)
                content = re.sub(r'- 未开始: \d+', f'- 未开始: {total_steps - completed}', content)

            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return "plan.md 更新成功！"
        except Exception as e:
            return f"更新 plan.md 失败: {e}"

    return f"无效的 action: '{action}'。可选值: create, status, mark, update"
