"""
=====================================================================
 🌐 Web UI 控制台界面 (v46.1)

 基于 Gradio 构建的 Web 控制台，对接底层多智能体路由系统。
 用户可在网页端输入消息，发送给 Agent 处理并返回结果。

 修复记录:
   v46.1 - 修复 Gradio 6.x 兼容性问题
           - 移除 ChatInterface 已废弃的 placeholder 参数
           - 将 theme/css 从 Blocks 移到 launch() 方法
           - 新增模式选择（用户确认模式 / 自动模式）
=====================================================================
"""

from core.hitl_approval import set_approval_strategy
from core.config import SAFE_BASE_DIR, logger
from main import run_multi_agent
import gradio as gr
import sys
import os

# 将项目根目录加入 sys.path
_project_root = os.path.abspath(os.path.dirname(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# =====================================================================
# 🌐 全局状态
# =====================================================================
# 模式选择: "confirm" = 用户确认模式（需要输入 Y/N）
#            "auto"    = 自动模式（不需要输入 Y/N）
_current_mode = "auto"


# =====================================================================
# 🌐 Web UI 聊天处理函数
# =====================================================================
def respond(message: str, history: list) -> str:
    """
    处理用户消息，调用多智能体路由系统并返回结果。

    Args:
        message: 用户输入的消息
        history: 聊天历史记录

    Returns:
        str: Agent 处理结果
    """
    if not message or not message.strip():
        return "请输入有效消息。"

    try:
        logger.info(f"[Web UI] 收到用户消息: {message[:100]}")
        result = run_multi_agent(message)
        return result or "Agent 未返回有效结果。"
    except Exception as e:
        logger.error(f"[Web UI] 处理异常: {e}")
        return f"系统处理异常: {e}"


# =====================================================================
# 🌐 模式切换回调
# =====================================================================
def on_mode_change(mode: str):
    """
    模式切换回调函数。

    Args:
        mode: 选择的模式 ("confirm" 或 "auto")
    """
    global _current_mode
    _current_mode = mode
    mode_label = "用户确认模式" if mode == "confirm" else "自动模式"
    logger.info(f"[Web UI] 模式已切换为: {mode_label}")
    return f"✅ 已切换为 **{mode_label}**"


# =====================================================================
# 🌐 构建 Gradio 界面
# =====================================================================
def create_ui() -> gr.Blocks:
    """
    创建 Gradio Web 界面。

    Returns:
        gr.Blocks: Gradio 界面实例
    """
    # Web 端默认使用免审批模式，所有操作自动放行
    set_approval_strategy("none")

    with gr.Blocks(
        title="🤖 多智能体路由系统 - Web UI",
    ) as demo:
        gr.Markdown(
            """
            # 🤖 多智能体路由系统 v46.1
            ### 架构: RouterAgent → [PMAgent | CoderAgent | DBAAgent | ReviewerAgent]
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown(
                    f"""
                    **系统信息**
                    - 安全目录: `{SAFE_BASE_DIR}`
                    - 模式: Web UI
                    - ✅ 审批模式: **免审批（Web端自动放行）**
                    """
                )

        # =============================================================
        # 🎛️ 模式选择区域
        # =============================================================
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🎛️ 运行模式")
                mode_radio = gr.Radio(
                    choices=[
                        ("🔐 用户确认模式（需要输入 Y/N 确认）", "confirm"),
                        ("🤖 自动模式（无需确认，自动执行）", "auto"),
                    ],
                    value="auto",
                    label="选择运行模式",
                    info="用户确认模式：Agent 在执行关键操作前会询问用户是否继续；自动模式：Agent 自动执行所有操作。",
                )
                mode_status = gr.Markdown("✅ 当前模式: **自动模式**")

        # 模式切换事件
        mode_radio.change(
            fn=on_mode_change,
            inputs=mode_radio,
            outputs=mode_status,
        )

        # =============================================================
        # 💬 对话区域
        # =============================================================
        # ChatInterface 自动管理聊天历史
        # 注意: Gradio 6.x 已移除 placeholder 参数
        gr.ChatInterface(
            fn=respond,
            title="💬 对话控制台",
            description="在下方输入您的任务描述，系统将自动路由到对应的子智能体处理。",
            examples=[
                "请帮我检查当前目录下的 Python 文件",
                "列出当前目录结构",
                "帮我创建一个简单的 Python 脚本",
            ],
        )

        gr.Markdown(
            """
            ---
            **提示**: 输入 `q` 或 `quit` 退出程序（需在终端中操作）。
            """
        )

    return demo


# =====================================================================
# 🌐 启动入口
# =====================================================================
def launch_ui(server_name: str = "127.0.0.1", server_port: int = 7860, share: bool = False):
    """
    启动 Gradio Web 界面。

    Args:
        server_name: 服务器地址，默认 127.0.0.1
        server_port: 服务器端口，默认 7860
        share: 是否生成公网链接，默认 False
    """
    print("=" * 60)
    print("🌐 多智能体路由系统 Web UI 启动中...")
    print(f"🔗 本地地址: http://{server_name}:{server_port}")
    if share:
        print("📡 公网链接: 启动后将显示在控制台")
    print("=" * 60)

    demo = create_ui()
    # Gradio 6.x: theme 和 css 需要移到 launch() 方法中
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True,
        theme=gr.themes.Soft(),
        css="""
        .container { max-width: 900px; margin: auto; }
        footer { display: none !important; }
        """,
    )


# =====================================================================
# 🚀 直接运行入口
# =====================================================================
if __name__ == "__main__":
    launch_ui()
