"""
=====================================================================
 💻 CoderAgent - 编程/文件操作子智能体 (v37.0)
 
 职责：
   - 处理所有编程相关任务（编写代码、修改文件、运行命令等）
   - 绑定文件操作工具和终端命令工具
   - 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit
=====================================================================
"""

from tools import (
    read_local_file, read_file_by_lines, write_local_file,
    run_terminal_command, list_directory_tree, pip_install,
    check_python_syntax, search_code_ast, grep_search,
    git_init_repo, git_create_branch, git_commit,
    git_diff, git_status, git_log, git_checkout, git_branch_list,
    read_webpage, web_search,
    agent_memory_archive, agent_memory_retrieve,
    archive_history_step, plan_progress,
    semantic_search_memory,
    data_format_tool, file_backup_tool, code_format_tool,
    send_api_request, fetch_dynamic_webpage,
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
# 💻 CoderAgent 类
# =====================================================================
class CoderAgent:
    """
    编程/文件操作子智能体。

    负责所有编程相关任务，绑定文件操作、终端命令、Git 版本控制、
    代码质量检查、网络搜索等工具。

    Attributes:
        name (str): 智能体名称
        llm: LLM 实例
        llm_with_tools: 绑定工具的 LLM 实例
        messages (list): 独立且绝对静态的上下文消息列表
        system_prompt (str): 系统提示词
    """

    CODER_SYSTEM_PROMPT = """你是一个专业的编程智能体（CoderAgent），你的职责是：

## 核心职责
1. **编写代码**：根据需求编写高质量的 Python 代码
2. **文件操作**：读写文件、创建目录、管理项目结构
3. **运行命令**：执行终端命令、安装依赖
4. **代码审查**：检查代码语法、格式化代码、分析代码质量
5. **版本控制**：使用 Git 进行版本管理
6. **网络搜索**：查阅文档、搜索解决方案

## 可用工具
你拥有以下工具集：

### 📂 文件操作工具
- `read_local_file(file_path)` - 读取小文件全文
- `read_file_by_lines(file_path, start_line, end_line)` - 按行读取大文件
- `write_local_file(file_path, content)` - 写入/创建文件
- `list_directory_tree(root_path, max_depth)` - 列出目录结构

### 💻 终端命令工具
- `run_terminal_command(command)` - 执行终端命令
- `pip_install(package_name, upgrade)` - 安装 Python 包

### ✅ 代码质量工具
- `check_python_syntax(file_path)` - 检查 Python 语法
- `code_format_tool(action, file_path)` - 格式化/检查代码
- `search_code_ast(file_path, search_type)` - AST 解析源码

### 🔍 搜索工具
- `grep_search(pattern, file_pattern, root_dir)` - 文本搜索
- `read_webpage(url)` - 抓取网页内容
- `web_search(query)` - 网络搜索

### 🗃️ Git 版本控制工具
- `git_init_repo(repo_path)` - 初始化仓库
- `git_create_branch(branch_name, repo_path)` - 创建分支
- `git_commit(message, repo_path)` - 提交更改
- `git_diff(repo_path, file_path)` - 查看差异
- `git_status(repo_path)` - 查看状态
- `git_log(repo_path, max_count)` - 查看历史
- `git_checkout(branch_name, repo_path)` - 切换分支
- `git_branch_list(repo_path)` - 列出分支

### 🧠 记忆管理工具
- `agent_memory_archive(key, content, category)` - 存档信息
- `agent_memory_retrieve(key, mode)` - 检索存档
- `archive_history_step(step_name, ...)` - 存档历史步骤
- `plan_progress(action, ...)` - 管理计划进度
- `semantic_search_memory(query, n_results)` - 通过自然语言语义搜索历史记忆

### 📊 数据格式工具
- `data_format_tool(action, data_format, input_data)` - 数据格式处理
- `file_backup_tool(action, file_path)` - 文件备份恢复

### 🌐 API 调试工具
- `send_api_request(url, method, headers, body)` - 发送 HTTP 请求，支持 GET/POST/PUT/DELETE 等，可自定义 Headers 和 Body，类似 Postman

### 🕸️ 高级动态网页抓取工具
- `fetch_dynamic_webpage(url, wait_time=2)` - 使用 Playwright 无头浏览器渲染 JavaScript 动态内容，提取网页纯文本

## 工作流程
1. 分析接收到的任务上下文
2. 选择合适的工具逐步执行
3. 任务完成后输出"【任务完成】"结束

你现在拥有高级 API 调试工具(send_api_request)和高级动态网页抓取工具(fetch_dynamic_webpage)，
可以直接发送带 Headers 和 Body 的真实请求来测试后端接口连通性，
或使用 Playwright 无头浏览器真正渲染并读取包含 JavaScript 动态内容的网页和在线文档。

你现在拥有向量语义记忆检索工具(semantic_search_memory)，当你遗忘前置步骤的细节或遇到历史同类 Bug 时，必须优先使用自然语言搜索本地记忆库提取经验。

## 重要约束
- 所有文件操作必须在安全目录内进行
- 执行代码前必须先检查语法
- 任务完成后必须输出"【任务完成】"
"""

    def __init__(self):
        """初始化 CoderAgent。"""
        self.name = "CoderAgent"
        self.llm = init_llm()

        # CoderAgent 绑定的工具列表（文件操作 + 终端 + Git + 搜索 + 记忆 + 数据格式）
        self.coder_tools = [
            # 文件操作
            read_local_file, read_file_by_lines, write_local_file,
            run_terminal_command, list_directory_tree, pip_install,
            # 代码质量
            check_python_syntax, search_code_ast, grep_search,
            code_format_tool,
            # Git 版本控制
            git_init_repo, git_create_branch, git_commit,
            git_diff, git_status, git_log, git_checkout, git_branch_list,
            # 搜索
            read_webpage, web_search,
            # 记忆管理
            agent_memory_archive, agent_memory_retrieve,
            archive_history_step, plan_progress,
            semantic_search_memory,
            # 数据格式
            data_format_tool, file_backup_tool,
            # API 调试
            send_api_request,
            # 网页抓取
            fetch_dynamic_webpage,
        ]

        self.llm_with_tools = self.llm.bind_tools(self.coder_tools)

        # 维护独立且绝对静态的 messages 上下文列表
        self.messages = [
            SystemMessage(content=self.CODER_SYSTEM_PROMPT)
        ]

    def run(self, task_context: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
        """
        运行 CoderAgent 处理任务。

        Args:
            task_context: 任务上下文描述
            max_steps: 最大循环步数

        Returns:
            str: 处理结果
        """
        print(f"\n   [💻 CoderAgent] 已接收任务，开始处理...")
        print(f"   [💻 CoderAgent] 任务: {task_context[:100]}...")

        # 添加任务到上下文
        self.messages.append(HumanMessage(content=task_context))

        # 看门狗超时
        ROUND_TIMEOUT = LLM_TIMEOUT * 3 + 60

        for step in range(1, max_steps + 1):
            print(f"\n   --- 🔄 [CoderAgent] 第 {step} 轮 ---")

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
                    logger.error(f"CoderAgent LLM 调用超时 (第{llm_attempt}次尝试)")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⏱️  CoderAgent LLM 超时，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ CoderAgent LLM 超时，已达最大重试次数")
                except Exception as e:
                    logger.error(f"CoderAgent LLM 调用失败: {e}")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⚠️  CoderAgent LLM 异常: {e}，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ CoderAgent LLM 异常，已达最大重试次数")

            # 看门狗
            elapsed = time.time() - round_start_time
            if elapsed > ROUND_TIMEOUT:
                print(f"      ⏰ [CoderAgent] 看门狗触发：本轮超时")
                self.messages.append(HumanMessage(
                    content='系统提示：上一轮执行超时，请简化思路继续。'
                ))
                continue

            if response is None:
                print("\n   ⚠️  [CoderAgent] LLM 调用多次失败，强制停止。")
                break

            self.messages.append(response)
            content = response.content or ""

            # 检测完成信号
            if "【任务完成】" in content:
                print(f"\n   🎉 [CoderAgent] 任务完成!\n")
                return content

            # ===== tool_calls 处理逻辑 =====

            # 提取 tool_calls
            tool_calls = getattr(response, 'tool_calls', [])
            if not tool_calls:
                # 没有 tool_calls 且没有完成信号 → 继续下一轮
                continue

            # 分离合法调用和非法调用
            valid_calls = []
            invalid_calls = []
            for tc in tool_calls:
                tc_name = tc.get('name', '')
                tc_args = tc.get('args', {})
                tc_id = tc.get('id', '')

                # 检查工具是否在 coder_tools 列表中
                tool_func = next(
                    (t for t in self.coder_tools if t.name == tc_name),
                    None
                )
                if tool_func is None:
                    invalid_calls.append({"name": tc_name, "id": tc_id})
                else:
                    valid_calls.append({
                        "name": tc_name, "args": tc_args,
                        "id": tc_id, "func": tool_func
                    })

            # 情况 A：合法调用 → 执行工具
            for call_info in valid_calls:
                tool_name = call_info["name"]
                tool_args = call_info["args"]
                tool_id = call_info["id"]
                tool_func = call_info["func"]

                print(f"      🛠️  [{tool_name}] 调用中...")

                # 查找工具函数
                tool_func = next(
                    (t for t in self.coder_tools if t.name == tool_name),
                    None
                )
                if tool_func is None:
                    tool_result = f"错误：未找到工具 '{tool_name}'"
                    print(f"         结果: {tool_result}")
                else:
                    # 执行工具（含重试机制）
                    tool_result = None
                    tool_retry_delay = 1
                    for tool_attempt in range(1, MAX_RETRIES + 1):
                        tool_call_start = time.time()
                        try:
                            tool_result = tool_func.invoke(tool_args)
                            print(f"         结果: [{str(tool_result)[:150]}]")
                            break
                        except Exception as e:
                            tool_elapsed = time.time() - tool_call_start
                            if tool_elapsed > LLM_TIMEOUT:
                                tool_result = f"工具执行超时 ({tool_elapsed:.1f}秒)"
                                print(f"         ⏰ 工具执行超时 ({tool_elapsed:.1f}秒)，跳过")
                                break
                            logger.error(f"CoderAgent 工具 {tool_name} 调用失败: {e}")
                            if tool_attempt < MAX_RETRIES:
                                print(f"         ⏳ 重试... ({tool_attempt}/{MAX_RETRIES})")
                                time.sleep(tool_retry_delay)
                                tool_retry_delay = min(tool_retry_delay * 2, MAX_RETRY_DELAY)
                            else:
                                tool_result = f"工具 {tool_name} 调用失败: {e}"
                                print(f"         结果: {tool_result}")

                # 特殊处理：write_local_file 后自动语法检查
                if tool_name == 'write_local_file' and tool_result and '成功写入' in str(tool_result):
                    written_file = tool_args.get('file_path', '')
                    if written_file.endswith('.py'):
                        print(f"         🔍 自动语法检查: {written_file}")
                        try:
                            syntax_func = next(
                                (t for t in self.coder_tools if t.name == 'check_python_syntax'),
                                None
                            )
                            if syntax_func:
                                syntax_result = syntax_func.invoke({"file_path": written_file})
                                print(f"         📋 语法检查: {syntax_result[:150]}...")
                                tool_result = str(tool_result) + \
                                    "\n\n【自动语法检查结果】\n" + str(syntax_result)
                        except Exception as e:
                            print(f"         ⚠️ 语法检查异常: {e}")

                # 将工具结果追加到 messages
                self.messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

            # 情况 C：非法调用 → 提示 JSON 格式错误
            for invalid_call in invalid_calls:
                tool_id = invalid_call.get("id")
                print(f"      ⚠️ [CoderAgent] 非法调用: {invalid_call.get('name', 'unknown')}")
                self.messages.append(ToolMessage(
                    content="系统拦截：JSON 格式非法。请检查参数格式。",
                    tool_call_id=tool_id
                ))

        # for 循环正常结束（达到最大步数）后的兜底
        print(f"\n   ⚠️  [CoderAgent] 达到最大步数 {max_steps}，强制结束。")
        return "【CoderAgent 处理完成，但未输出完成信号】"
