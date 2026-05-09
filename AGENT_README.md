# 🤖 企业级多智能体路由系统 (v41.0)

> **多智能体协作框架** — 基于 LangChain + DeepSeek 构建，通过 RouterAgent 统一调度多个专业子 Agent，实现复杂任务的智能分解与自动化执行。

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构](#2-系统架构)
- [3. Agent 角色与职责](#3-agent-角色与职责)
  - [3.1 RouterAgent — 路由调度核心](#31-routeragent--路由调度核心)
  - [3.2 PMAgent — 技术产品经理](#32-pmagent--技术产品经理)
  - [3.3 CoderAgent — 编程智能体](#33-coderagent--编程智能体)
  - [3.4 DBAAgent — 数据库与数据格式智能体](#34-dbaagent--数据库与数据格式智能体)
  - [3.5 ReviewerAgent — 代码审查与测试智能体](#35-revieweragent--代码审查与测试智能体)
- [4. 项目结构](#4-项目结构)
- [5. 各 Agent 的配置与使用](#5-各-agent-的配置与使用)
  - [5.1 环境配置](#51-环境配置)
  - [5.2 启动方式](#52-启动方式)
  - [5.3 交互模式](#53-交互模式)
- [6. 工具集总览](#6-工具集总览)
- [7. 如何添加新的 Agent](#7-如何添加新的-agent)
- [8. 依赖与环境要求](#8-依赖与环境要求)
- [9. 版本历史](#9-版本历史)

---

## 1. 项目概述

本项目是一个**基于大语言模型的多智能体协作系统**，采用 **RouterAgent 路由调度架构**。系统核心思想是：

- **单一入口**：所有用户请求统一由 `main.py` 接收
- **智能路由**：`RouterAgent` 评估任务类型，自动分派给最合适的子 Agent
- **专业分工**：每个子 Agent 专注于特定领域（编程、数据库、代码审查、需求分析）
- **独立上下文**：每个 Agent 维护自己独立的 `messages` 上下文列表，最大化 LLM Cache Hit
- **工具驱动**：每个 Agent 绑定专属工具集，通过工具调用完成具体操作

### 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 **多智能体协作** | 5 个专业 Agent 协同工作，各司其职 |
| 🚦 **智能路由** | RouterAgent 自动评估任务类型并分派 |
| 🛡️ **安全沙盒** | 所有文件操作限制在安全目录内 |
| ⏱️ **超时保护** | LLM 调用、工具调用、交互输入三重超时保护 |
| 🔄 **自动重试** | 指数退避策略，提升系统稳定性 |
| 📐 **高低水位线** | 智能截断历史消息，防止 Token 溢出 |
| 🧠 **记忆管理** | 跨会话持久化存档，支持检索 |
| 📋 **计划管理** | 自动生成和跟踪 plan.md 开发计划 |

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                       用户输入                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     main.py (入口)                           │
│              run_multi_agent(user_task)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐  │
│  │              RouterAgent (路由调度核心)                │  │
│  │                                                       │  │
│  │  职责：评估任务 → 选择子 Agent → 转发 → 汇总结果      │  │
│  │                                                       │  │
│  │  工具：delegate_task(target_agent, task_context)       │  │
│  └──────┬──────────┬──────────┬──────────┬───────────────┘  │
│         │          │          │          │                   │
│         ▼          ▼          ▼          ▼                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐      │
│  │PMAgent  │ │CoderAgent│ │DBAAgent │ │ReviewerAgent │      │
│  │产品经理 │ │ 编程专家 │ │数据库专家│ │ 代码审查专家 │      │
│  └─────────┘ └─────────┘ └─────────┘ └──────────────┘      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   core/ (核心层)                       │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │  │
│  │  │config.py │ │  llm.py  │ │ utils.py │ │memory  │  │  │
│  │  │ 安全配置 │ │ LLM初始化 │ │ 工具函数 │ │ 记忆管理│  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  tools/ (工具层)                       │  │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐  │  │
│  │  │file_tools│ │ git_tools│ │db_tools│ │data_tools│  │  │
│  │  │ 文件操作 │ │版本控制  │ │数据库  │ │数据格式  │  │  │
│  │  └──────────┘ └──────────┘ └────────┘ └──────────┘  │  │
│  │  ┌──────────┐ ┌────────────┐                        │  │
│  │  │search    │ │memory_tools│                        │  │
│  │  │ 搜索工具 │ │ 记忆管理   │                        │  │
│  │  └──────────┘ └────────────┘                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 架构分层说明

| 层级 | 目录 | 说明 |
|------|------|------|
| **入口层** | `main.py` | 系统启动入口，初始化所有 Agent，启动交互循环 |
| **Agent 层** | `agents/` | 5 个智能体，每个独立维护上下文和工具集 |
| **核心层** | `core/` | LLM 初始化、安全配置、工具函数、记忆管理 |
| **工具层** | `tools/` | 具体功能工具（文件、Git、数据库、数据格式、搜索、记忆） |

---

## 3. Agent 角色与职责

### 3.1 RouterAgent — 路由调度核心

**文件**: `agents/router_agent.py`

**角色**: 系统的"大脑"和"调度员"，负责接收用户输入并决定由哪个子 Agent 处理。

**核心职责**:
- 评估用户任务类型
- 使用 `delegate_task` 工具将任务转发给对应的子 Agent
- 收集子 Agent 的处理结果，汇总汇报给用户
- 维护独立的静态 `messages` 上下文列表

**任务分类规则**:

| 任务类型 | 转发目标 | 示例 |
|----------|----------|------|
| 宏观新需求/新项目 | **PMAgent** | "帮我开发一个博客系统" |
| 编程/文件操作 | **CoderAgent** | "帮我写一个排序算法" |
| 数据库任务 | **DBAAgent** | "查询这个数据库的表结构" |
| 代码审查/测试 | **ReviewerAgent** | "检查这段代码的 Bug" |

**关键方法**:
```python
class RouterAgent:
    def __init__(self, coder_agent, dba_agent, reviewer_agent, pm_agent)
    def run(self, user_task, max_steps=500) -> str
    def _handle_delegate(self, target_agent, task_context) -> str
```

---

### 3.2 PMAgent — 技术产品经理

**文件**: `agents/pm_agent.py`

**角色**: 技术产品经理，负责将用户模糊的初始需求转化为可执行的开发步骤。

**核心职责**:
- 拦截用户模糊的初始需求
- 通过逻辑推理将需求转化为可执行的开发步骤
- 强制调用 `plan_progress(action='create')` 生成 `plan.md` 文件
- **绝不写具体代码**，只负责制定严谨的计划

**绑定工具**:
- `plan_progress` — 创建/更新开发计划
- `write_local_file` — 写入计划文件

**关键方法**:
```python
class PMAgent:
    def __init__(self)
    def run(self, task_context, max_steps=500) -> str
```

---

### 3.3 CoderAgent — 编程智能体

**文件**: `agents/coder_agent.py`

**角色**: 编程专家，处理所有编程相关任务。

**核心职责**:
- 编写高质量的 Python 代码
- 读写文件、创建目录、管理项目结构
- 执行终端命令、安装依赖
- 使用 Git 进行版本管理
- 网络搜索查阅文档

**绑定工具**（最全面的工具集）:

| 类别 | 工具 |
|------|------|
| 📂 文件操作 | `read_local_file`, `read_file_by_lines`, `write_local_file`, `list_directory_tree` |
| 💻 终端命令 | `run_terminal_command`, `pip_install` |
| ✅ 代码质量 | `check_python_syntax`, `code_format_tool`, `search_code_ast`, `grep_search` |
| 🗃️ Git 版本控制 | `git_init_repo`, `git_create_branch`, `git_commit`, `git_diff`, `git_status`, `git_log`, `git_checkout`, `git_branch_list` |
| 🔍 搜索 | `read_webpage`, `web_search` |
| 🧠 记忆管理 | `agent_memory_archive`, `agent_memory_retrieve`, `archive_history_step`, `plan_progress` |
| 📊 数据格式 | `data_format_tool`, `file_backup_tool` |

**关键方法**:
```python
class CoderAgent:
    def __init__(self)
    def run(self, task_context, max_steps=500) -> str
```

---

### 3.4 DBAAgent — 数据库与数据格式智能体

**文件**: `agents/dba_agent.py`

**角色**: 数据库与数据格式专家，处理所有数据库探查和数据格式转换任务。

**核心职责**:
- 连接 SQLite/MySQL 数据库，分析表结构和数据
- 解析、验证、格式化 JSON/CSV/YAML 数据
- 格式互转（JSON ↔ CSV, JSON ↔ YAML）
- 按路径查询 JSON/YAML 数据
- 文件备份与恢复

**绑定工具**:

| 类别 | 工具 |
|------|------|
| 🗄️ 数据库 | `inspect_database`（支持 SQLite 和 MySQL） |
| 📊 数据格式 | `data_format_tool`, `file_backup_tool`, `code_format_tool` |
| 📂 文件读取 | `read_local_file`, `read_file_by_lines`, `write_local_file`, `list_directory_tree`, `grep_search` |
| 🧠 记忆管理 | `agent_memory_archive`, `agent_memory_retrieve`, `archive_history_step`, `plan_progress` |

**关键方法**:
```python
class DBAAgent:
    def __init__(self)
    def run(self, task_context, max_steps=500) -> str
```

---

### 3.5 ReviewerAgent — 代码审查与测试智能体

**文件**: `agents/reviewer_agent.py`

**角色**: 严苛的代码审查与测试专家。

**核心职责**:
- 代码格式化（使用 `code_format_tool`）
- Python 语法检查（使用 `check_python_syntax`）
- 编写 pytest 单元测试用例
- 运行 pytest 测试
- 发现 Bug 并明确指出位置、原因和修复建议

**工作流程**:
```
接收代码 → 格式化 → 语法检查 → 编写测试 → 运行测试 → 报告结果
```

**绑定工具**:
- `code_format_tool` — 代码格式化与质量检查
- `check_python_syntax` — Python 语法检查
- `write_local_file` — 写入测试文件
- `run_terminal_command` — 运行 pytest

**关键方法**:
```python
class ReviewerAgent:
    def __init__(self)
    def run(self, task_context, max_steps=500) -> str
```

---

## 4. 项目结构

```
D:\ai_workspace\v41\
│
├── main.py                          # 🚀 系统入口，多智能体路由启动
├── AGENT_README.md                  # 📖 本文档
├── .env                             # 🔑 环境变量（API Key 等）
├── __init__.py                      # Python 包标记
│
├── agents/                          # 🤖 Agent 层
│   ├── __init__.py                  #   导出所有 Agent 类
│   ├── router_agent.py              #   🚦 路由调度核心
│   ├── pm_agent.py                  #   📋 产品经理智能体
│   ├── coder_agent.py               #   💻 编程智能体
│   ├── dba_agent.py                 #   🗄️ 数据库智能体
│   └── reviewer_agent.py            #   🔍 代码审查智能体
│
├── core/                            # ⚙️ 核心层
│   ├── __init__.py                  #   导出核心模块
│   ├── config.py                    #   🔒 安全策略与全局配置
│   ├── llm.py                       #   🤖 LLM 初始化
│   ├── utils.py                     #   🔧 辅助函数
│   └── agent_memory.py              #   🧠 记忆管理器
│
├── tools/                           # 🛠️ 工具层
│   ├── __init__.py                  #   导出所有工具
│   ├── file_tools.py                #   📂 文件操作工具
│   ├── git_tools.py                 #   🗃️ Git 版本控制工具
│   ├── db_tools.py                  #   🗄️ 数据库探查工具
│   ├── data_tools.py                #   📊 数据格式处理工具
│   ├── search_tools.py              #   🔍 网络搜索工具
│   └── memory_tools.py              #   🧠 记忆管理工具
│
└── agent_history_archive/           # 📦 记忆存档目录（自动生成）
    └── memory_index.json            #   记忆索引文件
```

---

## 5. 各 Agent 的配置与使用

### 5.1 环境配置

#### 1. API Key 配置

在项目根目录的 `.env` 文件中配置：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here
```

> **注意**：当前系统主要使用 DeepSeek Chat 模型（`deepseek-chat`），通过 `core/llm.py` 中的 `init_llm()` 函数初始化。

#### 2. Python 环境配置

在 `core/config.py` 中配置 pip 路径（用于 `pip_install` 工具）：

```python
PIP_PYTHON_EXE = r"D:\ProgramData\anaconda3\envs\ai_agent\python.exe"
PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

#### 3. 安全目录配置

所有文件操作默认限制在项目根目录内，由 `SAFE_BASE_DIR` 控制：

```python
SAFE_BASE_DIR = os.path.abspath(os.getcwd())  # 默认为项目根目录
```

### 5.2 启动方式

#### 方式一：命令行直接传参

```bash
python main.py "请帮我检查当前目录下的 Python 文件"
```

#### 方式二：交互式模式

```bash
python main.py
```

进入交互模式后：
- **多行输入**：连续两次回车（空行）自动提交
- **结束标记**：输入单独一行 `EOF` 结束输入
- **退出程序**：输入单独一行 `q` 或 `quit` 或 `exit`
- **超时保护**：输入超时 300 秒自动使用默认任务

### 5.3 交互模式示例

```
🚀 企业级多智能体路由系统 v37.0
🔒 安全目录: D:\ai_workspace\v41
📋 架构: RouterAgent → [CoderAgent | DBAAgent]

--------------------------------------------------
  [多行输入模式]
  - 输入单独一行 EOF 结束
  - 连续两次回车(空行)自动提交
  - 输入 q 单独一行退出程序
--------------------------------------------------

> 帮我分析这个项目的代码结构
> （空行两次提交）
```

---

## 6. 工具集总览

| 工具函数 | 所属模块 | 说明 |
|----------|----------|------|
| `read_local_file` | file_tools | 读取小文件全文（自动检测编码） |
| `read_file_by_lines` | file_tools | 按行读取大文件 |
| `write_local_file` | file_tools | 写入/创建文件（自动备份） |
| `list_directory_tree` | file_tools | 列出目录结构树 |
| `run_terminal_command` | file_tools | 执行终端命令 |
| `pip_install` | file_tools | 安装 Python 包 |
| `check_python_syntax` | file_tools | Python 语法检查 |
| `search_code_ast` | file_tools | AST 解析源码 |
| `grep_search` | file_tools | 文本搜索 |
| `git_init_repo` | git_tools | 初始化 Git 仓库 |
| `git_create_branch` | git_tools | 创建并切换分支 |
| `git_commit` | git_tools | 提交更改 |
| `git_diff` | git_tools | 查看差异 |
| `git_status` | git_tools | 查看状态 |
| `git_log` | git_tools | 查看提交历史 |
| `git_checkout` | git_tools | 切换分支 |
| `git_branch_list` | git_tools | 列出分支 |
| `inspect_database` | db_tools | 探查 SQLite/MySQL 数据库 |
| `data_format_tool` | data_tools | JSON/CSV/YAML 格式处理 |
| `file_backup_tool` | data_tools | 文件备份与恢复 |
| `code_format_tool` | data_tools | 代码格式化与质量检查 |
| `read_webpage` | search_tools | 抓取网页内容 |
| `web_search` | search_tools | 网络搜索 |
| `agent_memory_archive` | memory_tools | 记忆存档 |
| `agent_memory_retrieve` | memory_tools | 记忆检索 |
| `archive_history_step` | memory_tools | 历史步骤存档 |
| `plan_progress` | memory_tools | 计划管理 |

---

## 7. 如何添加新的 Agent

### 步骤一：创建 Agent 文件

在 `agents/` 目录下创建新的 Agent 类文件，例如 `agents/data_agent.py`：

```python
"""
=====================================================================
 📊 DataAgent - 数据分析智能体 (v41.0)
 
 职责：
   - 处理数据分析相关任务
   - 绑定数据分析相关工具
   - 维护自己独立且绝对静态的 messages 上下文列表
=====================================================================
"""

import os
import sys
import time

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.config import DEFAULT_MAX_STEPS, LLM_TIMEOUT, MAX_RETRIES, MAX_RETRY_DELAY, logger
from core.llm import init_llm
from core.utils import _apply_watermark_truncation, _TimeoutError, _execute_with_timeout
from tools import (
    read_local_file, write_local_file, run_terminal_command,
    data_format_tool, agent_memory_archive, agent_memory_retrieve,
)


class DataAgent:
    """数据分析智能体"""
    
    SYSTEM_PROMPT = """你是一个数据分析智能体（DataAgent），你的职责是：
    
## 核心职责
1. 读取和分析数据文件
2. 进行数据统计和可视化
3. 生成数据分析报告

## 可用工具
- read_local_file, write_local_file
- run_terminal_command
- data_format_tool
- agent_memory_archive, agent_memory_retrieve

## 工作流程
1. 分析任务上下文
2. 选择合适的工具逐步执行
3. 任务完成后输出"【任务完成】"
"""

    def __init__(self):
        self.name = "DataAgent"
        self.llm = init_llm()
        self.data_tools = [
            read_local_file, write_local_file,
            run_terminal_command,
            data_format_tool,
            agent_memory_archive, agent_memory_retrieve,
        ]
        self.llm_with_tools = self.llm.bind_tools(self.data_tools)
        self.messages = [SystemMessage(content=self.SYSTEM_PROMPT)]
    
    def run(self, task_context, max_steps=DEFAULT_MAX_STEPS):
        # ... 参照其他 Agent 的 run 方法实现
        pass
```

### 步骤二：注册到 `__init__.py`

在 `agents/__init__.py` 中导出新 Agent：

```python
from .router_agent import RouterAgent
from .coder_agent import CoderAgent
from .dba_agent import DBAAgent
from .reviewer_agent import ReviewerAgent
from .pm_agent import PMAgent
from .data_agent import DataAgent  # ← 新增
```

### 步骤三：注册到 RouterAgent

在 `agents/router_agent.py` 中：

1. **导入新 Agent**（可选，RouterAgent 的 system prompt 中已包含引用）
2. **在 `__init__` 方法中添加参数**：
   ```python
   def __init__(self, coder_agent=None, dba_agent=None, reviewer_agent=None, pm_agent=None, data_agent=None):
       self.data_agent = data_agent
   ```
3. **在 `_handle_delegate` 方法中添加路由逻辑**：
   ```python
   elif target_agent == "DataAgent" and self.data_agent:
       result = self.data_agent.run(task_context)
       self._last_result = result
       return result
   ```
4. **更新 `ROUTER_SYSTEM_PROMPT`**，添加新 Agent 的描述和路由规则

### 步骤四：在 `main.py` 中初始化

```python
from agents.data_agent import DataAgent

def run_multi_agent(user_task, max_steps=DEFAULT_MAX_STEPS):
    coder_agent = CoderAgent()
    dba_agent = DBAAgent()
    data_agent = DataAgent()  # ← 新增
    
    router = RouterAgent(
        coder_agent=coder_agent,
        dba_agent=dba_agent,
        data_agent=data_agent  # ← 新增
    )
    # ...
```

---

## 8. 依赖与环境要求

### 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows / Linux / macOS |
| Python | 3.8+（推荐 3.10） |
| 网络 | 需要访问 DeepSeek API（api.deepseek.com） |

### Python 依赖

| 包名 | 用途 | 安装命令 |
|------|------|----------|
| `langchain-core` | LangChain 核心框架 | `pip install langchain-core` |
| `langchain-openai` | OpenAI 兼容接口（DeepSeek） | `pip install langchain-openai` |
| `python-dotenv` | 环境变量加载 | `pip install python-dotenv` |
| `requests` | HTTP 请求 | `pip install requests` |
| `beautifulsoup4` | 网页解析 | `pip install beautifulsoup4` |
| `pymysql` | MySQL 连接（可选） | `pip install pymysql` |
| `pyyaml` | YAML 解析（可选） | `pip install pyyaml` |
| `autopep8` | 代码格式化（可选） | `pip install autopep8` |
| `flake8` | 代码质量检查（可选） | `pip install flake8` |
| `pytest` | 单元测试（可选） | `pip install pytest` |

### 一键安装

```bash
pip install langchain-core langchain-openai python-dotenv requests beautifulsoup4
# 可选依赖
pip install pymysql pyyaml autopep8 flake8 pytest
```

### 环境变量

创建 `.env` 文件（已提供模板）：

```env
DEEPSEEK_API_KEY=sk-your_deepseek_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here
```

---

## 9. 版本历史

| 版本 | 主要更新 |
|------|----------|
| v37.0 | 多智能体路由架构初始版，RouterAgent + CoderAgent + DBAAgent |
| v38.0 | 新增 ReviewerAgent（代码审查与测试） |
| v39.0 | 新增 PMAgent（技术产品经理），完善路由规则 |
| v40.0 | 系统稳定性增强，超时保护、自动重试、看门狗机制 |
| v41.0 | 架构优化，各 Agent 独立上下文管理，工具集完善 |

---

> **📌 提示**：本文档由 CoderAgent 自动生成，基于对项目源代码的静态分析。如有与实际代码不符之处，请以源代码为准。
