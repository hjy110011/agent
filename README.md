# 🚀 企业级多智能体路由系统 v44.0

> **架构**: RouterAgent → [PMAgent | CoderAgent | DBAAgent | ReviewerAgent]  
> **核心**: 基于 LangChain + DeepSeek Chat 的多智能体协作框架  
> **安全**: 文件操作沙盒隔离 + 高危命令黑名单拦截

---

## 📖 项目概述

本项目是一个**多智能体路由系统**，由 5 个各司其职的 AI 智能体组成，通过**路由调度**协作完成用户任务：

| 智能体 | 角色 | 核心职责 |
|--------|------|----------|
| **RouterAgent** | 🚦 路由调度核心 | 评估用户任务类型，转发给最合适的子 Agent |
| **PMAgent** | 📋 技术产品经理 | 将模糊需求转化为可执行的开发计划（plan.md） |
| **CoderAgent** | 💻 编程智能体 | 编写代码、文件操作、运行命令、Git 版本控制 |
| **DBAAgent** | 🗄️ 数据库智能体 | 探查数据库结构、数据格式转换（JSON/CSV/YAML） |
| **ReviewerAgent** | 🔍 代码审查专家 | 代码格式化、语法检查、编写并运行 pytest 测试 |

**核心设计理念**：
- 每个子 Agent 维护**独立且绝对静态**的 messages 上下文列表，最大化 LLM Cache Hit
- 所有文件操作限制在**安全基目录**内，高危命令被黑名单拦截
- 支持**三重超时保护**：LLM 调用 + 工具调用 + 交互输入
- 内置**记忆管理系统**（本地文件 + ChromaDB 向量数据库），支持跨会话持久化

---

## 📂 项目结构

```
D:\ai_workspace\v44/
│
├── main.py                      # 🚀 主程序入口 - 多智能体路由启动器
├── .env                         # 🔑 环境变量（API Key 配置）
├── plan.md                      # 📋 PMAgent 生成的开发计划（运行时自动生成）
│
├── agents/                      # 🤖 智能体模块
│   ├── __init__.py              #   包导出
│   ├── router_agent.py          #   🚦 RouterAgent - 路由调度核心
│   ├── coder_agent.py           #   💻 CoderAgent - 编程/文件操作
│   ├── pm_agent.py              #   📋 PMAgent - 技术产品经理
│   ├── dba_agent.py             #   🗄️ DBAAgent - 数据库/数据格式
│   └── reviewer_agent.py        #   🔍 ReviewerAgent - 代码审查/测试
│
├── core/                        # ⚙️ 核心基础设施
│   ├── __init__.py              #   包导出（统一暴露核心模块）
│   ├── config.py                #   🔒 安全策略与全局配置
│   ├── llm.py                   #   🤖 大模型初始化（DeepSeek Chat）
│   ├── utils.py                 #   🔧 辅助函数（截断/超时/路径检查）
│   └── agent_memory.py          #   🧠 记忆管理器（本地存档 + ChromaDB）
│
├── tools/                       # 🛠️ 工具集（LangChain Tool 装饰器）
│   ├── __init__.py              #   包导出（统一注册所有工具）
│   ├── file_tools.py            #   📂 文件操作（读/写/执行命令/搜索）
│   ├── git_tools.py             #   🗃️ Git 版本控制（init/branch/commit/diff/log）
│   ├── db_tools.py              #   🗄️ 数据库探查（SQLite + MySQL）
│   ├── data_tools.py            #   📊 数据格式（JSON/CSV/YAML 解析转换 + 备份 + 代码格式化）
│   ├── search_tools.py          #   🔍 网络搜索（DuckDuckGo + 网页抓取）
│   ├── memory_tools.py          #   🧠 记忆管理（存档/检索/计划管理/语义搜索）
│   ├── api_tools.py             #   🌐 API 调试（类似 Postman 的 HTTP 请求）
│   └── browser_tools.py         #   🕸️ 动态网页抓取（Playwright 无头浏览器）
│
├── agent_history_archive/       # 📦 记忆存档目录（运行时自动生成）
│   └── memory_index.json        #   记忆索引文件
│
├── agent_vector_db/             # 🔢 ChromaDB 向量数据库（运行时自动生成）
│   └── chroma.sqlite3           #   向量存储文件
│
└── .agent_backups/              # 📂 文件备份目录（运行时自动生成）
```

---

## 🔧 环境要求与安装步骤

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | ≥ 3.10 | 推荐 3.10 - 3.12 |
| DeepSeek API Key | 有效 | 用于调用大模型 |
| Git | 任意版本 | 可选，用于版本控制功能 |

### 安装步骤

#### 1️⃣ 克隆/进入项目目录

```bash
cd D:\ai_workspace\v44
```

#### 2️⃣ 创建虚拟环境（推荐）

```bash
# 使用 conda
conda create -n ai_agent python=3.10
conda activate ai_agent

# 或使用 venv
python -m venv venv
venv\Scripts\activate
```

#### 3️⃣ 安装核心依赖

```bash
pip install langchain langchain-openai langchain-core python-dotenv requests beautifulsoup4 chardet
```

#### 4️⃣ 安装可选依赖（按需）

```bash
# ChromaDB 向量记忆（推荐）
pip install chromadb

# Playwright 动态网页抓取
pip install playwright
playwright install chromium

# 数据库探查（MySQL）
pip install pymysql

# YAML 格式支持
pip install pyyaml

# 代码质量检查
pip install flake8 autopep8

# 网络搜索
pip install duckduckgo_search
```

#### 5️⃣ 配置 API Key

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
ZHIPU_API_KEY=your-zhipu-api-key-here
```

> ⚠️ **注意**：当前系统主要使用 `DEEPSEEK_API_KEY`（DeepSeek Chat 模型），`ZHIPU_API_KEY` 为预留字段。

---

## ⚙️ 配置说明

所有全局配置集中在 `core/config.py` 中，关键配置项如下：

### 安全策略

```python
# 安全基目录：所有文件操作限制在此目录内
SAFE_BASE_DIR = os.path.abspath(os.getcwd())  # 默认为项目根目录

# 高危命令黑名单（匹配即拦截）
DANGEROUS_COMMANDS = [
    r"rm\s+-r", r"del\s+/s", r"format\s+", r"sudo\s+",
    r"chmod\s+-R\s+777", r"shutdown", r"reboot", ...
]
```

### 超时与重试

```python
MAX_OUTPUT_LENGTH = 20000      # 输出截断长度（字符）
MAX_RETRIES = 3                # 工具调用最大重试次数
SEARCH_TIMEOUT = 15            # 网络请求超时（秒）
DEFAULT_MAX_STEPS = 500        # Agent 最大循环步数
LLM_TIMEOUT = 120              # LLM 调用超时（秒）
MAX_RETRY_DELAY = 30           # 最大重试延迟（秒）
```

### pip 安装配置

```python
PIP_PYTHON_EXE = r"D:\ProgramData\anaconda3\envs\ai_agent\python.exe"  # 你的 Python 路径
PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"             # 清华源镜像
```

> 💡 **修改建议**：将 `PIP_PYTHON_EXE` 改为你实际使用的 Python 解释器路径。

---

## 🚀 使用方法

### 方式一：命令行直接运行

```bash
# 直接传入任务
python main.py "请帮我检查当前目录下的 Python 文件"

# 传入复杂任务
python main.py "创建一个 Flask Web 应用，包含用户登录功能"
```

### 方式二：交互式模式

```bash
python main.py
```

进入交互模式后：
- **多行输入**：连续两次回车（空行）自动提交
- **结束标记**：输入单独一行 `EOF` 结束输入
- **退出程序**：输入 `q` 或 `quit` 或 `exit`
- **超时保护**：300 秒无输入自动使用默认任务

### 运行示例

```
🚀 企业级多智能体路由系统 v44.0
🔒 安全目录: D:\ai_workspace\v44
📋 架构: RouterAgent → [PMAgent | CoderAgent | DBAAgent | ReviewerAgent]
============================================================

  [多行输入模式]
  - 输入单独一行 EOF 结束
  - 连续两次回车(空行)自动提交
  - 输入 q 单独一行退出程序
------------------------------------------------------------

> 请帮我分析当前目录下的 Python 代码质量
> （连续两次回车提交）

============================================================
[🤖 多智能体路由系统 (v37.0) 已启动]
📋 任务: 请帮我分析当前目录下的 Python 代码质量
============================================================

[系统] 初始化子智能体...
[系统] PMAgent ✅ 已就绪
[系统] CoderAgent ✅ 已就绪
[系统] DBAAgent ✅ 已就绪
[系统] ReviewerAgent ✅ 已就绪
[系统] RouterAgent ✅ 已就绪
============================================================

[🚦 RouterAgent] 已接收任务，开始评估路由...
...
```

---

## 🧩 各模块功能详解

### 1️⃣ `main.py` — 主程序入口

**实际逻辑**：
1. 从 `.env` 加载 API Key
2. 初始化 4 个子 Agent（PMAgent、CoderAgent、DBAAgent、ReviewerAgent）
3. 初始化 RouterAgent，传入所有子 Agent 引用
4. 调用 `router.run(user_task)` 开始路由调度
5. 支持命令行参数和交互式两种模式
6. 交互模式使用 `_input_with_timeout()` 替代 `input()`，防止 stdin 阻塞

**关键函数**：
- `run_multi_agent(user_task, max_steps)` — 多智能体路由入口

---

### 2️⃣ `agents/router_agent.py` — 路由调度核心

**实际逻辑**：
- 维护独立的 `messages` 上下文列表（SystemMessage + 历史对话）
- 通过 `delegate_task` 工具将任务转发给子 Agent
- 主循环中执行：LLM 调用 → 解析 tool_calls → 执行工具 → 收集结果
- 支持**高低水位线截断**（超过 70 条消息时截断到 25 条，保留成对的 tool_calls 与 ToolMessage）
- 支持**指数退避重试**（LLM 调用失败时，延迟 2→4→8→...→30 秒重试）
- 支持**看门狗超时**（单轮执行超过 `LLM_TIMEOUT * 3 + 60` 秒时强制跳过）

**路由规则**：
| 任务类型 | 转发目标 |
|---------|---------|
| 宏观新需求/新项目 | → PMAgent（前置拆解） |
| 编程/文件操作 | → CoderAgent |
| 数据库/数据格式 | → DBAAgent |
| 代码审查/测试 | → ReviewerAgent |

---

### 3️⃣ `agents/coder_agent.py` — 编程智能体

**实际逻辑**：
- 绑定**最全的工具集**（约 25 个工具），涵盖文件操作、终端命令、Git、搜索、记忆等
- 主循环与 RouterAgent 相同模式：LLM 调用 → 工具执行 → 结果收集
- 检测到 `【任务完成】` 标记时结束循环

**绑定的工具**：
| 类别 | 工具 |
|------|------|
| 📂 文件操作 | `read_local_file`, `read_file_by_lines`, `write_local_file`, `list_directory_tree` |
| 💻 终端 | `run_terminal_command`, `pip_install` |
| ✅ 代码质量 | `check_python_syntax`, `code_format_tool`, `search_code_ast`, `grep_search` |
| 🗃️ Git | `git_init_repo`, `git_create_branch`, `git_commit`, `git_diff`, `git_status`, `git_log`, `git_checkout`, `git_branch_list` |
| 🔍 搜索 | `read_webpage`, `web_search` |
| 🧠 记忆 | `agent_memory_archive`, `agent_memory_retrieve`, `archive_history_step`, `plan_progress`, `semantic_search_memory` |
| 📊 数据 | `data_format_tool`, `file_backup_tool` |
| 🌐 API | `send_api_request` |
| 🕸️ 网页 | `fetch_dynamic_webpage` |

---

### 4️⃣ `agents/pm_agent.py` — 技术产品经理

**实际逻辑**：
- 系统提示词极简："你是一名资深的技术产品经理..."
- 仅绑定 2 个工具：`plan_progress` 和 `write_local_file`
- **绝不写具体代码**，只负责制定严谨的计划
- 强制调用 `plan_progress(action='create')` 生成 `plan.md` 文件
- 如果 LLM 没有调用工具，系统会提示"请调用 plan_progress 工具生成 plan.md"

---

### 5️⃣ `agents/dba_agent.py` — 数据库智能体

**实际逻辑**：
- 绑定数据库探查工具 + 数据格式处理工具 + 文件读取工具
- 支持 SQLite 和 MySQL 两种数据库
- 支持 JSON/CSV/YAML 三种数据格式的解析、验证、格式化、查询、互转
- 支持文件备份与恢复

**绑定的工具**：
| 类别 | 工具 |
|------|------|
| 🗄️ 数据库 | `inspect_database`（SQLite + MySQL） |
| 📊 数据格式 | `data_format_tool`, `file_backup_tool`, `code_format_tool` |
| 📂 文件 | `read_local_file`, `read_file_by_lines`, `write_local_file`, `list_directory_tree`, `grep_search` |
| 🧠 记忆 | `agent_memory_archive`, `agent_memory_retrieve`, `archive_history_step`, `plan_progress` |

---

### 6️⃣ `agents/reviewer_agent.py` — 代码审查专家

**实际逻辑**：
- 系统提示词要求：**先格式化 → 再语法检查 → 再写 pytest 测试 → 再运行测试 → 最后报告 Bug**
- 绑定代码审查相关工具 + API 调试 + 网页抓取 + 记忆检索
- 测试文件命名格式：`test_<被测试文件名>.py`
- 发现 Bug 必须明确指出位置、原因和修复建议

**绑定的工具**：
| 类别 | 工具 |
|------|------|
| ✅ 代码质量 | `code_format_tool`, `check_python_syntax` |
| 📂 文件 | `write_local_file` |
| 💻 终端 | `run_terminal_command` |
| 🌐 API | `send_api_request` |
| 🕸️ 网页 | `fetch_dynamic_webpage` |
| 🧠 记忆 | `semantic_search_memory` |

---

### 7️⃣ `core/` — 核心基础设施

#### `core/config.py` — 安全策略与全局配置
- 定义安全基目录、高危命令黑名单、超时时间、重试次数等
- 配置 pip 安装路径和镜像源
- 配置 Git 可执行文件路径
- 配置备份目录

#### `core/llm.py` — 大模型初始化
- 从 `.env` 读取 `DEEPSEEK_API_KEY`
- 初始化 `ChatOpenAI` 实例，连接 DeepSeek Chat API
- 模型参数：`temperature=0.2`, `max_tokens=50000`, `timeout=120`
- `build_system_prompt()` 构建包含所有工具说明的系统提示词

#### `core/utils.py` — 辅助函数
| 函数 | 功能 |
|------|------|
| `_truncate_output(text, max_len)` | 截断过长输出文本 |
| `_safe_path_check(target_path)` | 检查路径是否在安全目录内 |
| `_decode_terminal_bytes(raw_bytes)` | 智能解码终端输出（UTF-8/GBK） |
| `_format_size(size_bytes)` | 字节数格式化为人类可读（B/KB/MB/GB） |
| `_apply_watermark_truncation(messages)` | 高低水位线截断（70→25条） |
| `_execute_with_timeout(func, timeout)` | 带超时保护的函数执行器 |
| `_input_with_timeout(prompt, timeout)` | 带超时保护的交互式输入 |

#### `core/agent_memory.py` — 记忆管理器
- 将关键信息压缩存档到 `agent_history_archive/` 目录
- 支持 6 种分类：`step`, `tool`, `logic`, `config`, `error`, `snapshot`
- 自动压缩长文本为摘要（保留开头+结尾关键信息）
- 集成 ChromaDB 向量数据库，支持语义搜索
- 自动清理旧存档（超过阈值自动触发）

---

### 8️⃣ `tools/` — 工具集详解

#### `tools/file_tools.py` — 文件操作工具
| 工具 | 功能 | 安全机制 |
|------|------|---------|
| `read_local_file` | 读取小文件全文（≤500KB） | 越权拦截、编码自动检测 |
| `read_file_by_lines` | 按行读取大文件 | 智能行号校验、导航提示 |
| `write_local_file` | 写入/创建文件 | 越权拦截、自动备份(.bak)、50MB限制 |
| `run_terminal_command` | 执行终端命令 | 高危命令黑名单、30秒超时 |
| `list_directory_tree` | 列出目录结构 | 深度控制、通配符过滤 |
| `pip_install` | 安装 Python 包 | 清华源镜像、自动重试 |
| `check_python_syntax` | 检查 Python 语法 | ast.parse + flake8 双重检查 |
| `search_code_ast` | AST 解析源码 | 支持搜索类/函数/变量/导入 |
| `grep_search` | 文本搜索 | 支持正则、上下文行 |

#### `tools/git_tools.py` — Git 版本控制
| 工具 | 功能 |
|------|------|
| `git_init_repo` | 初始化 Git 仓库 |
| `git_create_branch` | 创建并切换到新分支 |
| `git_commit` | 暂存并提交更改 |
| `git_diff` | 查看工作区差异 |
| `git_status` | 查看仓库状态 |
| `git_log` | 查看提交历史 |
| `git_checkout` | 切换分支 |
| `git_branch_list` | 列出所有本地分支 |

#### `tools/db_tools.py` — 数据库探查
| 工具 | 功能 |
|------|------|
| `inspect_database` | 探查数据库结构（SQLite/MySQL） |
| `_inspect_sqlite` | SQLite 探查：表名、列名、类型、约束、行数 |
| `_inspect_mysql` | MySQL 探查：同上，需 pymysql |

#### `tools/data_tools.py` — 数据格式处理
| 工具 | 功能 |
|------|------|
| `data_format_tool` | JSON/CSV/YAML 解析、验证、格式化、查询、互转 |
| `file_backup_tool` | 文件备份、版本列表、恢复、差异对比 |
| `code_format_tool` | 代码格式化(autopep8)、质量检查(flake8)、指标统计 |

#### `tools/search_tools.py` — 网络搜索
| 工具 | 功能 |
|------|------|
| `read_webpage` | requests + BeautifulSoup 抓取网页正文 |
| `web_search` | DuckDuckGo 搜索（支持多引擎回退） |

#### `tools/memory_tools.py` — 记忆管理
| 工具 | 功能 |
|------|------|
| `agent_memory_archive` | 将关键信息存档到本地 |
| `agent_memory_retrieve` | 从存档中检索信息 |
| `archive_history_step` | 将功能核心逻辑压缩为快照存档 |
| `plan_progress` | 管理 plan.md 的读写和进度更新 |
| `semantic_search_memory` | 通过自然语言语义搜索历史记忆 |

#### `tools/api_tools.py` — API 调试
| 工具 | 功能 |
|------|------|
| `send_api_request` | 发送 HTTP 请求（GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS） |
| 特性 | 自动 JSON 解析、超时处理、状态码文本描述、curl 命令转换 |

#### `tools/browser_tools.py` — 动态网页抓取
| 工具 | 功能 |
|------|------|
| `fetch_dynamic_webpage` | Playwright 无头浏览器渲染 JS 动态内容 |
| 特性 | 可配置等待时间、视口大小、User-Agent、HTML 清洗提取纯文本 |

---

## 🔄 工作流程

```
用户输入任务
     │
     ▼
┌─────────────────────────────────────────────────┐
│  RouterAgent 评估任务类型                        │
│  (LLM 分析 + delegate_task 工具)                 │
└─────────────────────────────────────────────────┘
     │
     ├── 宏观新需求/新项目 ──► PMAgent ──► 生成 plan.md
     │
     ├── 编程/文件操作 ──────► CoderAgent ──► 编写代码/运行命令
     │
     ├── 数据库/数据格式 ────► DBAAgent ──► 探查数据库/转换格式
     │
     └── 代码审查/测试 ──────► ReviewerAgent ──► 格式化/测试/找 Bug
              │
              ▼
     RouterAgent 收集结果 → 汇报给用户
```

**每个 Agent 的内部循环**：
```
1. LLM 调用（带超时保护 + 指数退避重试）
2. 解析 tool_calls
3. 执行工具（带重试 + 看门狗）
4. 收集结果 → 回到步骤 1
5. 检测到 "【任务完成】" → 退出循环
```

---

## 🛠️ 如何修改和扩展

### 修改配置

编辑 `core/config.py`：
- 修改 `SAFE_BASE_DIR` 改变安全目录范围
- 修改 `DANGEROUS_COMMANDS` 添加/移除高危命令规则
- 修改 `LLM_TIMEOUT` 调整超时时间
- 修改 `PIP_PYTHON_EXE` 指向你的 Python 路径

### 更换大模型

编辑 `core/llm.py` 中的 `init_llm()` 函数：

```python
def init_llm() -> ChatOpenAI:
    # 更换为其他兼容 OpenAI API 的模型
    return ChatOpenAI(
        model="gpt-4",                    # 更换模型名
        api_key="your-api-key",           # 更换 API Key
        base_url="https://api.openai.com/v1",  # 更换 API 地址
        max_tokens=50000,
        temperature=0.2,
        timeout=LLM_TIMEOUT,
        max_retries=2,
    )
```

### 添加新工具

1. 在 `tools/` 下创建新的工具文件（如 `tools/my_tools.py`）
2. 使用 `@tool` 装饰器定义工具函数：

```python
from langchain_core.tools import tool

@tool
def my_new_tool(param1: str, param2: int = 10) -> str:
    """
    工具描述（LLM 会读取此描述来决定何时调用）。

    Args:
        param1: 参数1说明
        param2: 参数2说明，默认10

    Returns:
        str: 返回结果说明
    """
    # 你的工具逻辑
    return f"处理结果: {param1} x {param2}"
```

3. 在 `tools/__init__.py` 中导入并添加到 `all_tools` 列表
4. 在对应 Agent 的 `__init__` 方法中将工具添加到 `self.xxx_tools` 列表

### 添加新 Agent

1. 在 `agents/` 下创建新文件（如 `agents/my_agent.py`）
2. 继承 Agent 模式（参考 `CoderAgent` 的结构）：

```python
from core.llm import init_llm
from core.config import DEFAULT_MAX_STEPS, LLM_TIMEOUT, MAX_RETRIES, MAX_RETRY_DELAY, logger
from core.utils import _apply_watermark_truncation, _TimeoutError, _execute_with_timeout
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

class MyAgent:
    MY_SYSTEM_PROMPT = """你是一个..."""

    def __init__(self):
        self.name = "MyAgent"
        self.llm = init_llm()
        self.my_tools = [tool1, tool2, ...]
        self.llm_with_tools = self.llm.bind_tools(self.my_tools)
        self.messages = [SystemMessage(content=self.MY_SYSTEM_PROMPT)]

    def run(self, task_context, max_steps=DEFAULT_MAX_STEPS):
        # 主循环逻辑（参考其他 Agent 的 run 方法）
        ...
```

3. 在 `agents/__init__.py` 中导入
4. 在 `main.py` 中初始化新 Agent 并传入 RouterAgent

### 修改 Agent 行为

每个 Agent 的行为由其**系统提示词**（`XXX_SYSTEM_PROMPT`）控制：
- 修改 `CoderAgent.CODER_SYSTEM_PROMPT` 改变编程智能体的行为规则
- 修改 `RouterAgent.ROUTER_SYSTEM_PROMPT` 改变路由规则
- 修改 `ReviewerAgent.REVIEWER_SYSTEM_PROMPT` 改变审查流程

### 调整高低水位线

在 `core/utils.py` 的 `_apply_watermark_truncation` 函数中：
```python
def _apply_watermark_truncation(
    messages: list,
    high_watermark: int = 70,   # 超过此值触发截断
    low_watermark: int = 25     # 保留的最近消息数量
) -> list:
```

---

## ⚠️ 常见问题

### Q: 启动报错 `DEEPSEEK_API_KEY 未设置`
A: 检查 `.env` 文件是否存在，且 `DEEPSEEK_API_KEY` 是否正确填写。

### Q: pip_install 安装失败
A: 检查 `core/config.py` 中的 `PIP_PYTHON_EXE` 是否指向正确的 Python 路径。

### Q: Git 工具报错
A: 确保系统已安装 Git 并加入 PATH 环境变量。

### Q: 交互模式卡住
A: 系统有 300 秒超时保护，超时后会自动使用默认任务。也可以按 `Ctrl+C` 退出。

### Q: 如何查看运行日志？
A: 日志格式为 `2024-01-01 12:00:00 [INFO] 消息内容`，在控制台直接输出。

---

## 📜 版本历史

| 版本 | 特性 |
|------|------|
| v44.0 | 当前版本 - 多智能体路由架构 |
| v42.0 | 新增 API 调试工具（send_api_request） |
| v39.0 | PMAgent 独立，RouterAgent 路由调度 |
| v38.0 | ReviewerAgent 独立 |
| v37.0 | CoderAgent/DBAAgent 独立，子 Agent 独立上下文 |
| v34.0 | 三重超时保护、看门狗机制 |
| v31.0 | 高低水位线截断、指数退避重试 |
| v18.0 | ChromaDB 向量记忆、计划管理 |
| v16.0 | 数据库探查工具 |
