
# 🤖 多智能体路由系统 (Multi-Agent System)

**版本**: v50.0 | **连续上下文记忆版**

> 基于 LangChain 框架的企业级多智能体协作系统，实现从需求分析 → 计划制定 → 代码生成 → 代码审查的全自动化开发流程。

---

## 📋 项目简介

本系统采用**路由调度架构**，由 **RouterAgent** 统一接收用户任务，智能评估任务类型后转发给对应的子 Agent 执行。每个子 Agent 维护自己独立且绝对静态的 messages 上下文列表，以最大化 LLM Cache Hit。v50.0 引入**全局单例模式**，实现跨任务的连续上下文记忆。

### 核心架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户输入                                   │
│              (CLI 终端 / Gradio Web UI)                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  🚦 RouterAgent（路由调度核心）                                     │
│                                                                     │
│  职责：                                                             │
│  ├─ 评估用户任务类型                                                │
│  ├─ 通过 delegate_task 转发给子 Agent                               │
│  └─ 收集结果并汇报给用户                                            │
│                                                                     │
│  🧠 连续上下文记忆（v50.0）                                         │
│  └─ 全局单例，跨任务保持对话上下文自然延续                           │
└────────┬──────────┬──────────┬──────────┬───────────────────────────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐
│ 📋 PMAgent │  💻 Coder   │  🗄️ DBA     │  🔍 Reviewer  │
│            │    Agent     │    Agent    │    Agent      │
│技术产品经理│ 编程智能体    │ 数据库智能体 │ 代码审查智能体 │
│            │              │             │                │
│ • 需求拆解 │ • 编写代码   │ • 数据库探查 │ • 代码格式化    │
│ • 计划制定 │ • 文件操作   │ • SQL 查询   │ • 语法检查      │
│ • 生成plan │ • 运行命令   │ • 数据格式   │ • 单元测试      │
│   .md      │ • Git 管理   │   转换       │ • Bug 报告      │
└────────────┘ └────────────┘ └────────────┘ └──────────────┘
```

---

## 🧠 五大智能体

| 智能体 | 名称 | 核心职责 | 绑定工具数 |
|--------|------|----------|-----------|
| 🚦 **RouterAgent** | 路由调度核心 | 评估用户任务，智能路由转发，汇总子 Agent 结果 | 1（delegate_task） |
| 📋 **PMAgent** | 技术产品经理 | 将模糊需求转化为可执行的开发步骤，生成 `plan.md` 计划文件 | 2 |
| 💻 **CoderAgent** | 编程智能体 | 编写/修改代码、文件操作、运行终端命令、Git 版本控制 | 25+ |
| 🗄️ **DBAAgent** | 数据库智能体 | 数据库探查（SQLite/MySQL）、数据格式转换（JSON/CSV/YAML） | 10+ |
| 🔍 **ReviewerAgent** | 代码审查智能体 | 代码格式化、语法检查、编写并运行 pytest 单元测试 | 7 |

---

## 🔧 工具集

### 📂 文件操作工具
| 工具 | 说明 |
|------|------|
| `read_local_file` | 读取小文件全文，自动检测编码 |
| `read_file_by_lines` | 按行读取大文件，支持行号范围 |
| `write_local_file` | 写入/创建文件，自动备份原文件 |
| `list_directory_tree` | 递归列出目录结构 |
| `pip_install` | 安装 Python 包（清华源镜像） |
| `check_python_syntax` | 双重检查 Python 语法（ast + flake8） |
| `search_code_ast` | AST 深度解析 Python 源码 |
| `grep_search` | 快速文本搜索 |

### 💻 终端命令工具
| 工具 | 说明 |
|------|------|
| `run_terminal_command` | 执行终端命令，带安全保护和超时 |

### 🗃️ Git 版本控制工具
| 工具 | 说明 |
|------|------|
| `git_init_repo` | 初始化 Git 仓库 |
| `git_create_branch` | 创建并切换分支 |
| `git_commit` | 提交更改 |
| `git_diff` | 查看差异 |
| `git_status` | 查看状态 |
| `git_log` | 查看提交历史 |
| `git_checkout` | 切换分支 |
| `git_branch_list` | 列出分支 |

### 🗄️ 数据库工具
| 工具 | 说明 |
|------|------|
| `inspect_database` | 探查 SQLite/MySQL 数据库结构 |

### 📊 数据格式工具
| 工具 | 说明 |
|------|------|
| `data_format_tool` | JSON/CSV/YAML 解析、验证、格式化、查询、互转 |
| `file_backup_tool` | 文件备份、版本恢复、差异对比 |
| `code_format_tool` | 代码格式化（autopep8）、质量检查（flake8）、指标统计 |

### 🔍 搜索工具
| 工具 | 说明 |
|------|------|
| `read_webpage` | 抓取网页正文内容 |
| `web_search` | 网络搜索（DuckDuckGo，多引擎回退） |

### 🧠 记忆管理工具
| 工具 | 说明 |
|------|------|
| `agent_memory_archive` | 将关键信息压缩存档到本地 |
| `agent_memory_retrieve` | 检索历史存档 |
| `archive_history_step` | 压缩提取历史功能快照 |
| `plan_progress` | 管理 plan.md 计划进度 |
| `semantic_search_memory` | 向量语义搜索历史记忆 |

### 🌐 API 调试工具
| 工具 | 说明 |
|------|------|
| `send_api_request` | 发送 HTTP 请求（类似 Postman） |

### 🕸️ 动态网页抓取工具
| 工具 | 说明 |
|------|------|
| `fetch_dynamic_webpage` | Playwright 无头浏览器渲染 JS 动态内容 |

---

## 🌟 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 **连续上下文记忆** | 全局单例 RouterAgent，跨任务保持对话上下文自然延续 |
| 👤 **双轨制入口** | CLI 终端交互模式 + Gradio Web UI 界面 |
| 🔒 **安全沙盒** | 所有文件操作限制在安全目录内，高危命令黑名单拦截 |
| 👀 **HITL 人工审批** | 支持免审批/高危审批两种模式，关键操作可请求人工确认 |
| 📦 **向量记忆** | 集成 ChromaDB 向量数据库，支持语义搜索历史记忆 |
| ⏱️ **三重超时保护** | LLM 调用 + 工具调用 + 交互输入，无死角覆盖 |
| 🔄 **自动重试** | 指数退避重试策略，提升系统稳定性 |
| 📐 **高低水位线截断** | 智能滑动窗口截断，确保 tool_calls 与 ToolMessage 成对保留 |
| 🛡️ **看门狗机制** | 单轮执行超时检测，防止无限卡死 |
| 🔧 **20+ 专业工具** | 覆盖文件操作、Git、数据库、数据格式、搜索、记忆、API 调试等 |

---

## 🔌 技术栈

| 类别 | 技术 |
|------|------|
| **语言** | Python ≥ 3.10 |
| **AI 框架** | LangChain, LangChain-Core, LangChain-Community, LangChain-OpenAI |
| **大模型** | DeepSeek Chat（兼容 OpenAI API 格式） |
| **Web 界面** | Gradio |
| **向量数据库** | ChromaDB |
| **代码质量** | flake8, autopep8, black, ruff |
| **网页抓取** | Playwright, BeautifulSoup4, requests |
| **数据格式** | PyYAML, chardet |
| **网络搜索** | duckduckgo_search |
| **数据库** | SQLAlchemy, pymysql（可选） |
| **工具库** | Pydantic, python-dotenv, rich, tqdm |

---

## 📦 安装指南

### 前置要求

- Python ≥ 3.10
- Git（可选，用于版本控制功能）
- 有效的 DeepSeek API Key

### 安装步骤

```bash
# 1. 克隆仓库
git clone -b v50 https://github.com/hjy110011/agent.git
cd multi-agent-system

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DEEPSEEK_API_KEY

# 5. （可选）安装 Playwright 浏览器
playwright install chromium
```

---

## 🚀 启动指南

### CLI 交互模式（推荐）

```bash
python main.py
```

启动后，系统会提示选择审批模式：
- **免审批模式** — 所有操作自动放行
- **高危审批模式** — 仅高危命令需要人工确认

支持多行输入，连续两次回车自动提交，输入 `q` 单独一行退出。

### Web UI 模式

```bash
python main.py --ui
```

启动后访问 `http://127.0.0.1:7860` 即可在浏览器中使用。

### 直接执行任务

```bash
python main.py "请帮我检查当前目录下的 Python 文件"
```

---

## 💡 使用示例

### 示例 1：代码审查

```
用户: 请帮我审查 main.py 的代码质量
系统: RouterAgent → ReviewerAgent
      → 格式化代码 → 语法检查 → 运行测试 → 输出报告
```

### 示例 2：数据库探查

```
用户: 帮我看看这个 SQLite 数据库里有什么表
系统: RouterAgent → DBAAgent
      → 连接数据库 → 列出表结构 → 统计行数 → 输出结果
```

### 示例 3：新项目开发

```
用户: 帮我创建一个简单的计算器程序
系统: RouterAgent → PMAgent（制定计划）
      → CoderAgent（编写代码）
      → ReviewerAgent（审查代码）
      → 输出最终结果
```

### 示例 4：API 调试

```
用户: 帮我测试一下 https://api.example.com/health 是否可用
系统: RouterAgent → CoderAgent
      → send_api_request(GET, url)
      → 输出状态码和响应结果
```

---

## 📁 项目结构

```
multi-agent-system/
├── agents/                     # 🧠 多智能体模块
│   ├── router_agent.py         # 🚦 路由调度核心
│   ├── coder_agent.py          # 💻 编程/文件操作 Agent
│   ├── dba_agent.py            # 🗄️ 数据库 Agent
│   ├── pm_agent.py             # 📋 产品经理 Agent
│   └── reviewer_agent.py       # 🔍 代码审查 Agent
├── core/                       # ⚙️ 核心基础设施
│   ├── config.py               # 🔒 安全策略与全局配置
│   ├── llm.py                  # 🤖 LLM 初始化（DeepSeek）
│   ├── agent_memory.py         # 🧠 记忆管理（含 ChromaDB）
│   ├── hitl_approval.py        # 👤 人工审批（HITL）
│   └── utils.py                # 🛠️ 工具函数
├── tools/                      # 🔧 Agent 工具集
│   ├── file_tools.py           # 📂 文件操作工具
│   ├── git_tools.py            # 🗃️ Git 版本控制工具
│   ├── db_tools.py             # 🗄️ 数据库探查工具
│   ├── data_tools.py           # 📊 数据格式/备份/代码格式化
│   ├── search_tools.py         # 🔍 网页搜索工具
│   ├── memory_tools.py         # 🧠 记忆管理工具
│   ├── api_tools.py            # 🌐 API 调试工具
│   └── browser_tools.py        # 🕸️ 动态网页抓取工具
├── main.py                     # 🚀 主入口（CLI + Web UI）
├── web_ui.py                   # 🌐 Gradio Web 界面
├── pyproject.toml              # 📦 项目配置
├── requirements.txt            # 📦 Python 依赖清单
├── .env                        # 🔑 环境变量
└── .env.example                # 🔑 环境变量模板
```

---

## ⚙️ 配置说明

### 环境变量（.env）

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API 密钥 |
| `APPROVAL_MODE` | ❌ | 审批模式：`none` / `dangerous_only` |
| `AGENT_MAX_ITERATIONS` | ❌ | Agent 最大循环步数（默认 500） |
| `LLM_TIMEOUT` | ❌ | LLM 调用超时时间（默认 120 秒） |

### 审批模式

| 模式 | 说明 |
|------|------|
| `none` | 免审批模式，所有操作自动放行 |
| `dangerous_only` | 高危审批模式，仅高危命令需要人工确认（默认） |

---

## 🧪 开发指南

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
# 使用 black 格式化
black .

# 使用 ruff 检查
ruff check .
```

### 添加新工具

1. 在 `tools/` 目录下创建新的工具文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在 `tools/__init__.py` 中导入并添加到 `all_tools` 列表
4. 在对应 Agent 的 `__init__` 方法中绑定新工具

---

## 📜 版本历史

| 版本 | 亮点 |
|------|------|
| v50.0 | 🧠 **连续上下文记忆** — 全局单例 RouterAgent，跨任务对话延续 |
| v48.0 | 📦 项目标准化 — pyproject.toml 配置，版本号统一 |
| v47.0 | 👤 HITL 审批模式 — 策略模式重构，支持免审批/高危审批 |
| v45.0 | 🔒 HITL 人工审批 — 高危操作执行前请求人工确认 |
| v42.0 | 🌐 API 调试工具 — send_api_request，类似 Postman |
| v39.0 | 🚦 RouterAgent 重构 — 路由调度核心全面升级 |
| v34.0 | 🛡️ 主循环稳定性增强 — 三重超时保护，看门狗机制 |
| v31.0 | ⏱️ 超时解决方案 — LLM 调用超时保护，指数退避重试 |
| v23.0 | ✨ 代码格式化工具 — code_format_tool |
| v21.0 | 📂 文件备份恢复 — file_backup_tool |
| v19.0 | 📊 数据格式处理 — data_format_tool |
| v18.0 | 🧠 记忆管理 + ChromaDB — 向量语义搜索 |
| v16.0 | 🗄️ 数据库探查 — inspect_database |



*让 AI 智能体协作，自动化您的开发流程！*
