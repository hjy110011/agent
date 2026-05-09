"""
=====================================================================
 🚦 RouterAgent - 多智能体路由调度核心 (v39.0)

 职责：
   - 接收用户输入，评估任务类型
   - 通过 delegate_task 工具将任务转发给对应的子 Agent
   - 收集子 Agent 的处理结果，最终汇报给用户
   - 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit
=====================================================================
"""

from agents.pm_agent import PMAgent  # noqa: F401
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
from langchain_core.tools import tool

# 将项目根目录加入 sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# =====================================================================
# 🚦 RouterAgent 类
# =====================================================================
class RouterAgent:
    """
    路由调度智能体。

    负责：
    1. 接收用户输入，评估任务类型
    2. 通过 delegate_task 工具将任务转发给对应的子 Agent
    3. 收集子 Agent 的处理结果，最终汇报给用户
    4. 维护自己独立且绝对静态的 messages 上下文列表以最大化 Cache Hit

    Attributes:
        name (str): 智能体名称
        llm: LLM 实例
        llm_with_tools: 绑定工具的 LLM 实例
        messages (list): 静态上下文消息列表
        system_prompt (str): 系统提示词
        coder_agent: CoderAgent 实例引用
        dba_agent: DBAAgent 实例引用
        reviewer_agent: ReviewerAgent 实例引用
        pm_agent: PMAgent 实例引用
    """

    ROUTER_SYSTEM_PROMPT = """你是一个智能路由调度器（RouterAgent），你的职责是：

## 核心职责
1. **评估用户任务**：分析用户输入的任务，判断其类型
2. **路由转发**：使用 delegate_task 工具将任务转发给最合适的子 Agent
3. **结果汇报**：收集子 Agent 的处理结果，以清晰易懂的方式汇报给用户

## 【可分配下属】
- **PMAgent**：技术产品经理，负责将用户模糊的初始需求转化为可执行的开发步骤，生成 plan.md 计划文件
- **CoderAgent**：编程/文件操作任务（编写代码、修改文件、运行命令等）
- **DBAAgent**：数据库任务（查询数据库、分析表结构、数据格式转换等）
- **ReviewerAgent**：代码审查任务（代码格式化、语法检查、编写并运行 pytest 单元测试、找 Bug）

## 任务分类规则
- **宏观新需求/新项目**（如用户提出一个模糊的、未拆解的新功能或新项目需求）
  → 优先转发给 PMAgent 进行前置拆解，生成 plan.md 计划文件
- **编程/文件操作任务**（如编写代码、修改文件、运行命令等）
  → 转发给 CoderAgent
- **数据库任务**（如查询数据库、分析表结构、数据格式转换等）
  → 转发给 DBAAgent
- **代码审查/测试任务**（如代码审查、找 Bug、写测试用例、格式化代码、语法检查等）
  → 转发给 ReviewerAgent

## 路由规则
1. 每次用户输入，你必须先评估任务类型
2. 如果用户输入的是一个宏观的新需求或新项目，Router 必须优先将任务派发给 PMAgent 进行前置拆解
3. 调用 delegate_task(target_agent, task_context) 转发任务
4. 等待子 Agent 返回结果后，整理并汇报给用户
5. 如果任务涉及多个领域，可以分步转发

## 重要约束
- 你只负责路由调度，不直接执行具体任务
- 所有具体工作必须由子 Agent 完成
- 最终汇报必须包含子 Agent 的执行结果摘要
- 如果子 Agent 返回"【任务完成】"，直接输出给用户
"""

    def __init__(self, coder_agent=None, dba_agent=None, reviewer_agent=None, pm_agent=None):
        """
        初始化 RouterAgent。

        Args:
            coder_agent: CoderAgent 实例（可选）
            dba_agent: DBAAgent 实例（可选）
            reviewer_agent: ReviewerAgent 实例（可选）
            pm_agent: PMAgent 实例（可选）
        """
        self.name = "RouterAgent"
        self.llm = init_llm()

        # 注册 delegate_task 工具
        self.delegate_tool = self._create_delegate_tool()
        self.llm_with_tools = self.llm.bind_tools([self.delegate_tool])

        # 维护独立且绝对静态的 messages 上下文列表
        self.messages = [
            SystemMessage(content=self.ROUTER_SYSTEM_PROMPT)
        ]

        # 子 Agent 引用
        self.coder_agent = coder_agent
        self.dba_agent = dba_agent
        self.reviewer_agent = reviewer_agent
        self.pm_agent = pm_agent

        # 子 Agent 结果缓存
        self._last_result = None

    def _create_delegate_tool(self):
        """
        创建 delegate_task 工具。

        Returns:
            Tool: 委托任务工具
        """
        router_self = self  # 捕获 self 引用

        @tool
        def delegate_task(target_agent: str, task_context: str) -> str:
            """
            将任务委托给指定的子 Agent 执行。

            根据任务类型选择合适的子 Agent，将任务上下文传递给它，
            并返回子 Agent 的执行结果。

            Args:
                target_agent: 目标子 Agent 名称
                    （"PMAgent" / "CoderAgent" / "DBAAgent" / "ReviewerAgent"）
                task_context: 要委托的任务上下文描述

            Returns:
                str: 子 Agent 的执行结果
            """
            return router_self._handle_delegate(target_agent, task_context)

        return delegate_task

    def _handle_delegate(self, target_agent: str, task_context: str) -> str:
        """
        处理委托任务。

        Args:
            target_agent: 目标子 Agent 名称
            task_context: 任务上下文

        Returns:
            str: 子 Agent 执行结果
        """
        print(f"\n   [RouterAgent] 转发任务到 {target_agent}...")
        print(f"   [RouterAgent] 任务上下文: {task_context[:200]}...")

        if target_agent == "PMAgent" and self.pm_agent:
            result = self.pm_agent.run(task_context)
            self._last_result = result
            return result
        elif target_agent == "CoderAgent" and self.coder_agent:
            result = self.coder_agent.run(task_context)
            self._last_result = result
            return result
        elif target_agent == "DBAAgent" and self.dba_agent:
            result = self.dba_agent.run(task_context)
            self._last_result = result
            return result
        elif target_agent == "ReviewerAgent" and self.reviewer_agent:
            result = self.reviewer_agent.run(task_context)
            self._last_result = result
            return result
        else:
            error_msg = f"未知的子 Agent: '{target_agent}' 或该 Agent 未注册"
            print(f"   [RouterAgent] ❌ {error_msg}")
            return f"错误: {error_msg}"

    def run(self, user_task: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
        """
        运行 RouterAgent 主循环。

        Args:
            user_task: 用户输入的任务
            max_steps: 最大循环步数

        Returns:
            str: 最终处理结果
        """
        print("\n" + "=" * 60)
        print("[🚦 RouterAgent] 已接收任务，开始评估路由...")
        print(f"📋 任务: {user_task[:100]}{'...' if len(user_task) > 100 else ''}")
        print("=" * 60)

        # 添加用户消息到上下文
        self.messages.append(HumanMessage(content=user_task))

        # v34.0 新增：全局看门狗 - 单轮最大执行时间（秒）
        ROUND_TIMEOUT = LLM_TIMEOUT * 3 + 60

        for step in range(1, max_steps + 1):
            print(f"\n--- 🔄 [RouterAgent] 第 {step} 轮路由决策 ---")

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
                    logger.error(f"RouterAgent LLM 调用超时 (第{llm_attempt}次尝试)")
                    if llm_attempt < MAX_RETRIES:
                        print(f"   ⏱️  RouterAgent LLM 调用超时，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"   ❌ RouterAgent LLM 调用超时，已达最大重试次数 ({MAX_RETRIES})")
                except Exception as e:
                    logger.error(f"RouterAgent LLM 调用失败 (第{llm_attempt}次尝试): {e}")
                    if llm_attempt < MAX_RETRIES:
                        print(f"   ⚠️  RouterAgent LLM 调用异常: {e}，{llm_retry_delay}秒后重试...")
                        time.sleep(llm_retry_delay)
                        llm_retry_delay = min(llm_retry_delay * 2, MAX_RETRY_DELAY)
                    else:
                        print(f"   ❌ RouterAgent LLM 调用异常，已达最大重试次数 ({MAX_RETRIES})")

            # 看门狗检测
            elapsed = time.time() - round_start_time
            if elapsed > ROUND_TIMEOUT:
                print(f"\n   ⏰ [RouterAgent] 看门狗触发：本轮执行超过 {ROUND_TIMEOUT} 秒，强制跳过")
                self.messages.append(HumanMessage(
                    content='系统提示：上一轮执行超时，请简化思路，直接调用 delegate_task 进行路由。'
                ))
                continue

            if response is None:
                print("\n⚠️  [RouterAgent] LLM 调用多次失败，强制停止。")
                break

            self.messages.append(response)
            content = response.content or ""

            # 检测到成功信号
            if "【任务完成】" in content:
                print(f"\n🎉 [RouterAgent] 最终汇报:\n{content}\n")
                return content

            valid_calls = getattr(response, "tool_calls", [])
            invalid_calls = getattr(response, "invalid_tool_calls", [])

            if not valid_calls and not invalid_calls:
                print(f"   [RouterAgent 思考中]: {content[:200]}...")
                self.messages.append(HumanMessage(
                    content='系统提示：请调用 delegate_task 工具将任务转发给子 Agent，或者如果任务已完成，输出"【任务完成】"。'
                ))
                continue

            for tool_call in valid_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print(f"🔧 [RouterAgent] 调用工具: {tool_name}")
                print(f"   参数: {str(tool_args)[:300]}")

                tool_result = None
                retry_delay = 1
                for attempt in range(1, MAX_RETRIES + 1):
                    tool_call_start = time.time()
                    try:
                        if tool_name == "delegate_task":
                            tool_result = self.delegate_tool.invoke(tool_args)
                        else:
                            tool_result = f"RouterAgent 不支持直接调用工具 '{tool_name}'，请使用 delegate_task"
                        print(f"   执行结果: 截取前150字... [{str(tool_result)[:150]}]")
                        break
                    except Exception as e:
                        tool_elapsed = time.time() - tool_call_start
                        if tool_elapsed > LLM_TIMEOUT:
                            tool_result = f"工具执行超时 ({tool_elapsed:.1f}秒)"
                            print(f"   ⏰ 工具执行超时 ({tool_elapsed:.1f}秒)，跳过")
                            break
                        if attempt == MAX_RETRIES:
                            tool_result = f"工具执行异常: {e}"
                            print(f"   执行异常: {e}")
                        else:
                            print(f"   ⏳ 工具执行异常，{retry_delay}秒后重试... ({attempt}/{MAX_RETRIES})")
                            time.sleep(retry_delay)
                            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

                self.messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

            for invalid_call in invalid_calls:
                tool_id = invalid_call.get("id")
                self.messages.append(ToolMessage(
                    content="系统拦截：JSON 格式非法。请检查 delegate_task 的参数格式。",
                    tool_call_id=tool_id
                ))

        else:
            print("\n⚠️ [RouterAgent] 达到了最大循环次数限制，强制停止。")

        return self._last_result or "RouterAgent 未能完成路由调度。"
