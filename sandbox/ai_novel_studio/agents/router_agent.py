"""
RouterAgent - 小说创作总编
负责根据用户输入判断任务类型并分派给对应的 Agent：
- 遇到宏观设定、写大纲任务派发给 DirectorAgent
- 遇到撰写具体章节正文的任务派发给 WriterAgent
支持连续对话（保持对话历史）。
"""

from agents import DirectorAgent, WriterAgent

# 系统提示词
SYSTEM_PROMPT = (
    "你是小说创作总编（Router）。遇到宏观设定、写大纲任务派发给 DirectorAgent；"
    "遇到撰写具体章节正文的任务派发给 WriterAgent"
)


class RouterAgent:
    """小说创作总编智能体，负责路由分发任务。"""

    def __init__(self, novel_name: str = ""):
        self.novel_name = novel_name
        self.system_prompt = SYSTEM_PROMPT
        self.director = DirectorAgent(novel_name=novel_name)
        self.writer = WriterAgent(novel_name=novel_name)
        # 对话历史：存储 (role, content) 元组列表
        self.conversation_history: list = []

    def set_novel_name(self, name: str) -> None:
        """设置小说名称，同步更新下属 Agent。"""
        self.novel_name = name
        self.director.set_novel_name(name)
        self.writer.set_novel_name(name)

    def get_system_prompt(self) -> str:
        """获取系统提示词。"""
        return self.system_prompt

    def add_to_history(self, role: str, content: str) -> None:
        """
        添加一条对话记录到历史。

        Args:
            role: 角色（user / assistant / system）
            content: 对话内容
        """
        self.conversation_history.append({"role": role, "content": content})

    def get_conversation_history(self) -> list:
        """
        获取完整的对话历史。

        Returns:
            list: 对话历史列表，每项为 {"role": str, "content": str}
        """
        return self.conversation_history

    def clear_history(self) -> None:
        """清空对话历史。"""
        self.conversation_history = []

    def route(self, user_input: str) -> str:
        """
        根据用户输入判断任务类型并分派给对应的 Agent。

        路由逻辑：
        - 包含"世界观"、"设定"、"人物"、"角色"、"大纲"、"规划"等关键词 → DirectorAgent
        - 包含"写"、"章"、"正文"、"撰写"、"章节"等关键词 → WriterAgent
        - 默认：提示用户明确任务类型

        Args:
            user_input: 用户输入的自然语言指令

        Returns:
            str: 路由结果描述
        """
        # 记录用户输入到对话历史
        self.add_to_history("user", user_input)

        # 关键词判断
        director_keywords = ["世界观", "设定", "人物", "角色", "大纲", "规划", "架构"]
        writer_keywords = ["写", "章", "正文", "撰写", "章节", "创作"]

        # 统计匹配关键词数量
        director_score = sum(1 for kw in director_keywords if kw in user_input)
        writer_score = sum(1 for kw in writer_keywords if kw in user_input)

        # 路由决策
        if director_score > writer_score:
            # 派发给 DirectorAgent
            result = (
                f"【Router】已将任务派发给 DirectorAgent（小说架构师）\n"
                f"当前小说：{self.novel_name}\n"
                f"Director 系统提示词：{self.director.get_system_prompt()}\n"
                f"可用工具：{len(self.director.get_tools())} 个\n"
                f"请调用 DirectorAgent 的方法来执行任务。"
            )
            self.add_to_history("assistant", result)
            return result

        elif writer_score > director_score:
            # 派发给 WriterAgent
            result = (
                f"【Router】已将任务派发给 WriterAgent（小说主笔）\n"
                f"当前小说：{self.novel_name}\n"
                f"Writer 系统提示词：{self.writer.get_system_prompt()}\n"
                f"可用工具：{len(self.writer.get_tools())} 个\n"
                f"请调用 WriterAgent 的方法来执行任务。"
            )
            self.add_to_history("assistant", result)
            return result

        else:
            # 无法判断，提示用户明确任务类型
            result = (
                f"【Router】无法确定任务类型。\n"
                f"当前小说：{self.novel_name}\n\n"
                f"请明确您的需求：\n"
                f"  - 世界观设定 / 人物创建 / 大纲规划 → 交给 DirectorAgent（架构师）\n"
                f"  - 撰写章节正文 → 交给 WriterAgent（主笔）\n\n"
                f"您也可以直接说：\n"
                f"  - '帮我规划一下这本小说的世界观和人物'\n"
                f"  - '开始写第一章正文'"
            )
            self.add_to_history("assistant", result)
            return result
