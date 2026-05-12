"""
DirectorAgent - 顶级小说架构师
负责构建世界观、设定核心人物属性和规划详细的章节大纲。
完成重要设定后，必须调用 agent_memory_archive 将人物卡片和世界观精要存入向量记忆库。
"""

from tools import (
    write_local_file,
    agent_memory_archive,
    tools_list,
)

# 系统提示词
SYSTEM_PROMPT = (
    "你是顶级小说架构师（Director）。你不写具体正文，只负责构建世界观、"
    "设定核心人物属性和规划详细的章节大纲。当你完成重要设定后，"
    "必须调用 agent_memory_archive 将人物卡片和世界观精要存入向量记忆库"
)


class DirectorAgent:
    """小说架构师智能体，负责世界观构建、人物设定和章节大纲规划。"""

    def __init__(self, novel_name: str = ""):
        self.novel_name = novel_name
        self.system_prompt = SYSTEM_PROMPT
        self.tools = tools_list

    def set_novel_name(self, name: str) -> None:
        """设置小说名称。"""
        self.novel_name = name

    def get_system_prompt(self) -> str:
        """获取系统提示词。"""
        return self.system_prompt

    def get_tools(self) -> list:
        """获取绑定的工具列表。"""
        return self.tools

    def build_worldview(self, world_name: str, description: str) -> dict:
        """
        构建世界观设定，并存入记忆库。

        Args:
            world_name: 世界观名称
            description: 世界观详细描述

        Returns:
            dict: 世界观设定卡片
        """
        worldview_card = {
            "type": "worldview",
            "novel": self.novel_name,
            "world_name": world_name,
            "description": description,
        }
        # 存入向量记忆库
        agent_memory_archive(
            key=f"worldview_{world_name}",
            content=f"小说《{self.novel_name}》世界观 - {world_name}：{description}",
            category="novel_setting",
        )
        return worldview_card

    def create_character_card(
        self, name: str, role: str, traits: str, background: str
    ) -> dict:
        """
        创建人物卡片，并存入记忆库。

        Args:
            name: 人物姓名
            role: 角色定位（如主角、反派、配角等）
            traits: 性格特征
            background: 背景故事

        Returns:
            dict: 人物卡片
        """
        character_card = {
            "type": "character",
            "novel": self.novel_name,
            "name": name,
            "role": role,
            "traits": traits,
            "background": background,
        }
        # 存入向量记忆库
        agent_memory_archive(
            key=f"character_{name}",
            content=(
                f"小说《{self.novel_name}》人物卡片 - {name}（{role}）："
                f"性格特征：{traits}。背景：{background}"
            ),
            category="novel_character",
        )
        return character_card

    def outline_chapter(self, chapter_num: int, title: str, summary: str) -> dict:
        """
        规划章节大纲，并存入记忆库。

        Args:
            chapter_num: 章节编号
            title: 章节标题
            summary: 章节内容概要

        Returns:
            dict: 章节大纲卡片
        """
        chapter_outline = {
            "type": "chapter_outline",
            "novel": self.novel_name,
            "chapter_num": chapter_num,
            "title": title,
            "summary": summary,
        }
        # 存入向量记忆库
        agent_memory_archive(
            key=f"chapter_{chapter_num:03d}_outline",
            content=(
                f"小说《{self.novel_name}》第{chapter_num}章大纲 - "
                f"标题：{title}。概要：{summary}"
            ),
            category="novel_outline",
        )
        return chapter_outline

    def save_full_outline(self, outline_text: str, file_path: str) -> str:
        """
        将完整的大纲保存为 markdown 文件。

        Args:
            outline_text: 大纲全文
            file_path: 保存路径

        Returns:
            str: 保存结果描述
        """
        return write_local_file(file_path, outline_text)
