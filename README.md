# 🤖 多 Agent 协作系统 (v48.0)

## 项目简介

本项目是一个基于 **LangChain** 框架的企业级多 Agent 协作系统，通过 **RouterAgent** 统一调度多个专业化子 Agent（PMAgent、CoderAgent、DBAAgent、ReviewerAgent），实现从需求分析到代码生成、数据库操作、代码审查的完整开发流程自动化。

每个子 Agent 维护**独立且绝对静态的 messages 上下文列表**，以最大化 LLM Cache Hit 效率。系统支持 **CLI 终端交互模式**和 **Gradio Web UI 界面**双轨制入口，并内置 **HITL（Human-In-The-Loop）人工审批**机制保障操作安全。

### 核心特性

- 🚦 **智能路由调度** — RouterAgent 自动评估任务类型，分派给最合适的子 Agent
- 📋 **需求拆解** — PMAgent 将模糊需求转化为可执行的开发计划（plan.md）
- 💻 **代码生成** — CoderAgent 绑定 20+ 工具，覆盖文件操作、Git、搜索、API 调试等
- 🗄️ **数据库与数据格式** — DBAAgent 支持 SQLite/MySQL 探查、JSON/CSV/YAML 格式处理
- 🔍 **代码审查** — ReviewerAgent 进行语法检查、代码格式化、pytest 单元测试
- 🛡️ **安全机制** — 高危命令黑名单拦截 + HITL 人工审批（支持免审批/高危审批两种模式）
- 🧠 **记忆管理** — 基于 ChromaDB 的向量语义记忆检索，跨会话持久化
- 🌐 **双轨制入口** — CLI 多行终端交互 + Gradio Web UI 界面

## 系统架构

```
用户请求
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     RouterAgent                             │
│              🚦 智能路由调度核心                              │
│         评估任务类型 → 分派给对应子 Agent                      │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  PMAgent    │ │ CoderAgent  │ │  DBAAgent   │ │ReviewerAgent│
│  📋 产品经理 │ │ 💻 编程专家  │ │ 🗄️ 数据库专家│ │ 🔍 审查专家  │
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│ 需求分析     │ │ 文件操作     │ │ 数据库探查   │ │ 语法检查     │
│ 任务拆解     │ │ 代码编写     │ │ 数据格式转换 │ │ 代码格式化   │
│ 生成计划     │ │ Git 版本控制 │ │ 文件备份恢复 │ │ 编写测试     │
│ plan.md     │ │ API 调试     │ │ 数据查询     │ │ Bug 报告     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 数据流说明

1. **用户输入** → 通过 CLI 或 Web UI 提交自然语言任务
2. **RouterAgent 评估** → 分析任务类型，决定由哪个子 Agent 处理
3. **任务转发** → 使用 `delegate_task` 工具将任务上下文传递给子 Agent
4. **子 Agent 执行** → 各自调用绑定的工具集完成任务
5. **结果汇总** → RouterAgent 收集结果并汇报给用户

## Agent 角色说明

### 1. 🚦 RouterAgent（路由调度代理）
| 项目 | 说明 |
|------|------|
| **职责** | 接收用户请求，分析请求类型，通过 `delegate_task` 工具路由到对应的子 Agent |
| **输入** | 用户自然语言请求 |
| **输出** | 路由决策 + 子 Agent 执行结果汇总 |
| **核心逻辑** | 维护独立静态 messages 列表，LLM 调用带超时保护（120s）和指数退避重试 |
| **版本** | v39.0 |

### 2. 📋 PMAgent（技术产品经理代理）
| 项目 | 说明 |
|------|------|
| **职责** | 拦截用户模糊的初始需求，通过逻辑推理转化为可执行的开发步骤，强制生成 plan.md |
| **输入** | 用户需求描述 |
| **输出** | plan.md 计划文件、任务清单 |
| **绑定工具** | `plan_progress`、`write_local_file` |
| **约束** | 绝不写具体代码，只负责制定严谨的计划 |
| **版本** | v39.0 |

### 3. 💻 CoderAgent（编程/文件操作代理）
| 项目 | 说明 |
|------|------|
| **职责** | 处理所有编程相关任务（编写代码、修改文件、运行命令、Git 版本控制等） |
| **输入** | 任务描述、技术栈要求 |
| **输出** | 代码文件、命令执行结果 |
| **绑定工具** | 文件操作（6个）、代码质量（3个）、Git（8个）、搜索（3个）、记忆（5个）、数据格式（2个）、API调试（1个）、网页抓取（1个）— 共 29 个工具 |
| **版本** | v37.0 |

### 4. 🗄️ DBAAgent（数据库管理员代理）
| 项目 | 说明 |
|------|------|
| **职责** | 处理数据库探查（SQLite/MySQL）、数据格式处理（JSON/CSV/YAML 解析、转换、查询）、文件备份恢复 |
| **输入** | 数据需求描述 |
| **输出** | 数据库结构分析、格式转换结果、备份恢复结果 |
| **绑定工具** | `inspect_database`、`data_format_tool`、`file_backup_tool`、`code_format_tool`、文件读取工具、记忆工具 |
| **版本** | v37.0 |

### 5. 🔍 ReviewerAgent（代码审查代理）
| 项目 | 说明 |
|------|------|
| **职责** | 代码格式化、语法检查、编写并运行 pytest 单元测试、发现 Bug 并明确指出 |
| **输入** | 代码文件路径或内容 |
| **输出** | 审查报告、测试结果、Bug 修复建议 |
| **绑定工具** | `code_format_tool`、`check_python_syntax`、`write_local_file`、`run_terminal_command`、`send_api_request`、`fetch_dynamic_webpage`、`semantic_search_memory` |
| **工作流程** | 格式化 → 语法检查 → 编写测试 → 运行测试 → 报告结果 |
| **版本** | v38.0 |

## 技术栈

### 核心框架
| 技术 | 用途 |
|------|------|
| **Python 3.10+** | 运行环境 |
| **LangChain** | LLM 调用框架、消息管理、工具绑定 |
| **ChatOpenAI / DeepSeek** | 大语言模型后端（兼容 OpenAI API 格式） |

### 工具库
| 技术 | 用途 |
|------|------|
| **python-dotenv** | 环境变量管理 |
| **Pydantic** | 数据验证 |
| **PyYAML** | YAML 格式处理 |
| **Requests** | HTTP 请求 |
| **ChromaDB** | 向量数据库（语义记忆检索） |
| **Playwright** | 动态网页抓取（JavaScript 渲染） |

### Web 界面
| 技术 | 用途 |
|------|------|
| **Gradio** | Web UI 界面（v46.1，兼容 Gradio 6.x） |

### 数据库
| 技术 | 用途 |
|------|------|
| **SQLAlchemy** | ORM 框架 |
| **SQLite** | 内置数据库支持 |
| **MySQL / PostgreSQL** | 可选外部数据库 |

### 开发与测试
| 技术 | 用途 |
|------|------|
| **pytest** | 单元测试 |
| **pytest-asyncio** | 异步测试支持 |
| **Black** | 代码格式化 |
| **Ruff** | 代码质量检查 |
| **Flake8** | 代码质量检查（运行时） |
| **autopep8** | 代码自动格式化（运行时） |

## 环境要求

- **Python 3.10+**（推荐 3.10 ~ 3.12）
- **pip** 或 **conda** 包管理器
- **操作系统**：Windows / Linux / macOS 均可

### 可选依赖
- **PostgreSQL**（如需使用 PostgreSQL 数据库）
- **Redis**（如需 Agent 状态缓存）
- **Docker**（如需容器化部署）

## 一键环境配置

### 方式一：本地安装

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd v48_test

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活
venv\Scripts\activate
# Linux/Mac 激活
# source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DEEPSEEK_API_KEY（必填）

# 5. 运行项目（CLI 交互模式）
python main.py

# 或启动 Web UI
python main.py --ui
```

### 方式二：使用 Conda

```bash
# 1. 创建虚拟环境
conda create -n multi-agent python=3.10
conda activate multi-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置并运行
cp .env.example .env
# 编辑 .env 文件
python main.py
```

### 方式三：使用 Docker（需自行编写 Dockerfile）

```bash
docker build -t multi-agent-system .
docker run -it --rm multi-agent-system
```

## 项目目录结构

```
D:\ai_workspace\v48_test/
├── main.py                      # 🚀 主入口（CLI + Web UI 双轨制）
├── web_ui.py                    # 🌐 Gradio Web UI 界面（v46.1）
├── README.md                    # 📖 项目说明文档
├── requirements.txt             # 📦 Python 依赖文件
├── pyproject.toml               # 📋 项目元数据与工具配置
├── plan.md                      # 📋 当前任务计划文件
├── .env                         # 🔒 环境变量（不提交到版本控制）
├── .env.example                 # 🔑 环境变量模板
│
├── agents/                      # 🤖 Agent 模块
│   ├── __init__.py              #   包入口，导出所有 Agent 类
│   ├── router_agent.py          #   🚦 路由调度核心（v39.0）
│   ├── pm_agent.py              #   📋 产品经理代理（v39.0）
│   ├── coder_agent.py           #   💻 编程/文件操作代理（v37.0）
│   ├── dba_agent.py             #   🗄️ 数据库/数据格式代理（v37.0）
│   └── reviewer_agent.py        #   🔍 代码审查代理（v38.0）
│
├── core/                        # ⚙️ 核心模块
│   ├── __init__.py              #   包入口
│   ├── config.py                #   🔒 安全策略与全局配置
│   ├── llm.py                   #   🤖 LLM 初始化（DeepSeek Chat）
│   ├── llm_backup.py            #   📦 LLM 备份版本
│   ├── llm_new.py               #   📦 LLM 新版本
│   ├── agent_memory.py          #   🧠 Agent 记忆管理器（v18.0，集成 ChromaDB）
│   ├── hitl_approval.py         #   🤝 HITL 人工审批模块（策略模式）
│   └── utils.py                 #   🔧 辅助函数（截断、超时、水位线等）
│
├── tools/                       # 🛠️ 工具集
│   ├── __init__.py              #   包入口，导出所有工具函数
│   ├── file_tools.py            #   📂 文件操作工具
│   ├── git_tools.py             #   🗃️ Git 版本控制工具
│   ├── db_tools.py              #   🗄️ 数据库探查工具
│   ├── data_tools.py            #   📊 数据格式处理工具
│   ├── search_tools.py          #   🔍 网络搜索工具
│   ├── memory_tools.py          #   🧠 记忆管理工具
│   ├── api_tools.py             #   🌐 API 调试工具
│   └── browser_tools.py         #   🕸️ 动态网页抓取工具
│
├── agent_history_archive/       # 📦 记忆存档目录
│   └── memory_index.json        #   记忆索引文件
│
├── agent_vector_db/             # 🧠 ChromaDB 向量数据库
│   └── chroma.sqlite3           #   向量存储文件
│
└── .agent_backups/              # 📂 文件备份目录（自动生成）
```

## 使用示例

### CLI 交互模式

```bash
# 启动多行终端 CLI 交互模式
python main.py

# 直接执行指定任务
python main.py "请帮我检查当前目录下的 Python 文件"

# 启动 Web UI 界面
python main.py --ui
```

### Python API 调用

```python
from agents.router_agent import RouterAgent
from agents.coder_agent import CoderAgent
from agents.dba_agent import DBAAgent
from agents.reviewer_agent import ReviewerAgent
from agents.pm_agent import PMAgent

# 初始化子 Agent
pm_agent = PMAgent()
coder_agent = CoderAgent()
dba_agent = DBAAgent()
reviewer_agent = ReviewerAgent()

# 初始化 RouterAgent（传入所有子 Agent 引用）
router = RouterAgent(
    coder_agent=coder_agent,
    dba_agent=dba_agent,
    reviewer_agent=reviewer_agent,
    pm_agent=pm_agent,
)

# 发送任务
result = router.run("请帮我创建一个简单的 Python 脚本，计算斐波那契数列")
print(result)
```

### 使用 main.py 入口函数

```python
from main import run_multi_agent

# 直接调用多 Agent 路由入口
result = run_multi_agent("请帮我检查当前目录下的 Python 文件")
print(result)
```

### Web UI 界面

```python
# 编程方式启动 Web UI
from web_ui import launch_ui
launch_ui(server_name="127.0.0.1", server_port=7860)
```

## 开发指南

### 添加新的 Agent

1. 在 `agents/` 目录下创建新的 Agent 文件（如 `my_agent.py`）
2. 定义 Agent 类，参考现有 Agent 的结构：
   - 在 `__init__` 中初始化 LLM 并绑定工具
   - 维护独立的 `messages` 上下文列表
   - 实现 `run(task_context, max_steps)` 方法
   - 任务完成后输出 `"【任务完成】"`
3. 在 `agents/__init__.py` 中导出新 Agent
4. 在 `main.py` 中实例化新 Agent 并传入 RouterAgent

```python
# agents/my_agent.py 示例
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm import init_llm

class MyAgent:
    def __init__(self):
        self.name = "MyAgent"
        self.llm = init_llm()
        self.messages = [SystemMessage(content="你的系统提示词")]
    
    def run(self, task_context, max_steps=500):
        self.messages.append(HumanMessage(content=task_context))
        # ... 主循环逻辑
        return "【任务完成】"
```

### 添加新的工具

1. 在 `tools/` 目录下选择合适的文件添加工具函数
2. 使用 `@tool` 装饰器（来自 `langchain_core.tools`）
3. 在 `tools/__init__.py` 中导出并加入 `all_tools` 列表
4. 在对应 Agent 的 `__init__` 中将工具加入绑定列表

### 修改 LLM 后端

编辑 `core/llm.py` 中的 `init_llm()` 函数：

```python
# 切换到 OpenAI
return ChatOpenAI(
    model="gpt-4-turbo-preview",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1",
    ...
)
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_router_agent.py -v

# 带覆盖率报告
pytest --cov=agents --cov=core tests/
```

### 代码质量检查

```bash
# 代码格式化
black .

# 代码质量检查
ruff check .

# 类型检查（需安装 mypy）
mypy agents/ core/
```

## 配置说明

### 环境变量（.env）

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API 密钥（当前默认 LLM 后端） |
| `ZHIPU_API_KEY` | ❌ | 智谱 API 密钥（备用） |
| `OPENAI_API_KEY` | ❌ | OpenAI API 密钥（如需切换） |
| `ANTHROPIC_API_KEY` | ❌ | Anthropic API 密钥（如需切换） |
| `DB_HOST` / `DB_PORT` | ❌ | 数据库连接配置 |
| `APP_ENV` | ❌ | 运行环境（development/production） |

### 审批模式

系统启动时可选择两种审批模式：

- **免审批模式（none）** — 所有操作自动放行，适合开发调试
- **高危审批模式（dangerous_only）** — 只审批高危命令（如 `rm -rf`、`format` 等），适合生产环境

```python
from core.hitl_approval import set_approval_strategy

# 切换为免审批模式
set_approval_strategy("none")

# 切换为高危审批模式
set_approval_strategy("dangerous_only")
```

## 常见问题 (FAQ)

### Q: 如何配置 API Key？
A: 复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`。当前系统默认使用 DeepSeek Chat 模型（兼容 OpenAI API 格式）。

### Q: 支持哪些 LLM 后端？
A: 当前默认使用 **DeepSeek Chat**。通过修改 `core/llm.py` 中的 `init_llm()` 函数，可切换为 OpenAI、Anthropic、智谱 GLM 等兼容 OpenAI API 格式的模型。

### Q: 如何切换审批模式？
A: 启动 CLI 模式时，系统会提示选择审批模式（1=免审批，2=高危审批）。也可以在代码中调用 `set_approval_strategy("none")` 或 `set_approval_strategy("dangerous_only")`。

### Q: Web UI 如何启动？
A: 执行 `python main.py --ui`，默认在 `http://127.0.0.1:7860` 启动。Web 端自动使用免审批模式。

### Q: 如何添加新的工具？
A: 在 `tools/` 目录下添加工具函数，使用 `@tool` 装饰器，然后在 `tools/__init__.py` 中导出并加入 `all_tools` 列表，最后在对应 Agent 中绑定。

### Q: 如何扩展新的 Agent 类型？
A: 参考开发指南中的步骤，创建新的 Agent 类（继承/参考现有 Agent 结构），实现 `run()` 方法，在 RouterAgent 中注册。

### Q: 系统支持哪些数据库？
A: 内置支持 **SQLite**（无需额外配置），可选支持 **MySQL** 和 **PostgreSQL**（需安装对应驱动）。

### Q: 记忆管理如何工作？
A: 系统使用 ChromaDB 向量数据库存储记忆摘要，支持语义搜索。Agent 可通过 `agent_memory_archive` 存档信息，通过 `semantic_search_memory` 按语义检索历史记忆。

### Q: 遇到 "DEEPSEEK_API_KEY 未设置" 错误怎么办？
A: 请确保已复制 `.env.example` 为 `.env`，并在 `.env` 文件中填入有效的 `DEEPSEEK_API_KEY`。

### Q: 如何退出 CLI 模式？
A: 在输入提示符下输入 `q`、`quit` 或 `exit` 即可退出。

## 许可证

MIT License
