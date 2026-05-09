# 🚀 多功能 Agent 系统 (v37.0 多智能体路由版)

> **企业级多智能体路由系统** — 基于大语言模型（LLM）驱动的智能体协作框架，通过 **RouterAgent** 统一调度，将用户任务智能路由给 **CoderAgent**（编程/文件操作）或 **DBAAgent**（数据库/数据格式）执行。

---

## 📋 目录

- [项目简介](#-项目简介)
- [项目结构](#-项目结构)
- [功能特性](#-功能特性)
- [环境要求](#-环境要求)
- [安装与配置](#-安装与配置)
- [使用方法](#-使用方法)
- [架构说明](#-架构说明)
- [注意事项](#-注意事项)

---

## 🎯 项目简介

**多功能 Agent 系统** 是一个基于 LangChain 框架构建的多智能体协作平台，采用 **路由调度架构**（Router Pattern）。系统包含三个核心智能体：

| 智能体 | 角色 | 职责范围 |
|--------|------|----------|
| 🚦 **RouterAgent** | 路由调度核心 | 评估用户任务类型，智能转发给子 Agent |
| 💻 **CoderAgent** | 编程/文件操作 | 代码编写、文件管理、终端命令、Git 版本控制、代码审查 |
| 🗄️ **DBAAgent** | 数据库/数据格式 | 数据库探查（SQLite/MySQL）、JSON/CSV/YAML 格式处理 |

每个子 Agent 维护**独立且绝对静态**的 messages 上下文列表，以最大化 LLM 的 **Cache Hit** 率，提升响应速度和稳定性。

---

## 📁 项目结构

```
D:\ai_workspace\v37_multi_agent\
│
├── main.py                      # 🚀 主程序入口（多智能体路由启动器）
├── .env                         # 🔑 环境变量配置（API Key）
├── plan.md                      # 📋 任务计划文件（由 plan_progress 工具自动管理）
│
├── agents/                      # 🤖 智能体模块
│   ├── __init__.py              #   包初始化，导出所有 Agent 类
│   ├── router_agent.py          #   🚦 RouterAgent - 路由调度核心
│   ├── coder_agent.py           #   💻 CoderAgent - 编程/文件操作子智能体
│   └── dba_agent.py             #   🗄️ DBAAgent - 数据库/数据格式子智能体
│
├── core/                        # ⚙️ 核心模块
│   ├── __init__.py              #   包初始化，导出所有核心组件
│   ├── config.py                #   🔒 安全策略与全局配置
│   ├── llm.py                   #   🤖 大模型初始化（DeepSeek Chat）
│   ├── agent_memory.py          #   🧠 Agent 记忆管理器
│   └── utils.py                 #   🔧 辅助函数（截断、超时、安全路径等）
│
├── tools/                       # 🛠️ 工具集
│   ├── __init__.py              #   包初始化，注册所有工具
│   ├── file_tools.py            #   📂 文件操作工具（读写、终端、搜索等）
│   ├── git_tools.py             #   🗃️ Git 版本控制工具
│   ├── db_tools.py              #   🗄️ 数据库探查工具（SQLite/MySQL）
│   ├── data_tools.py            #   📊 数据格式处理工具（JSON/CSV/YAML）
│   ├── search_tools.py          #   🔍 网络搜索工具（网页抓取、搜索引擎）
│   └── memory_tools.py          #   🧠 记忆管理工具（存档、检索、计划）
│
└── agent_history_archive/       # 📦 记忆存档目录（自动生成）
    └── memory_index.json        #   记忆索引文件
```

---

## ✨ 功能特性

### 🤖 多智能体路由调度
- **RouterAgent** 智能评估用户任务，自动判断任务类型并转发给最合适的子 Agent
- 支持**多轮对话**，RouterAgent 可多次调度不同子 Agent 协同完成复杂任务
- 每个 Agent 维护**独立上下文**，互不干扰，最大化 Cache Hit

### 💻 CoderAgent — 编程与文件操作
| 类别 | 工具 | 功能说明 |
|------|------|----------|
| 📂 **文件操作** | `read_local_file` | 读取小文件全文，自动检测编码 |
| | `read_file_by_lines` | 按行读取大文件，支持范围导航 |
| | `write_local_file` | 写入/创建文件，自动备份原文件 |
| | `list_directory_tree` | 递归列出目录结构树 |
| 💻 **终端命令** | `run_terminal_command` | 执行终端命令，高危命令黑名单拦截 |
| | `pip_install` | 安装 Python 包，内置清华源镜像 |
| ✅ **代码质量** | `check_python_syntax` | 双重检查 Python 语法（ast + flake8） |
| | `code_format_tool` | 格式化/检查/统计代码指标 |
| | `search_code_ast` | AST 解析 Python 源码 |
| 🔍 **搜索** | `grep_search` | 文本搜索 |
| | `read_webpage` | 抓取网页正文 |
| | `web_search` | 网络搜索（多引擎回退） |
| 🗃️ **Git 版本控制** | `git_init_repo` / `git_create_branch` / `git_commit` / `git_diff` / `git_status` / `git_log` / `git_checkout` / `git_branch_list` | 完整的 Git 操作 |

### 🗄️ DBAAgent — 数据库与数据格式
| 类别 | 工具 | 功能说明 |
|------|------|----------|
| 🗄️ **数据库** | `inspect_database` | 探查 SQLite/MySQL 数据库结构 |
| 📊 **数据格式** | `data_format_tool` | JSON/CSV/YAML 解析、验证、格式化、查询、互转 |
| 📂 **文件备份** | `file_backup_tool` | 创建备份、列出版本、恢复文件、对比差异 |
| ✅ **代码格式化** | `code_format_tool` | 代码格式化与质量检查 |

### 🧠 记忆与计划管理
| 工具 | 功能说明 |
|------|----------|
| `agent_memory_archive` | 将关键信息压缩存档到本地，支持分类存储 |
| `agent_memory_retrieve` | 按 ID/键名/分类/步骤检索存档信息 |
| `archive_history_step` | 将功能核心逻辑压缩为快照存档 |
| `plan_progress` | 自动管理 plan.md 的创建、查看、标记、更新 |

### 🛡️ 安全与稳定性
- **安全沙盒**：所有文件操作限制在安全基目录内
- **高危命令黑名单**：拦截 rm -rf、format 等危险操作
- **三重超时保护**：LLM 调用 + 工具调用 + 交互输入 全覆盖
- **指数退避重试**：LLM 调用和工具调用失败时自动重试
- **高低水位线截断**：自动管理上下文窗口，防止 Token 溢出
- **看门狗机制**：单轮执行超时自动跳过，防止卡死

---

## 🔧 环境要求

### 系统要求
- **操作系统**：Windows 10/11 或 Linux / macOS
- **Python**：3.8 及以上（推荐 3.10）
- **Git**：可选（用于版本控制功能）

### Python 依赖

| 包名 | 用途 | 安装方式 |
|------|------|----------|
| `langchain-core` | LangChain 核心框架 | 自动安装 |
| `langchain-openai` | OpenAI 兼容 API 接口 | 自动安装 |
| `openai` | OpenAI SDK | 自动安装 |
| `python-dotenv` | 环境变量加载 | 自动安装 |
| `chardet` | 文件编码检测 | 自动安装 |
| `beautifulsoup4` | 网页解析 | 自动安装 |
| `requests` | HTTP 请求 | 自动安装 |
| `duckduckgo_search` | 网络搜索 | 自动安装 |
| `pymysql` | MySQL 数据库连接（可选） | 按需安装 |
| `pyyaml` | YAML 格式处理（可选） | 按需安装 |
| `autopep8` | 代码格式化（可选） | 按需安装 |
| `flake8` | 代码质量检查（可选） | 按需安装 |

### API 密钥
- **DeepSeek API Key**：必须（用于调用 DeepSeek Chat 模型）
- **智谱 API Key**：可选（.env 文件中预留）

---

## 📦 安装与配置

### 1️⃣ 克隆/下载项目

将项目代码下载到本地目录 `D:\ai_workspace\v37_multi_agent`（或任意安全目录）。

### 2️⃣ 配置 API 密钥

编辑项目根目录下的 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here
```

> **获取 API Key**：
> - DeepSeek：访问 [https://platform.deepseek.com](https://platform.deepseek.com) 注册获取
> - 智谱：访问 [https://open.bigmodel.cn](https://open.bigmodel.cn) 注册获取

### 3️⃣ 安装依赖

推荐使用 conda 虚拟环境：

```bash
# 创建虚拟环境（推荐 Python 3.10）
conda create -n ai_agent python=3.10
conda activate ai_agent

# 安装核心依赖
pip install langchain-core langchain-openai openai python-dotenv chardet beautifulsoup4 requests duckduckgo_search

# 安装可选依赖（按需）
pip install pymysql pyyaml autopep8 flake8
```

### 4️⃣ 验证安装

```bash
python main.py
```

如果看到启动欢迎界面，说明安装成功。

---

## 🚀 使用方法

### 方式一：交互式命令行模式

直接运行主程序，进入交互式输入界面：

```bash
python main.py
```

启动后界面：
```
🚀 企业级多智能体路由系统 v37.0
🔒 安全目录: D:\ai_workspace\v37_multi_agent
📋 架构: RouterAgent → [CoderAgent | DBAAgent]
============================================================

  [多行输入模式]
  - 输入单独一行 EOF 结束
  - 连续两次回车(空行)自动提交
  - 输入 q 单独一行退出程序
------------------------------------------------------------
```

**输入示例**：

```
请帮我检查当前目录下的 Python 文件语法
```

```
帮我查看 data.db 数据库中有哪些表
```

```
将 data.json 文件转换为 YAML 格式
```

### 方式二：命令行参数模式

直接传入任务描述作为命令行参数：

```bash
python main.py "请列出当前目录结构"
python main.py "帮我创建一个 test.py 文件，内容为 print('Hello World')"
python main.py "检查当前目录下所有 .py 文件的语法"
```

### 方式三：Python API 调用

在代码中导入并调用：

```python
import sys
sys.path.insert(0, r"D:\ai_workspace\v37_multi_agent")

from agents.router_agent import RouterAgent
from agents.coder_agent import CoderAgent
from agents.dba_agent import DBAAgent

# 初始化子 Agent
coder = CoderAgent()
dba = DBAAgent()

# 初始化 RouterAgent
router = RouterAgent(coder_agent=coder, dba_agent=dba)

# 运行任务
result = router.run("请列出当前目录结构")
print(result)
```

### 任务示例

| 任务类型 | 示例输入 | 处理 Agent |
|----------|----------|------------|
| 📝 **编写代码** | "帮我写一个快速排序的 Python 函数" | CoderAgent |
| 📂 **文件操作** | "读取 config.json 文件内容" | CoderAgent |
| 💻 **运行命令** | "查看当前目录下有哪些文件" | CoderAgent |
| ✅ **代码审查** | "检查 main.py 的语法和代码质量" | CoderAgent |
| 🗃️ **Git 操作** | "初始化 Git 仓库并提交当前代码" | CoderAgent |
| 🗄️ **数据库探查** | "连接 data.db 查看所有表结构" | DBAAgent |
| 📊 **格式转换** | "将 data.json 转换为 CSV 格式" | DBAAgent |
| 🔄 **文件备份** | "备份 config.py 文件" | DBAAgent |
| 🔍 **网络搜索** | "搜索 Python 异步编程的最佳实践" | CoderAgent |

---

## 🏗️ 架构说明

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户输入 (User Input)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  🚦 RouterAgent（路由调度核心）                               │
│                                                             │
│  职责：                                                      │
│  1. 评估用户任务类型                                          │
│  2. 调用 delegate_task 工具转发任务                            │
│  3. 收集子 Agent 结果并汇报给用户                              │
│                                                             │
│  上下文：独立静态 messages 列表                                │
└──────────┬────────────────────────────────┬──────────────────┘
           │                                │
           ▼                                ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│ 💻 CoderAgent        │    │ 🗄️ DBAAgent                  │
│                      │    │                              │
│ 编程/文件操作子智能体   │    │ 数据库/数据格式子智能体       │
│                      │    │                              │
│ 绑定工具：             │    │ 绑定工具：                   │
│ 📂 文件操作工具集      │    │ 🗄️ 数据库探查工具            │
│ 💻 终端命令工具        │    │ 📊 数据格式处理工具           │
│ ✅ 代码质量工具        │    │ 📂 文件读取工具              │
│ 🗃️ Git 版本控制       │    │ 🧠 记忆管理工具              │
│ 🔍 网络搜索工具        │    │                            │
│ 🧠 记忆管理工具        │    │                            │
│ 📊 数据格式工具        │    │                            │
│                      │    │                              │
│ 上下文：独立静态列表    │    │ 上下文：独立静态列表          │
└──────────────────────┘    └──────────────────────────────┘
```

### 核心组件说明

#### 1️⃣ RouterAgent（路由调度核心）
- **文件**：`agents/router_agent.py`
- **职责**：接收用户输入，通过 LLM 评估任务类型，使用 `delegate_task` 工具将任务转发给 CoderAgent 或 DBAAgent
- **特点**：维护独立静态上下文，不直接执行具体任务

#### 2️⃣ CoderAgent（编程/文件操作子智能体）
- **文件**：`agents/coder_agent.py`
- **职责**：处理所有编程相关任务，绑定 20+ 个工具
- **工具范围**：文件读写、终端命令、代码质量检查、Git 版本控制、网络搜索、记忆管理

#### 3️⃣ DBAAgent（数据库/数据格式子智能体）
- **文件**：`agents/dba_agent.py`
- **职责**：处理数据库探查和数据格式转换任务
- **工具范围**：SQLite/MySQL 探查、JSON/CSV/YAML 处理、文件备份恢复

#### 4️⃣ Core 核心模块
- **`core/config.py`**：安全策略（安全基目录、高危命令黑名单）、全局配置（超时、重试、截断）
- **`core/llm.py`**：初始化 DeepSeek Chat 模型，构建系统提示词
- **`core/agent_memory.py`**：记忆管理器，支持压缩存档、分类存储、版本追踪、灵活检索
- **`core/utils.py`**：辅助函数（输出截断、安全路径检查、编码解码、高低水位线截断、超时执行包装器）

#### 5️⃣ Tools 工具集
- **`tools/file_tools.py`**：文件操作、终端命令、代码质量、搜索工具
- **`tools/git_tools.py`**：Git 版本控制全套工具
- **`tools/db_tools.py`**：SQLite/MySQL 数据库探查
- **`tools/data_tools.py`**：JSON/CSV/YAML 格式处理、文件备份、代码格式化
- **`tools/search_tools.py`**：网页抓取、网络搜索
- **`tools/memory_tools.py`**：记忆存档、检索、历史快照、计划管理

### 关键设计理念

1. **独立上下文**：每个 Agent 维护自己的 messages 列表，互不干扰，最大化 LLM Cache Hit
2. **路由解耦**：RouterAgent 只负责调度，不执行具体任务，职责单一
3. **工具驱动**：Agent 通过调用工具完成任务，LLM 负责决策和规划
4. **安全优先**：所有文件操作限制在安全目录，高危命令黑名单拦截
5. **稳定性保障**：三重超时保护、指数退避重试、看门狗机制、高低水位线截断

---

## ⚠️ 注意事项

### 🔒 安全相关
1. **API Key 保护**：`.env` 文件包含 API Key，**切勿**提交到公共 Git 仓库
2. **安全目录限制**：所有文件操作只能在项目根目录及其子目录内进行
3. **高危命令拦截**：系统会自动拦截 `rm -rf`、`format`、`shutdown` 等危险命令
4. **文件备份**：修改已有文件时会自动创建 `.bak` 备份

### ⚙️ 配置相关
1. **Python 路径**：如果使用 conda 虚拟环境，请修改 `core/config.py` 中的 `PIP_PYTHON_EXE` 为你的实际 Python 路径
2. **LLM 超时**：默认 LLM 调用超时为 120 秒，可根据网络状况在 `core/config.py` 中调整 `LLM_TIMEOUT`
3. **最大步数**：默认最大循环步数为 500，可在 `core/config.py` 中调整 `DEFAULT_MAX_STEPS`

### 🚀 使用建议
1. **复杂任务**：对于需要多步操作的任务，Agent 会自动创建 `plan.md` 来管理进度
2. **大文件处理**：读取大文件时请使用 `read_file_by_lines` 按行读取，避免内存溢出
3. **代码执行**：执行 Python 代码前，Agent 会自动检查语法，确保代码正确
4. **网络搜索**：搜索功能依赖 DuckDuckGo，如遇网络问题会自动回退到备用方案

### 🐛 常见问题
| 问题 | 解决方案 |
|------|----------|
| `DEEPSEEK_API_KEY 未设置` | 检查 `.env` 文件是否存在且包含正确的 API Key |
| `Git 未安装` | 安装 Git 或忽略 Git 相关功能 |
| `pymysql 未安装` | 运行 `pip install pymysql`（仅 MySQL 功能需要） |
| `PyYAML 未安装` | 运行 `pip install pyyaml`（仅 YAML 功能需要） |
| 输入卡住无响应 | 系统有 300 秒输入超时保护，超时后会自动使用默认任务 |
| LLM 调用超时 | 检查网络连接，或在 `core/config.py` 中增大 `LLM_TIMEOUT` |

---

## 📜 版本历史

| 版本 | 说明 |
|------|------|
| v37.0 | 多智能体路由版 — RouterAgent + CoderAgent + DBAAgent 架构 |
| v34.0 | 主循环稳定性增强 — 三重超时保护、看门狗机制 |
| v31.0 | 主循环优化 — 高低水位线截断、指数退避重试 |
| v23.0 | 代码格式化与质量检查工具 |
| v21.0 | 文件备份与恢复工具 |
| v19.0 | 数据格式处理工具（JSON/CSV/YAML） |
| v18.0 | 记忆管理与计划管理工具 |
| v16.0 | 数据库探查工具（SQLite/MySQL） |
| v14.0 | 基础 Agent 框架 |

---

> **📧 联系我们**：如有问题或建议，欢迎提交 Issue 或 Pull Request。
>
> **📝 许可证**：本项目仅供学习和研究使用。
