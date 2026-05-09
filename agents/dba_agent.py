"""
=====================================================================
 🗄️ DBAAgent - 数据库/数据格式子智能体 (v37.0)
 
 职责：
   - 处理所有数据库相关任务（查询数据库、分析表结构等）
   - 处理数据格式转换任务（JSON/CSV/YAML 解析、转换等）
   - 绑定数据库探查工具和数据格式处理工具
   - 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit
=====================================================================
"""

from tools import (
    inspect_database,
    data_format_tool, file_backup_tool, code_format_tool,
    read_local_file, read_file_by_lines, write_local_file,
    list_directory_tree, grep_search,
    agent_memory_archive, agent_memory_retrieve,
    archive_history_step, plan_progress,
)
from core.utils import (
    _apply_watermark_truncation, _TimeoutError,
    _execute_with_timeout
)
from core.llm import init_llm
from core.config import (
    DEFAULT_MAX_STEPS, LLM_TIMEOUT, MAX_RETRIES,
    MAX_RETRY_DELAY, logger
)
import os
import sys
import time
import logging
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

# 将项目根目录加入 sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# =====================================================================
# 🗄️ DBAAgent 类
# =====================================================================
class DBAAgent:
    """
    数据库/数据格式子智能体。

    负责所有数据库探查和数据格式处理任务，绑定数据库工具、
    数据格式转换工具、文件读取工具等。

    Attributes:
        name (str): 智能体名称
        llm: LLM 实例
        llm_with_tools: 绑定工具的 LLM 实例
        messages (list): 独立且绝对静态的上下文消息列表
        system_prompt (str): 系统提示词
    """

    DBA_SYSTEM_PROMPT = """你是一个专业的数据库与数据格式智能体（DBAAgent），你的职责是：

## 核心职责
1. **数据库探查**：连接 SQLite/MySQL 数据库，分析表结构和数据
2. **数据格式处理**：解析、验证、格式化 JSON/CSV/YAML 数据
3. **格式互转**：JSON ↔ CSV, JSON ↔ YAML 等格式转换
4. **数据查询**：按路径查询 JSON/YAML 数据
5. **文件备份**：创建文件备份、恢复版本、对比差异

## 可用工具
你拥有以下工具集：

### 🗄️ 数据库工具
- `inspect_database(db_type, sqlite_path, ...)` - 探查数据库结构
  - SQLite: inspect_database(db_type="sqlite", sqlite_path="xxx.db")
  - MySQL: inspect_database(db_type="mysql", host="...", database="...", user="...", password="...")

### 📊 数据格式工具
- `data_format_tool(action, data_format, input_data, query_path)` - 数据格式处理
  - parse: 解析并验证数据格式
  - validate: 仅验证数据格式是否正确
  - format: 美化格式化数据
  - query: 按路径查询/提取数据
  - convert: 格式互转（JSON ↔ CSV, JSON ↔ YAML）
- `file_backup_tool(action, file_path, version)` - 文件备份与恢复
  - backup: 创建文件备份
  - list: 列出版本
  - restore: 恢复版本
  - diff: 对比差异
- `code_format_tool(action, file_path)` - 代码格式化与质量检查

### 📂 文件读取工具
- `read_local_file(file_path)` - 读取小文件
- `read_file_by_lines(file_path, start_line, end_line)` - 按行读取大文件
- `write_local_file(file_path, content)` - 写入文件
- `list_directory_tree(root_path, max_depth)` - 列出目录结构
- `grep_search(pattern, file_pattern, root_dir)` - 文本搜索

### 🧠 记忆管理工具
- `agent_memory_archive(key, content, category)` - 存档信息
- `agent_memory_retrieve(key, mode)` - 检索存档
- `archive_history_step(step_name, ...)` - 存档历史步骤
- `plan_progress(action, ...)` - 管理计划进度

## 工作流程
1. 分析接收到的任务上下文
2. 选择合适的工具逐步执行
3. 任务完成后输出"【任务完成】"结束

## 重要约束
- 数据库连接需要正确的参数
- 数据格式转换时注意源格式和目标格式
- 任务完成后必须输出"【任务完成】"
"""

    def __init__(self):
        """初始化 DBAAgent。"""
        self.name = "DBAAgent"
        self.llm = init_llm()

        # DBAAgent 绑定的工具列表（数据库 + 数据格式 + 文件读取 + 记忆）
        self.dba_tools = [
            # 数据库
            inspect_database,
            # 数据格式
            data_format_tool, file_backup_tool, code_format_tool,
            # 文件读取
            read_local_file, read_file_by_lines, write_local_file,
            list_directory_tree, grep_search,
            # 记忆管理
            agent_memory_archive, agent_memory_retrieve,
            archive_history_step, plan_progress,
        ]

        self.llm_with_tools = self.llm.bind_tools(self.dba_tools)

        # 维护独立且绝对静态的 messages 上下文列表
        self.messages = [
            SystemMessage(content=self.DBA_SYSTEM_PROMPT)
        ]

    def run(self, task_context: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
        """
        运行 DBAAgent 处理任务。

        Args:
            task_context: 任务上下文描述
            max_steps: 最大循环步数

        Returns:
            str: 处理结果
        """
        print(f"\n   [🗄️ DBAAgent] 已接收任务，开始处理...")
        print(f"   [🗄️ DBAAgent] 任务: {task_context[:100]}...")

        # 添加任务到上下文
        self.messages.append(HumanMessage(content=task_context))

        # 看门狗超时
        ROUND_TIMEOUT = LLM_TIMEOUT * 3 + 60

        for step in range(1, max_steps + 1):
            print(f"\n   --- 🔄 [DBAAgent] 第 {step} 轮 ---")

            round_start_time = time.time()

            # 高低水位线安全滑动窗口
            self.messages = _apply_watermark_truncation(self.messages)

            # LLM 调用
            response = None
            llm_retry_delay = 2
            for llm_attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = _execute_with_timeout(
                        self.llm_with_tools.invoke,
                        args=(self.messages,),
                        timeout=LLM_TIMEOUT
                    )
                    break
                except _TimeoutError:
                    logger.error(f"DBAAgent LLM 调用超时 (第{llm_attempt}次尝试)")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⏱️  DBAAgent LLM 超时，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ DBAAgent LLM 超时，已达最大重试次数")
                except Exception as e:
                    logger.error(f"DBAAgent LLM 调用失败: {e}")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⚠️  DBAAgent LLM 异常: {e}，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ DBAAgent LLM 异常，已达最大重试次数")

            # 看门狗
            elapsed = time.time() - round_start_time
            if elapsed > ROUND_TIMEOUT:
                print(f"      ⏰ [DBAAgent] 看门狗触发：本轮超时")
                self.messages.append(HumanMessage(
                    content='系统提示：上一轮执行超时，请简化思路继续。'
                ))
                continue

            if response is None:
                print("\n   ⚠️  [DBAAgent] LLM 调用多次失败，强制停止。")
                break

            self.messages.append(response)
            content = response.content or ""

            # 检测完成信号
            if "【任务完成】" in content:
                print(f"\n   🎉 [DBAAgent] 任务完成!\n")
                return content

            valid_calls = getattr(response, "tool_calls", [])
            invalid_calls = getattr(response, "invalid_tool_calls", [])

            if not valid_calls and not invalid_calls:
                print(f"      [DBAAgent 思考中]: {content[:150]}...")
                self.messages.append(HumanMessage(
                    content='系统提示：请调用工具进行下一步，或者如果任务已完成，输出"【任务完成】"。'
                ))
                continue

            for tool_call in valid_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print(f"      🔧 [DBAAgent] 调用: {tool_name}")
                print(f"         参数: {str(tool_args)[:200]}")

                tool_result = None
                retry_delay = 1
                for attempt in range(1, MAX_RETRIES + 1):
                    tool_call_start = time.time()
                    try:
                        tool_func = next(
                            (t for t in self.dba_tools if t.name == tool_name),
                            None
                        )
                        if tool_func is None:
                            tool_result = f"工具 '{tool_name}' 未找到"
                            break
                        tool_result = tool_func.invoke(tool_args)
                        print(f"         结果: [{str(tool_result)[:150]}]")
                        break
                    except Exception as e:
                        tool_elapsed = time.time() - tool_call_start
                        if tool_elapsed > LLM_TIMEOUT:
                            tool_result = f"工具执行超时 ({tool_elapsed:.1f}秒)"
                            break
                        if attempt == MAX_RETRIES:
                            tool_result = f"工具执行异常: {e}"
                        else:
                            print(f"         ⏳ 重试... ({attempt}/{MAX_RETRIES})")
                            time.sleep(retry_delay)
                            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

                self.messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

            for invalid_call in invalid_calls:
                tool_id = invalid_call.get("id")
                self.messages.append(ToolMessage(
                    content="系统拦截：JSON 格式非法。请检查参数格式。",
                    tool_call_id=tool_id
                ))

        else:
            print("\n   ⚠️ [DBAAgent] 达到了最大循环次数限制。")

        return "【DBAAgent 处理完成，但未输出完成信号】"
