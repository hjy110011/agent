"""
=====================================================================
 🔍 ReviewerAgent - 代码审查与测试子智能体 (v38.0)
 
 职责：
   - 代码格式化与质量检查
   - Python 语法检查
   - 编写并运行 pytest 单元测试
   - 发现 Bug 并明确指出
   - 绑定代码审查相关工具
   - 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit
=====================================================================
"""

from tools import (
    code_format_tool, check_python_syntax,
    write_local_file, run_terminal_command,
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
# 🔍 ReviewerAgent 类
# =====================================================================
class ReviewerAgent:
    """
    代码审查与测试子智能体。

    负责代码格式化、语法检查、编写并运行 pytest 单元测试、
    发现 Bug 并明确指出。

    绑定的工具：
    - code_format_tool: 代码格式化与质量检查
    - check_python_syntax: Python 语法检查
    - write_local_file: 写入/创建文件（用于编写测试文件）
    - run_terminal_command: 执行终端命令（用于运行 pytest）

    Attributes:
        name (str): 智能体名称
        llm: LLM 实例
        llm_with_tools: 绑定工具的 LLM 实例
        messages (list): 独立且绝对静态的上下文消息列表
        system_prompt (str): 系统提示词
    """

    REVIEWER_SYSTEM_PROMPT = """你是严苛的代码审查与测试专家，收到代码后必须先进行格式化和语法检查，然后编写并运行 pytest 单元测试，有 Bug 必须明确指出。

## 核心职责
1. **代码格式化**：使用 code_format_tool 对代码进行格式化
2. **语法检查**：使用 check_python_syntax 检查 Python 语法
3. **编写测试**：编写 pytest 单元测试用例
4. **运行测试**：使用 run_terminal_command 运行 pytest
5. **Bug 报告**：发现 Bug 必须明确指出，包括位置和原因

## 可用工具
你拥有以下工具集：

### ✅ 代码质量工具
- `code_format_tool(action, file_path)` - 代码格式化与质量检查
  - format: 自动格式化 Python 代码
  - check: 使用 flake8 进行代码质量检查
  - stats: 统计代码指标
- `check_python_syntax(file_path)` - 检查 Python 语法

### 📂 文件操作工具
- `write_local_file(file_path, content)` - 写入/创建文件（用于编写测试文件）

### 💻 终端命令工具
- `run_terminal_command(command)` - 执行终端命令（用于运行 pytest）

## 工作流程
1. **接收代码**：获取待审查的代码文件路径或内容
2. **格式化**：先使用 code_format_tool 格式化代码
3. **语法检查**：使用 check_python_syntax 检查语法
4. **编写测试**：编写 pytest 单元测试用例，保存为 test_*.py 文件
5. **运行测试**：使用 run_terminal_command("pytest test_*.py -v") 运行测试
6. **报告结果**：汇总格式化结果、语法检查结果、测试结果
7. **Bug 报告**：如果发现 Bug，明确指出位置、原因和修复建议
8. 任务完成后输出"【任务完成】"结束

## 重要约束
- 必须先进行格式化和语法检查，再编写测试
- 测试用例必须覆盖正常情况和边界情况
- 发现 Bug 必须明确指出，不能含糊其辞
- 测试文件命名格式为 test_<被测试文件名>.py
- 任务完成后必须输出"【任务完成】"
"""

    def __init__(self):
        """初始化 ReviewerAgent。"""
        self.name = "ReviewerAgent"
        self.llm = init_llm()

        # ReviewerAgent 绑定的工具列表（仅限代码审查相关）
        self.reviewer_tools = [
            code_format_tool,
            check_python_syntax,
            write_local_file,
            run_terminal_command,
        ]

        self.llm_with_tools = self.llm.bind_tools(self.reviewer_tools)

        # 维护独立且绝对静态的 messages 上下文列表
        self.messages = [
            SystemMessage(content=self.REVIEWER_SYSTEM_PROMPT)
        ]

    def run(self, task_context: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
        """
        运行 ReviewerAgent 处理任务。

        Args:
            task_context: 任务上下文描述
            max_steps: 最大循环步数

        Returns:
            str: 处理结果
        """
        print(f"\n   [🔍 ReviewerAgent] 已接收任务，开始处理...")
        print(f"   [🔍 ReviewerAgent] 任务: {task_context[:100]}...")

        # 添加任务到上下文
        self.messages.append(HumanMessage(content=task_context))

        # 看门狗超时
        ROUND_TIMEOUT = LLM_TIMEOUT * 3 + 60

        for step in range(1, max_steps + 1):
            print(f"\n   --- 🔄 [ReviewerAgent] 第 {step} 轮 ---")

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
                    logger.error(f"ReviewerAgent LLM 调用超时 (第{llm_attempt}次尝试)")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⏱️  ReviewerAgent LLM 超时，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ ReviewerAgent LLM 超时，已达最大重试次数")
                except Exception as e:
                    logger.error(f"ReviewerAgent LLM 调用失败: {e}")
                    if llm_attempt < MAX_RETRIES:
                        print(f"      ⚠️  ReviewerAgent LLM 异常: {e}，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"      ❌ ReviewerAgent LLM 异常，已达最大重试次数")

            # 看门狗
            elapsed = time.time() - round_start_time
            if elapsed > ROUND_TIMEOUT:
                print(f"      ⏰ [ReviewerAgent] 看门狗触发：本轮超时")
                self.messages.append(HumanMessage(
                    content='系统提示：上一轮执行超时，请简化思路继续。'
                ))
                continue

            if response is None:
                print("\n   ⚠️  [ReviewerAgent] LLM 调用多次失败，强制停止。")
                break

            self.messages.append(response)
            content = response.content or ""

            # 检测完成信号
            if "【任务完成】" in content:
                print(f"\n   🎉 [ReviewerAgent] 任务完成!\n")
                return content

            valid_calls = getattr(response, "tool_calls", [])
            invalid_calls = getattr(response, "invalid_tool_calls", [])

            if not valid_calls and not invalid_calls:
                print(f"      [ReviewerAgent 思考中]: {content[:150]}...")
                self.messages.append(HumanMessage(
                    content='系统提示：请调用工具进行下一步，或者如果任务已完成，输出"【任务完成】"。'
                ))
                continue

            for tool_call in valid_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print(f"      🔧 [ReviewerAgent] 调用: {tool_name}")
                if tool_name in ['write_local_file']:
                    print(f"         参数: '{tool_args.get('file_path')}' (内容已省略)")
                else:
                    print(f"         参数: {str(tool_args)[:200]}")

                tool_result = None
                retry_delay = 1
                for attempt in range(1, MAX_RETRIES + 1):
                    tool_call_start = time.time()
                    try:
                        tool_func = next(
                            (t for t in self.reviewer_tools if t.name == tool_name),
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
            print("\n   ⚠️ [ReviewerAgent] 达到了最大循环次数限制。")

        return "【ReviewerAgent 处理完成，但未输出完成信号】"
