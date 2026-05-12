"""
WriterAgent - 金牌小说主笔
负责根据大纲撰写几千字的章节正文。
为了保证长篇逻辑连贯，动笔前必须强制调用 semantic_search_memory 查阅前文设定和人物特征；
写完后必须调用 write_local_file 将正文保存为 markdown 文件，并将该章剧情摘要存入记忆库。
"""

from tools import (
    write_local_file,
    agent_memory_archive,
    semantic_search_memory,
    tools_list,
)

# 系统提示词
SYSTEM_PROMPT = (
    "你是金牌小说主笔（Writer）。负责根据大纲撰写几千字的章节正文。"
    "为了保证长篇逻辑连贯，你动笔前必须强制调用 semantic_search_memory "
    "查阅前文设定和人物特征；写完后必须调用 write_local_file 将正文保存为 "
    "markdown 文件，并将该章剧情摘要存入记忆库"
)


class WriterAgent:
    """小说主笔智能体，负责根据大纲撰写章节正文。"""

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

    def review_context(self, query: str, n_results: int = 5) -> str:
        """
        动笔前查阅前文设定和人物特征，确保逻辑连贯。

        Args:
            query: 搜索查询，描述要查阅的内容
            n_results: 返回的匹配结果数

        Returns:
            str: 语义检索结果
        """
        return semantic_search_memory(query=query, n_results=n_results)

    def write_chapter(
        self,
        chapter_num: int,
        title: str,
        content: str,
        output_dir: str = "chapters",
    ) -> str:
        """
        撰写章节正文，保存为 markdown 文件，并将剧情摘要存入记忆库。

        Args:
            chapter_num: 章节编号
            title: 章节标题
            content: 章节正文内容
            output_dir: 输出目录，默认为 "chapters"

        Returns:
            str: 保存结果描述
        """
        # 构建文件路径
        file_path = f"{output_dir}/chapter_{chapter_num:03d}_{title}.md"

        # 构建完整的 markdown 内容
        md_content = f"# 第{chapter_num}章 {title}\n\n{content}"

        # 保存为 markdown 文件
        result = write_local_file(file_path, md_content)

        # 提取剧情摘要（取前200字作为摘要）
        summary = content[:200].strip()
        if len(content) > 200:
            summary += "……"

        # 将剧情摘要存入记忆库
        agent_memory_archive(
            key=f"chapter_{chapter_num:03d}_content",
            content=(
                f"小说《{self.novel_name}》第{chapter_num}章《{title}》正文：{summary}"
            ),
            category="novel_chapter",
        )

        return result

    def write_chapter_with_review(
        self,
        chapter_num: int,
        title: str,
        content: str,
        context_query: str = "",
        output_dir: str = "chapters",
    ) -> str:
        """
        带前文回顾的章节撰写流程：先检索上下文，再撰写并保存。

        Args:
            chapter_num: 章节编号
            title: 章节标题
            content: 章节正文内容
            context_query: 前文检索查询词，为空时自动根据小说名和章节号生成
            output_dir: 输出目录

        Returns:
            str: 操作结果描述
        """
        # 1. 动笔前查阅前文设定
        query = context_query or f"小说《{self.novel_name}》前文设定和人物特征"
        context_result = self.review_context(query=query)

        # 2. 撰写并保存章节
        save_result = self.write_chapter(
            chapter_num=chapter_num,
            title=title,
            content=content,
            output_dir=output_dir,
        )

        return (
            f"【前文回顾】已检索相关设定和人物特征。\n"
            f"检索结果摘要：{context_result[:300]}……\n\n"
            f"【章节保存】{save_result}"
        )
