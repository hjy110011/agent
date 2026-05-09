"""
=====================================================================
 🤝 HITL (Human-In-The-Loop) 人工审批模块
 提供 request_human_approval 函数，用于在执行高危操作前请求人工确认。
=====================================================================
"""

from core.config import ENABLE_HITL


def request_human_approval(tool_name: str, context: dict) -> str:
    """
    请求人工审批。

    检查 config.ENABLE_HITL，若为 False 则直接返回 "ALLOW"。
    若为 True，在终端打印提示信息，使用 input() 获取用户输入。

    Args:
        tool_name: 要执行的工具名称（如 "write_local_file"）
        context: 上下文信息字典，包含工具调用的关键参数

    Returns:
        str: 审批结果
            - "ALLOW" - 用户允许执行
            - "REJECTED" - 用户拒绝执行
            - "FEEDBACK:用户输入的内容" - 用户提供了修改意见
    """
    if not ENABLE_HITL:
        return "ALLOW"

    # 构建上下文摘要
    context_summary = "\n".join([f"    {k}: {v}" for k, v in context.items()])

    print("\n" + "=" * 60)
    print("⚠️  申请执行 [{}]，是否允许？".format(tool_name))
    print("-" * 60)
    print("  上下文信息:")
    print(context_summary)
    print("-" * 60)
    print("  [Y] 允许执行  |  [N] 拒绝执行  |  输入其他内容作为修改意见")
    print("=" * 60)

    try:
        user_input = input(">>> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[审批] 输入中断，默认拒绝。")
        return "REJECTED"

    if not user_input:
        print("[审批] 输入为空，默认拒绝。")
        return "REJECTED"

    if user_input.upper() == "Y":
        print("[审批] ✅ 已允许执行 [{}]".format(tool_name))
        return "ALLOW"
    elif user_input.upper() == "N":
        print("[审批] ❌ 已拒绝执行 [{}]".format(tool_name))
        return "REJECTED"
    else:
        print("[审批] 💬 收到修改意见: {}".format(user_input))
        return "FEEDBACK:{}".format(user_input)
