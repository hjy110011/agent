"""
=====================================================================
 📋 PMAgent - 技术产品经理智能体 (v39.0)

 职责：
   - 拦截用户模糊的初始需求
   - 通过逻辑推理将需求转化为可执行的开发步骤
   - 强制调用 plan_progress(action='create') 生成 plan.md 文件
   - 绝不写具体代码，只负责制定严谨的计划
   - 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit
=====================================================================
"""

from tools import (
    plan_progress, write_local_file,
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

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

# 将项目根目录加入 sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# =====================================================================
# 📋 PMAgent 类
# =====================================================================
class PMAgent:
    """
    技术产品经理智能体。

    负责将用户模糊的初始需求转化为可执行的开发步骤，
    强制调用 plan_progress 生成 plan.md 文件。
    绝不写具体代码，只负责制定严谨的计划。

    Attributes:
        name (str): 智能体名称
        llm: LLM 实例
        llm_with_tools: 绑定工具的 LLM 实例
        messages (list): 独立且绝对静态的上下文消息列表
        system_prompt (str): 系统提示词
    """

    PM_SYSTEM_PROMPT = (
        "你是一名资深的技术产品经理。你的职责是拦截用户模糊的初始需求，"
        "通过逻辑推理将其转化为可执行的开发步骤，并强制调用 "
        "plan_progress(action='create') 生成 plan.md 文件。"
        "你绝不写具体代码，只负责制定严谨的计划。"
    )

    def __init__(self):
        """初始化 PMAgent。"""
        self.name = "PMAgent"
        self.llm = init_llm()

        # PMAgent 绑定的工具列表（计划管理 + 文件写入）
        self.pm_tools = [
            plan_progress,
            write_local_file,
        ]

        self.llm_with_tools = self.llm.bind_tools(self.pm_tools)

        # 维护独立且绝对静态的 messages 上下文列表
        self.messages = [
            SystemMessage(content=self.PM_SYSTEM_PROMPT)
        ]

    def run(self, task_context: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
        """
        运行 PMAgent 处理任务。

        Args:
            task_context: 任务上下文描述
            max_steps: 最大循环步数

        Returns:
            str: 处理结果
        """
        print("\n   [📋 PMAgent] 已接收任务，开始分析需求...")
        print("   [📋 PMAgent] 需求: " + task_context[:100] + "...")

        # 添加任务到上下文
        self.messages.append(HumanMessage(content=task_context))

        # 看门狗超时
        ROUND_TIMEOUT = LLM_TIMEOUT * 3 + 60

        for step in range(1, max_steps + 1):
            print("\n   --- 🔄 [PMAgent] 第 " + str(step) + " 轮 ---")

            round_start_time = time.time()

            # 高低水位线安全滑动窗口
            self.messages = _apply_watermark_truncation(self.messages)

            # LLM 调用（带超时保护和自动重试）
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
                    logger.error(
                        "PMAgent LLM 调用超时 (第" + str(llm_attempt) + "次尝试)"
                    )
                    if llm_attempt < MAX_RETRIES:
                        print("      ⏱️  PMAgent LLM 超时，" +
                              str(llm_retry_delay) + "秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(
                            llm_retry_delay * 2, MAX_RETRY_DELAY
                        )
                    else:
                        print("      ❌ PMAgent LLM 超时，已达最大重试次数")
                except Exception as e:
                    logger.error("PMAgent LLM 调用失败: " + str(e))
                    if llm_attempt < MAX_RETRIES:
                        print("      ⚠️  PMAgent LLM 异常: " + str(e) +
                              "，" + str(llm_retry_delay) + "秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(
                            llm_retry_delay * 2, MAX_RETRY_DELAY
                        )
                    else:
                        print("      ❌ PMAgent LLM 异常，已达最大重试次数")

            # 看门狗检测
            elapsed = time.time() - round_start_time
            if elapsed > ROUND_TIMEOUT:
                print("      ⏰ [PMAgent] 看门狗触发：本轮执行超过 " +
                      str(ROUND_TIMEOUT) + " 秒，强制跳过")
                self.messages.append(HumanMessage(
                    content='系统提示：上一轮执行超时，请简化思路，'
                            '直接调用 plan_progress 生成计划。'
                ))
                continue

            if response is None:
                print("\n   ⚠️  [PMAgent] LLM 调用多次失败，强制停止。")
                break

            self.messages.append(response)
            content = response.content or ""

            # 检测完成信号
            if "【任务完成】" in content:
                print("\n   🎉 [PMAgent] 计划制定完成!\n")
                return content

            valid_calls = getattr(response, "tool_calls", [])
            invalid_calls = getattr(response, "invalid_tool_calls", [])

            if not valid_calls and not invalid_calls:
                print("      [PMAgent 思考中]: " + content[:150] + "...")
                self.messages.append(HumanMessage(
                    content='系统提示：请调用 plan_progress 工具生成 '
                            'plan.md 计划文件，或者如果计划已完成，'
                            '输出"【任务完成】"。'
                ))
                continue

            for tool_call in valid_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print("      🔧 [PMAgent] 调用: " + tool_name)
                if tool_name == 'write_local_file':
                    print("         参数: '" +
                          tool_args.get('file_path', '') +
                          "' (内容已省略)")
                else:
                    print("         参数: " + str(tool_args)[:200])

                tool_result = None
                retry_delay = 1
                for attempt in range(1, MAX_RETRIES + 1):
                    tool_call_start = time.time()
                    try:
                        tool_func = next(
                            (t for t in self.pm_tools if t.name == tool_name),
                            None
                        )
                        if tool_func is None:
                            tool_result = "工具 '" + tool_name + "' 未找到"
                            break
                        tool_result = tool_func.invoke(tool_args)
                        print("         结果: [" + str(tool_result)[:150] +
                              "]")
                        break
                    except Exception as e:
                        tool_elapsed = time.time() - tool_call_start
                        if tool_elapsed > LLM_TIMEOUT:
                            tool_result = "工具执行超时 (" + \
                                str(round(tool_elapsed, 1)) + "秒)"
                            break
                        if attempt == MAX_RETRIES:
                            tool_result = "工具执行异常: " + str(e)
                        else:
                            print("         ⏳ 重试... (" +
                                  str(attempt) + "/" +
                                  str(MAX_RETRIES) + ")")
                            time.sleep(retry_delay)
                            retry_delay = min(
                                retry_delay * 2, MAX_RETRY_DELAY
                            )

                self.messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                )

            for invalid_call in invalid_calls:
                tool_id = invalid_call.get("id")
                self.messages.append(ToolMessage(
                    content="系统拦截：JSON 格式非法。请检查参数格式。",
                    tool_call_id=tool_id
                ))

        else:
            print("\n   ⚠️ [PMAgent] 达到了最大循环次数限制。")

        return "【PMAgent 计划制定完成，但未输出完成信号】"
