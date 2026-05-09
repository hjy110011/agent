# 🚀 企业级多智能体路由系统 v45.0

> **架构**: RouterAgent → [PMAgent | CoderAgent | DBAAgent | ReviewerAgent]  
> **核心**: 基于 LangChain + DeepSeek Chat 的多智能体协作框架  
> **安全**: 文件操作沙盒隔离 + 高危命令黑名单拦截 + **HITL 人工审批流**

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
- **HITL 人工审批流**：高危操作（写文件、执行命令、Git 变更）需人工确认

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
│   ├── agent_memory.py          #   🧠 记忆管理器（本地存档 + ChromaDB）
│   └── hitl_approval.py         #   ✅ HITL 人工审批拦截器（CLI 交互审批）
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

# HITL 人工审批开关（True=开启，False=关闭）
ENABLE_HITL = True
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
| 📂 文件 | `read_local_file`, `read_file_by_lines`, `write_local_file` |

---

### 6️⃣ `agents/reviewer_agent.py` — 代码审查专家

**实际逻辑**：
- 绑定代码质量工具 + 文件读取工具
- 支持 Python 语法检查、代码格式化、AST 解析、文本搜索
- 支持编写并运行 pytest 测试

**绑定的工具**：
| 类别 | 工具 |
|------|------|
| ✅ 代码质量 | `check_python_syntax`, `code_format_tool`, `search_code_ast`, `grep_search` |
| 📂 文件 | `read_local_file`, `read_file_by_lines`, `list_directory_tree` |
| 💻 终端 | `run_terminal_command`, `pip_install` |

---

## ✅ HITL 人工审批流

### 概述

HITL（Human-In-The-Loop，人在回路）是一种安全机制，当 AI Agent 执行**高危操作**时，系统会暂停执行，在终端弹出审批提示，等待人工确认后才继续执行。

### 触发场景

以下高危操作会触发 HITL 审批：

| 操作类型 | 触发条件 | 审批内容 |
|---------|---------|---------|
| 📝 写文件 | `write_local_file` 被调用 | 显示文件路径、内容预览（前 500 字符） |
| 💻 执行命令 | `run_terminal_command` 被调用 | 显示完整命令字符串 |
| 🗃️ Git 初始化 | `git_init_repo` 被调用 | 显示仓库路径 |
| 🗃️ Git 提交 | `git_commit` 被调用 | 显示提交信息 |
| 🗃️ Git 分支创建 | `git_create_branch` 被调用 | 显示分支名称 |
| 🗃️ Git 分支切换 | `git_checkout` 被调用 | 显示目标分支 |
| 📂 文件恢复 | `file_backup_tool.restore` 被调用 | 显示恢复路径和版本 |
| 📝 代码格式化 | `code_format_tool.format` 被调用 | 显示文件路径 |

### 审批流程

```
AI Agent 调用高危工具
        │
        ▼
┌─────────────────────────────┐
│  HITL 审批拦截器             │
│  ┌───────────────────────┐  │
│  │ ⚠️ 高危操作审批        │  │
│  │ 操作: write_local_file │  │
│  │ 路径: /path/to/file   │  │
│  │ 预览: "..."           │  │
│  │                       │  │
│  │ [Y] 批准  [N] 拒绝    │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
        │
    ┌───┴───┐
    ▼       ▼
  批准     拒绝
    │       │
    ▼       ▼
 执行操作  返回拒绝信息
```

### 配置开关

在 `core/config.py` 中控制：

```python
# 开启 HITL 审批（默认开启）
ENABLE_HITL = True

# 关闭 HITL 审批（跳过人工确认）
ENABLE_HITL = False
```

### 审批交互示例

```
═══════════════════════════════════════════════════════════════
⚠️  HITL 人工审批  ⚠️
═══════════════════════════════════════════════════════════════
操作类型: write_local_file
文件路径: D:\ai_workspace\v44\test_output.py
内容预览 (前 500 字符):
───────────────────────────────────────────────────────────────
print("Hello, World!")
print("This is a test file.")
───────────────────────────────────────────────────────────────
请输入 [Y] 批准 / [N] 拒绝 / [S] 跳过本次 (后续不再拦截同类操作): y
═══════════════════════════════════════════════════════════════
✅ 已批准
═══════════════════════════════════════════════════════════════
```

### 设计要点

1. **非侵入式**：HITL 审批器作为独立模块，通过函数调用集成，不修改 LangChain Tool 的注册逻辑
2. **可开关**：通过 `ENABLE_HITL` 配置项一键开启/关闭
3. **信息透明**：审批时展示完整的操作上下文（路径、内容预览、命令等）
4. **跳过选项**：支持 `[S] 跳过本次`，后续同类操作不再拦截
5. **安全兜底**：即使关闭 HITL，原有的沙盒隔离和黑名单拦截仍然生效

---

## 🛡️ 安全体系

系统采用**三层安全防护**：

| 层级 | 机制 | 说明 |
|------|------|------|
| 🏗️ 第一层 | **沙盒隔离** | 所有文件操作限制在 `SAFE_BASE_DIR` 内 |
| 🚫 第二层 | **黑名单拦截** | 高危命令（rm -rf、format、shutdown 等）自动拦截 |
| 👤 第三层 | **HITL 人工审批** | 高危操作需人工确认（可开关） |

---

## 📜 版本历史

| 版本 | 新增功能 |
|------|---------|
| **v45.0** | **HITL 人工审批流** — 高危操作 CLI 交互审批 |
| v44.0 | 新增动态网页抓取工具（fetch_dynamic_webpage） |
| v43.0 | 新增 API 调试工具（send_api_request） |
| v42.0 | 新增 API 调试工具（send_api_request） |
| v39.0 | PMAgent 独立，RouterAgent 路由调度 |
| v38.0 | ReviewerAgent 独立 |
| v37.0 | CoderAgent/DBAAgent 独立，子 Agent 独立上下文 |
| v34.0 | 三重超时保护、看门狗机制 |
| v31.0 | 高低水位线截断、指数退避重试 |
| v18.0 | ChromaDB 向量记忆、计划管理 |
| v16.0 | 数据库探查工具 |
