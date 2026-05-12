"""
=====================================================================
 🎨 AI Novel Studio - 可视化作家工作台 (Web UI)
=====================================================================
基于 Gradio 的左右分栏沉浸式 UI：
- 左侧（40%）：ChatInterface 聊天面板，复用 get_router() 全局单例
- 右侧（60%）：文档编辑器，支持浏览/编辑/保存 .md 文件

使用方式：
    python main.py --ui
=====================================================================
"""

import os
import glob
import gradio as gr

# 确保项目根目录在 sys.path 中
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import get_router  # noqa: E402


# =====================================================================
# 工作区目录配置
# =====================================================================
# 工作区根目录：当前项目目录
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
# 小说章节输出目录
CHAPTERS_DIR = os.path.join(WORKSPACE_DIR, "chapters")


# =====================================================================
# 文件列表操作
# =====================================================================
def refresh_file_list() -> list:
    """
    递归扫描工作区内的所有 .md 文件。

    搜索范围：
    - 工作区根目录下的 .md 文件
    - chapters/ 子目录下的 .md 文件

    Returns:
        list: 文件路径列表（相对于工作区的相对路径）
    """
    md_files = []

    # 搜索工作区根目录
    md_files.extend(
        glob.glob(os.path.join(WORKSPACE_DIR, "*.md"), recursive=False)
    )

    # 搜索 chapters/ 子目录（如果存在）
    if os.path.isdir(CHAPTERS_DIR):
        md_files.extend(
            glob.glob(os.path.join(CHAPTERS_DIR, "**", "*.md"), recursive=True)
        )

    # 转换为相对路径，便于显示
    relative_files = []
    for fpath in sorted(md_files):
        rel_path = os.path.relpath(fpath, WORKSPACE_DIR)
        relative_files.append(rel_path)

    return relative_files


def load_file_content(file_rel_path: str) -> str:
    """
    读取选中文件的内容。

    Args:
        file_rel_path: 文件的相对路径（相对于工作区）

    Returns:
        str: 文件内容，如果文件不存在则返回空字符串
    """
    if not file_rel_path:
        return ""

    abs_path = os.path.join(WORKSPACE_DIR, file_rel_path)
    if not os.path.isfile(abs_path):
        return f"（文件不存在：{file_rel_path}）"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"（读取文件失败：{e}）"


def save_file_content(file_rel_path: str, content: str) -> str:
    """
    将内容保存到指定文件。

    Args:
        file_rel_path: 文件的相对路径（相对于工作区）
        content: 要写入的内容

    Returns:
        str: 保存结果提示
    """
    if not file_rel_path:
        return "⚠️ 请先选择一个文件"

    abs_path = os.path.join(WORKSPACE_DIR, file_rel_path)
    if not os.path.isfile(abs_path):
        return f"⚠️ 文件不存在：{file_rel_path}"

    try:
        # 确保父目录存在
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 已保存：{file_rel_path}"
    except Exception as e:
        return f"❌ 保存失败：{e}"


# =====================================================================
# ChatInterface 响应函数
# =====================================================================
def chat_response(message: str, history: list) -> str:
    """
    ChatInterface 的响应函数。

    复用 main.py 中的 get_router() 全局单例，
    调用 router.route() 进行任务路由分发。

    Args:
        message: 用户输入的消息
        history: 对话历史（Gradio 自动维护）

    Returns:
        str: 路由结果
    """
    router = get_router()
    return router.route(message)


# =====================================================================
# 构建 UI
# =====================================================================
def create_ui() -> gr.Blocks:
    """
    构建左右分栏的沉浸式作家工作台 UI。

    Returns:
        gr.Blocks: Gradio Blocks 实例
    """
    with gr.Blocks(
        title="AI Novel Studio - 小说创作工作室",
        theme=gr.themes.Soft(),
        css="""
        .chat-column { border-right: 1px solid #e0e0e0; }
        .editor-column { padding-left: 10px; }
        """
    ) as ui:
        gr.Markdown(
            """
            # 📚 AI Novel Studio
            ### 小说创作工作室
            """
        )

        with gr.Row():
            # =============================================================
            # 左侧栏（40%）：ChatInterface 聊天面板
            # =============================================================
            with gr.Column(scale=4, elem_classes="chat-column"):
                gr.Markdown("### 💬 创作指令")
                gr.Markdown(
                    "向导演（架构师）或主笔（写手）下达指令：\n"
                    "- **世界观设定 / 人物创建 / 大纲规划** → DirectorAgent\n"
                    "- **撰写章节正文** → WriterAgent"
                )

                # ChatInterface 复用 get_router().route
                gr.ChatInterface(
                    fn=chat_response,
                    title="",
                    description="",
                    placeholder="输入您的创作指令...",
                )

            # =============================================================
            # 右侧栏（60%）：文档编辑器
            # =============================================================
            with gr.Column(scale=6, elem_classes="editor-column"):
                gr.Markdown("### 📝 文档编辑器")

                # 顶部：刷新按钮 + 文件下拉框
                with gr.Row():
                    refresh_btn = gr.Button(
                        "🔄 刷新文件列表",
                        variant="secondary",
                        scale=2,
                    )
                    file_dropdown = gr.Dropdown(
                        label="选择文件",
                        choices=refresh_file_list(),
                        interactive=True,
                        scale=8,
                    )

                # 中间：正文编辑区
                file_editor = gr.Textbox(
                    label="正文 / 大纲内容",
                    placeholder="选择一个文件开始编辑...",
                    lines=30,
                    interactive=True,
                )

                # 底部：保存按钮
                save_btn = gr.Button(
                    "💾 保存修改",
                    variant="primary",
                )

                # 保存状态提示
                save_status = gr.Textbox(
                    label="保存状态",
                    interactive=False,
                    lines=1,
                )

        # =============================================================
        # 回调绑定
        # =============================================================

        # 1. 点击刷新按钮 → 重载文件列表
        refresh_btn.click(
            fn=lambda: gr.update(choices=refresh_file_list()),
            outputs=file_dropdown,
        )

        # 2. 下拉框选中文件 → 读取内容到编辑器
        file_dropdown.change(
            fn=load_file_content,
            inputs=file_dropdown,
            outputs=file_editor,
        )

        # 3. 点击保存按钮 → 覆写文件
        save_btn.click(
            fn=save_file_content,
            inputs=[file_dropdown, file_editor],
            outputs=save_status,
        )

    return ui


# =====================================================================
# 启动入口
# =====================================================================
def launch_ui(server_name: str = "127.0.0.1", server_port: int = 7860) -> None:
    """
    启动 Gradio Web UI。

    Args:
        server_name: 服务器地址，默认 127.0.0.1
        server_port: 服务器端口，默认 7860
    """
    ui = create_ui()
    ui.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
    )


# =====================================================================
# 直接运行
# =====================================================================
if __name__ == "__main__":
    launch_ui()
