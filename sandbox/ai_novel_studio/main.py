"""
=====================================================================
 📚 AI Novel Studio - 小说创作工作室
=====================================================================
纯净的 CLI 多行交互循环，支持连续对话记忆。

使用方式：
    python main.py              # 启动 CLI 交互模式
    python main.py --ui         # 启动 Web UI 可视化工作台

交互说明（CLI 模式）：
    - 多行输入：输入空行结束当前输入
    - 输入 exit 退出程序
    - 每次对话复用全局 router 实例，保持连续对话记忆
=====================================================================
"""

import sys
import os
import argparse

# 确保项目根目录在 sys.path 中（必须在 import agents 之前）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import RouterAgent  # noqa: E402


# =====================================================================
# 全局单例：Router 实例
# =====================================================================
_router_instance: RouterAgent = None


def get_router() -> RouterAgent:
    """
    获取全局唯一的 RouterAgent 单例。

    首次调用时初始化 DirectorAgent、WriterAgent 以及统筹它们的 RouterAgent。
    后续调用直接返回已有实例，确保连续对话记忆不丢失。

    Returns:
        RouterAgent: 全局单例的 RouterAgent 实例
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = RouterAgent(novel_name="未命名小说")
    return _router_instance


# =====================================================================
# CLI 交互循环
# =====================================================================
def run_cli() -> None:
    """
    运行纯净的 CLI 多行交互循环。

    功能：
    - 支持多行输入（输入空行结束当前输入）
    - 输入 exit 退出程序
    - 复用全局 router 实例实现连续对话
    - 显示路由结果和对话历史
    """
    router = get_router()

    print("=" * 60)
    print("  📚 AI Novel Studio - 小说创作工作室")
    print("=" * 60)
    print()
    print("欢迎来到小说创作工作室！")
    print()
    print("您可以输入以下类型的指令：")
    print("  - 世界观设定 / 人物创建 / 大纲规划")
    print("  - 撰写章节正文")
    print()
    print("【操作说明】")
    print("  - 多行输入：输入空行结束当前输入")
    print("  - 输入 exit 退出程序")
    print("  - 输入 history 查看对话历史")
    print("  - 输入 clear 清空对话历史")
    print("  - 输入 novel:xxx 切换当前小说名称")
    print()

    while True:
        try:
            # 多行输入
            print(">>> (多行输入，空行结束)：")
            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)

            user_input = "\n".join(lines).strip()

            # 空输入跳过
            if not user_input:
                continue

            # 退出命令
            if user_input.lower() == "exit":
                print("感谢使用 AI Novel Studio，再见！")
                break

            # 查看对话历史
            if user_input.lower() == "history":
                history = router.get_conversation_history()
                if not history:
                    print("（暂无对话历史）")
                else:
                    print("\n" + "=" * 50)
                    print("📋 对话历史（共 {} 条）".format(len(history)))
                    print("=" * 50)
                    for i, entry in enumerate(history, 1):
                        role = entry["role"].upper()
                        content_preview = entry["content"][:100]
                        if len(entry["content"]) > 100:
                            content_preview += "..."
                        print("  [{}] {}: {}".format(i, role, content_preview))
                    print("=" * 50 + "\n")
                continue

            # 清空对话历史
            if user_input.lower() == "clear":
                router.clear_history()
                print("✅ 对话历史已清空。\n")
                continue

            # 切换小说名称
            if user_input.lower().startswith("novel:"):
                novel_name = user_input[6:].strip()
                if novel_name:
                    router.set_novel_name(novel_name)
                    print("✅ 当前小说已切换为：《{}》\n".format(novel_name))
                else:
                    print("❌ 请输入小说名称，格式：novel:小说名\n")
                continue

            # 路由分发
            print("\n" + "=" * 50)
            print("📖 当前小说：《{}》".format(router.novel_name))
            print("=" * 50)
            result = router.route(user_input)
            print(result)
            print()

        except KeyboardInterrupt:
            print("\n\n感谢使用 AI Novel Studio，再见！")
            break
        except EOFError:
            print("\n\n感谢使用 AI Novel Studio，再见！")
            break


# =====================================================================
# 入口
# =====================================================================
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="AI Novel Studio - 小说创作工作室"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="启动 Web UI 可视化工作台（默认启动 CLI 交互模式）",
    )
    args = parser.parse_args()

    if args.ui:
        # 启动 Web UI
        try:
            from web_ui import launch_ui  # noqa: E402
            print("正在启动 Web UI 可视化工作台...")
            print("访问地址：http://127.0.0.1:7860")
            launch_ui()
        except ImportError as e:
            print("❌ 启动 Web UI 失败：{}".format(e))
            print("请确保已安装 gradio：pip install gradio")
            sys.exit(1)
    else:
        # 启动 CLI 交互模式
        run_cli()
