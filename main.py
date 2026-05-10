"""
=====================================================================
 🚀 多智能体路由入口 (v46.0 CLI与Web UI双轨制)
 
 架构说明：
   - RouterAgent：路由调度核心，评估用户任务并转发给子 Agent
   - PMAgent：技术产品经理，负责将模糊需求转化为开发计划
   - CoderAgent：编程/文件操作子智能体
   - DBAAgent：数据库/数据格式子智能体
   - ReviewerAgent：代码审查与测试子智能体
   
 每个子 Agent 维护自己独立且绝对静态的 messages 上下文列表，
 以最大化 Cache Hit。
 
 双轨制入口：
   - python main.py          → 多行终端 CLI 交互模式
   - python main.py --ui     → 启动 Gradio Web UI 界面
=====================================================================
"""

from agents.reviewer_agent import ReviewerAgent
from agents.pm_agent import PMAgent
from agents.dba_agent import DBAAgent
from agents.coder_agent import CoderAgent
from agents.router_agent import RouterAgent
from core.utils import _TimeoutError, _input_with_timeout
from core.config import SAFE_BASE_DIR, DEFAULT_MAX_STEPS, logger, get_approval_mode
from core.hitl_approval import set_approval_strategy
import os
import sys
import argparse

# 将项目根目录加入 sys.path
_project_root = os.path.abspath(os.path.dirname(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# =====================================================================
# 🚀 多智能体路由入口
# =====================================================================
def run_multi_agent(user_task: str, max_steps: int = DEFAULT_MAX_STEPS) -> str:
    """
    多智能体路由入口。

    用户输入将首先交给 RouterAgent 评估，RouterAgent 决定转发给
    对应的子 Agent 执行，子 Agent 处理完毕后将结果封装返回给
    RouterAgent 最终汇报给用户。

    Args:
        user_task: 用户任务描述
        max_steps: 最大循环步数

    Returns:
        str: 最终处理结果
    """
    print("\n" + "=" * 60)
    print("[🤖 多智能体路由系统 (v46.0) 已启动]")
    print(f"📋 任务: {user_task[:100]}{'...' if len(user_task) > 100 else ''}")
    print("=" * 60)

    # 初始化子 Agent（每个子 Agent 维护独立的 messages 上下文）
    print("\n[系统] 初始化子智能体...")
    pm_agent = PMAgent()
    coder_agent = CoderAgent()
    dba_agent = DBAAgent()
    reviewer_agent = ReviewerAgent()
    print("[系统] PMAgent ✅ 已就绪")
    print("[系统] CoderAgent ✅ 已就绪")
    print("[系统] DBAAgent ✅ 已就绪")
    print("[系统] ReviewerAgent ✅ 已就绪")

    # 初始化 RouterAgent（传入所有子 Agent 引用）
    router = RouterAgent(
        coder_agent=coder_agent,
        dba_agent=dba_agent,
        reviewer_agent=reviewer_agent,
        pm_agent=pm_agent,
    )
    print("[系统] RouterAgent ✅ 已就绪")
    print("=" * 60)

    # 将任务交给 RouterAgent 处理
    result = router.run(user_task, max_steps)

    # 最终输出
    if result:
        print("\n" + "=" * 60)
        print("[📋 最终处理结果]")
        print(result)
        print("=" * 60)

    return result or ""


# =====================================================================
# 🚀 CLI 交互模式
# =====================================================================
def run_cli_mode():
    """运行多行终端 CLI 交互模式。"""
    print("=" * 60)
    print("🚀 企业级多智能体路由系统 v46.0")
    print(f"🔒 安全目录: {SAFE_BASE_DIR}")
    print("📋 架构: RouterAgent → [PMAgent | CoderAgent | DBAAgent | ReviewerAgent]")
    print("=" * 60)

    # =================================================================
    # 审批模式选择
    # =================================================================
    print("\n请选择审批模式：")
    print("  1. 免审批模式 (none) - 所有命令都不需要审批")
    print("  2. 高危审批模式 (dangerous_only) - 只审批高危命令")
    try:
        choice = input("请选择 (1/2，默认2): ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = ""

    if choice == "1":
        set_approval_strategy("none")
    else:
        set_approval_strategy("dangerous_only")

    # 显示当前审批模式
    mode = get_approval_mode()
    mode_display = {
        "none": "免审批模式 (none)",
        "dangerous_only": "高危审批模式 (dangerous_only)",
    }
    print(f"\n[系统] 当前审批模式: {mode_display.get(mode, mode)}")
    print("=" * 60)

    while True:
        try:
            print("\n" + "-" * 50)
            print("  [多行输入模式]")
            print("  - 输入单独一行 EOF 结束")
            print("  - 连续两次回车(空行)自动提交")
            print("  - 输入 q 单独一行退出程序")
            print("-" * 50)

            lines = []
            empty_line_count = 0
            while True:
                try:
                    line = _input_with_timeout(prompt="", timeout=300)
                except _TimeoutError:
                    print("  [输入超时，使用默认测试任务]")
                    task = "请帮我检查当前目录下的 Python 文件"
                    break
                if line.strip().lower() in ['q', 'quit', 'exit'] and not lines:
                    print("  Bye!")
                    raise SystemExit(0)
                if line.strip() == 'EOF':
                    break
                if line == '':
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        while lines and lines[-1] == '':
                            lines.pop()
                        break
                else:
                    empty_line_count = 0
                lines.append(line)

            task = "\n".join(lines).strip()
            if not task:
                print("  [输入为空，请重新输入]")
                continue
            run_multi_agent(task)
        except SystemExit:
            break
        except KeyboardInterrupt:
            print("\n\n  Bye!")
            break
        except Exception as e:
            logger.error(f"系统异常: {e}")


# =====================================================================
# 🚀 Web UI 模式
# =====================================================================
def run_web_ui_mode():
    """导入并启动 Gradio Web UI 界面。"""
    try:
        from web_ui import launch_ui
        launch_ui()
    except ImportError as e:
        print(f"[错误] 无法导入 web_ui 模块: {e}")
        print("[提示] 请确保已安装 gradio: pip install gradio")
        sys.exit(1)
    except Exception as e:
        print(f"[错误] 启动 Web UI 失败: {e}")
        sys.exit(1)


# =====================================================================
# 🚀 主程序入口
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🚀 企业级多智能体路由系统 v46.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py             启动多行终端 CLI 交互模式
  python main.py --ui        启动 Gradio Web UI 界面
  python main.py 任务描述    直接执行指定任务
        """,
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="启动 Gradio Web UI 界面（而非终端 CLI）",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="直接执行的任务描述（可选）",
    )

    args = parser.parse_args()

    if args.ui:
        # Web UI 模式
        run_web_ui_mode()
    elif args.task:
        # 直接执行指定任务
        run_multi_agent(" ".join(args.task))
    else:
        # 默认 CLI 交互模式
        run_cli_mode()
