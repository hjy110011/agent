# 🚀 企业级多智能体路由系统 (v43.0)

> **多智能体协作框架** — 基于 LangChain + DeepSeek 大模型，通过 RouterAgent 路由调度，协同多个专业子智能体完成复杂任务。

---

## 📋 项目简介

本项目是一个**企业级多智能体路由系统**，采用**路由调度架构**，通过一个中央路由智能体（RouterAgent）评估用户任务，智能地将任务转发给最合适的专业子智能体执行。每个子智能体维护自己独立且绝对静态的上下文消息列表，以最大化 LLM Cache Hit 效率。

系统内置 **5 个专业智能体**，覆盖需求分析、编程开发、数据库管理、代码审查等全流程，可协同完成从需求拆解到代码交付的完整开发周期。

---

## 🎯 核心功能

| 功能模块 | 说明 |
|---------|------|
| **🤖 多智能体路由调度** | RouterAgent 智能评估任务类型，自动分派给最合适的子 Agent |
| **📋 需求分析与计划制定** | PMAgent 将模糊需求转化为可执行的开发步骤，生成 plan.md |
| **💻 编程与文件操作** | CoderAgent 编写代码、读写文件、运行命令、Git 版本控制 |
| **🗄️ 数据库与数据格式** | DBAAgent 探查 SQLite/MySQL 数据库，处理 JSON/CSV/YAML 格式转换 |
| **🔍 代码审查与测试** | ReviewerAgent 格式化代码、语法检查、编写并运行 pytest 测试 |
| **🌐 API 调试** | 类似 Postman 的 HTTP 请求工具，支持 GET/POST/PUT/DELETE 等 |
| **🕸️ 动态网页抓取** | 基于 Playwright 无头浏览器，渲染 JavaScript 动态内容 |
| **🧠 记忆管理** | 关键信息持久化存档，支持跨会话检索 |
| **📊 数据格式处理** | JSON/CSV/YAML 解析、验证、格式化、互转、路径查询 |
| **📂 文件备份与恢复** | 自动备份、版本管理、差异对比 |
| **🔒 安全沙盒** | 所有文件操作限制在安全目录内，高危命令黑名单拦截 |

---

## 🏗️ 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.10+** | 开发语言 |
| **LangChain** | LLM 调用框架，Tool 绑定与消息管理 |
| **DeepSeek Chat API** | 大语言模型（通过 OpenAI 兼容接口调用） |
| **Playwright** | 无头浏览器，动态网页渲染抓取 |
| **requests** | HTTP 请求库，API 调试工具 |
| **autopep8 / flake8** | 代码格式化与质量检查 |
| **pytest** | 单元测试框架 |
| **python-dotenv** | 环境变量管理 |
| **chardet** | 文件编码自动检测 |
| **SQLite / MySQL** | 数据库探查支持 |

---

## 📁 项目结构

```
D:\ai_workspace\v43
├── 📄 main.py                          # 🚀 主程序入口，多智能体路由启动
├── 📄 .env                             # 🔑 环境变量（API Key 配置）
├── 📄 __init__.py                      # 包初始化
│
├── 📁 agents/                          # 🤖 智能体模块
│   ├── __init__.py                     # Agent 包导出
│   ├── router_agent.py                 # 🚦 RouterAgent - 路由调度核心
│   ├── coder_agent.py                  # 💻 CoderAgent - 编程/文件操作
│   ├── dba_agent.py                    # 🗄️ DBAAgent - 数据库/数据格式
│   ├── reviewer_agent.py               # 🔍 ReviewerAgent - 代码审查/测试
│   └── pm_agent.py                     # 📋 PMAgent - 技术产品经理
│
├── 📁 core/                            # ⚙️ 核心模块
│   ├── __init__.py                     # Core 包导出
│   ├── config.py                       # 🔒 安全策略与全局配置
│   ├── llm.py                          # 🤖 大模型初始化
│   ├── utils.py                        # 🔧 辅助函数（超时、截断、安全路径等）
│   └── agent_memory.py                 # 🧠 Agent 记忆管理器
│
├── 📁 tools/                           # 🛠️ 工具集
│   ├── __init__.py                     # 工具包导出与注册
│   ├── file_tools.py                   # 📂 文件操作工具集
│   ├── git_tools.py                    # 🗃️ Git 版本控制工具
│   ├── db_tools.py                     # 🗄️ 数据库探查工具
│   ├── data_tools.py                   # 📊 数据格式处理工具
│   ├── search_tools.py                 # 🔍 网络搜索工具
│   ├── memory_tools.py                 # 🧠 记忆管理工具
│   ├── api_tools.py                    # 🌐 API 调试工具（类似 Postman）
│   └── browser_tools.py                # 🕸️ 动态网页抓取工具（Playwright）
│
└── 📁 agent_history_archive/           # 📦 记忆存档目录
    └── memory_index.json               # 记忆索引文件
```

---

## 🧠 智能体架构

```
                    ┌─────────────────────────────────┐
                    │        用户输入 / 终端命令         │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      🚦 RouterAgent              │
                    │    （路由调度核心）                │
                    │  评估任务类型 → 分派给子 Agent    │
                    └──────┬──────┬──────┬──────┬─────┘
                           │      │      │      │
              ┌────────────┘      │      │      └────────────┐
              │                   │      │                   │
    ┌─────────▼────────┐  ┌──────▼──┐ ┌─▼──────────┐  ┌─────▼─────────┐
    │  📋 PMAgent      │  │ 💻      │ │ 🗄️         │  │ 🔍             │
    │  技术产品经理     │  │CoderAgent│ │ DBAAgent   │  │ ReviewerAgent  │
    │  需求分析        │  │编程开发  │ │ 数据库/格式 │  │ 代码审查/测试  │
    │  生成 plan.md    │  │文件操作  │ │ 格式转换    │  │ 语法检查       │
    └──────────────────┘  └─────────┘ └────────────┘  └────────────────┘
```

### 各智能体职责

| 智能体 | 职责 | 绑定工具 |
|--------|------|---------|
| **🚦 RouterAgent** | 路由调度核心，评估任务类型，转发给子 Agent | `delegate_task` 委托工具 |
| **📋 PMAgent** | 技术产品经理，将模糊需求转化为开发计划 | `plan_progress`, `write_local_file` |
| **💻 CoderAgent** | 编程/文件操作，编写代码、运行命令、Git 管理 | 文件操作、终端、Git、搜索、记忆等 20+ 工具 |
| **🗄️ DBAAgent** | 数据库探查、数据格式处理、格式互转 | `inspect_database`, `data_format_tool`, `file_backup_tool` 等 |
| **🔍 ReviewerAgent** | 代码格式化、语法检查、编写并运行 pytest 测试 | `code_format_tool`, `check_python_syntax`, `pytest` 等 |

---

## 🔧 安装与运行

### 环境要求

- Python 3.10 或更高版本
- 网络连接（用于调用 DeepSeek API）

### 安装步骤

1. **克隆或进入项目目录**

```bash
cd D:\ai_workspace\v43
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

核心依赖包括：
- `langchain-core`, `langchain-openchain` — LangChain 框架
- `python-dotenv` — 环境变量管理
- `requests` — HTTP 请求
- `playwright` — 动态网页抓取（可选）
- `autopep8`, `flake8` — 代码格式化与检查
- `pytest` — 单元测试
- `chardet` — 文件编码检测

> **注意**：如果使用 Playwright 动态网页抓取功能，还需安装浏览器：
> ```bash
> playwright install chromium
> ```

3. **配置 API Key**

编辑 `.env` 文件，填入你的 API Key：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here
```

> 系统默认使用 DeepSeek Chat API，通过 OpenAI 兼容接口调用。

### 运行方式

#### 方式一：交互式命令行模式

```bash
python main.py
```

进入交互模式后：
- 输入多行任务描述，连续两次回车（空行）自动提交
- 输入单独一行 `EOF` 结束输入
- 输入 `q` 单独一行退出程序
- 5 分钟无输入自动超时

#### 方式二：直接传入任务

```bash
python main.py "请帮我检查当前目录下的 Python 文件"
```

---

## 📖 使用示例

### 示例 1：需求分析与代码开发

```
用户输入：请帮我创建一个 Python 脚本，读取当前目录下的所有 CSV 文件，
          统计每个文件的行数和列数，并输出汇总报告。
```

**处理流程：**
1. RouterAgent 评估 → 识别为宏观新需求 → 转发给 PMAgent
2. PMAgent 分析需求 → 生成 plan.md 开发计划
3. RouterAgent 将具体编程任务转发给 CoderAgent
4. CoderAgent 编写代码、运行测试
5. 最终输出处理结果

### 示例 2：代码审查

```
用户输入：请审查 main.py 的代码质量
```

**处理流程：**
1. RouterAgent 评估 → 识别为代码审查任务 → 转发给 ReviewerAgent
2. ReviewerAgent 格式化代码 → 语法检查 → 编写 pytest 测试 → 运行测试
3. 输出审查报告，包含格式化结果、语法检查结果、测试结果

### 示例 3：数据库探查

```
用户输入：请探查当前目录下的 database.db 数据库结构
```

**处理流程：**
1. RouterAgent 评估 → 识别为数据库任务 → 转发给 DBAAgent
2. DBAAgent 调用 `inspect_database` 探查表结构和数据
3. 输出数据库分析报告

---

## ⚙️ 配置说明

核心配置位于 `core/config.py`，主要配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SAFE_BASE_DIR` | 当前工作目录 | 安全基目录，所有文件操作限制在此目录内 |
| `DEFAULT_MAX_STEPS` | 500 | Agent 最大循环步数 |
| `LLM_TIMEOUT` | 120 秒 | LLM 调用超时时间 |
| `MAX_RETRIES` | 3 | 工具调用最大重试次数 |
| `MAX_OUTPUT_LENGTH` | 20000 字符 | 输出截断长度 |
| `PIP_INDEX_URL` | 清华镜像源 | pip 安装镜像源 |

---

## 🔒 安全机制

- **安全沙盒**：所有文件操作限制在 `SAFE_BASE_DIR` 及子目录内
- **高危命令拦截**：`rm -rf`、`format`、`shutdown` 等命令被黑名单拦截
- **自动备份**：修改文件前自动创建 `.bak` 备份
- **超时保护**：LLM 调用、工具调用、交互输入三重超时保护
- **输出截断**：过长输出自动截断，防止 Token 溢出
- **高低水位线**：消息列表超过阈值时自动截断，确保上下文不溢出

---

## 📝 版本历史

| 版本 | 特性 |
|------|------|
| **v43.0** | 当前版本。多智能体路由架构，5 个专业子 Agent，完整工具链 |
| **v42.0** | 新增 API 调试工具（send_api_request），类似 Postman |
| **v41.0** | 新增动态网页抓取工具（fetch_dynamic_webpage），基于 Playwright |
| **v39.0** | RouterAgent + PMAgent 路由调度架构重构 |
| **v37.0** | 多智能体路由版，子 Agent 独立静态上下文 |
| **v34.0** | 主循环稳定性增强，三重超时保护 |
| **v31.0** | 高低水位线截断、指数退避重试、超时保护 |
| **v23.0** | 代码格式化与质量检查工具 |
| **v21.0** | 文件备份与恢复工具 |
| **v19.0** | 数据格式处理工具（JSON/CSV/YAML） |
| **v18.0** | 记忆管理 + 计划管理工具 |
| **v16.0** | 数据库探查工具 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进本项目。

### 开发规范

1. 所有代码必须通过 `check_python_syntax` 语法检查
2. 使用 `code_format_tool` 格式化代码（行长度 100，缩进 4 空格）
3. 新功能需编写 pytest 单元测试
4. 遵循现有架构风格，保持代码一致性

---

## 📄 许可证

本项目仅供学习和研究使用。

---

<p align="center">
  <b>🚀 企业级多智能体路由系统 v43.0</b><br>
  <i>Powered by LangChain + DeepSeek</i>
</p>
