# Plan: sandbox_v45_hitl 隔离测试环境搭建与CLI人工审批流实现

## 任务概述
在 `sandbox/v45_hitl` 目录下创建当前代码的隔离副本，并实现 CLI 终端的人工审批流（Human-In-The-Loop），对 `write_local_file` 和 `run_terminal_command` 等高危工具的执行进行拦截审批。

---

## 实施步骤

### 步骤 1：创建 sandbox/v45_hitl 目录并复制代码
- **操作**：在项目根目录下新建 `sandbox/v45_hitl/` 文件夹
- **操作**：将当前所有代码文件（除 sandbox 目录自身、.git、__pycache__、venv 等）递归复制到该目录
- **产出**：`sandbox/v45_hitl/` 下拥有完整的独立代码副本

### 步骤 2：在 core/config.py 中新增 ENABLE_HITL 配置项
- **文件**：`sandbox/v45_hitl/core/config.py`
- **操作**：在配置类或全局变量区域新增：
  ```python
  # HITL (Human-In-The-Loop) 人工审批开关
  ENABLE_HITL = True   # True=开启审批流, False=跳过审批
  ```
- **说明**：该开关控制是否启用人工审批，后续所有拦截逻辑均依赖此变量判断

### 步骤 3：设计并实现 HITL 审批拦截器模块
- **文件**：`sandbox/v45_hitl/core/hitl_approval.py`（新建）
- **核心函数**：`request_human_approval(tool_name: str, context: dict) -> tuple[bool, str]`
- **逻辑**：
  1. 检查 `config.ENABLE_HITL`，若为 `False` 则直接返回 `(True, "")`（放行）
  2. 若为 `True`，在终端打印清晰的提示信息：
     ```
     ╔══════════════════════════════════════════════════╗
     ║  ⚠️  HITL 人工审批请求                          ║
     ║  ──────────────────────────────                 ║
     ║  工具: {tool_name}                              ║
     ║  参数: {context}                                ║
     ║  ──────────────────────────────                 ║
     ║  请输入:                                        ║
     ║    Y  - 允许执行                                ║
     ║    N  - 拒绝执行                                ║
     ║    其他 - 作为修改意见返回给大模型              ║
     ╚══════════════════════════════════════════════════╝
     ```
  3. 使用 `input("> ")` 等待用户输入
  4. 解析输入：
     - `Y` / `y` → 返回 `(True, "")`
     - `N` / `n` → 返回 `(False, "执行被用户拒绝")`
     - 其他内容 → 返回 `(False, user_input)`（作为反馈给大模型重新思考）

### 步骤 4：修改 write_local_file 工具函数，集成 HITL 审批
- **文件**：`sandbox/v45_hitl/core/tools.py`（或工具函数所在文件）
- **操作**：在 `write_local_file` 函数体开头（实际执行写文件之前）插入：
  ```python
  from core.hitl_approval import request_human_approval
  from core.config import ENABLE_HITL
  
  if ENABLE_HITL:
      approved, feedback = request_human_approval(
          tool_name="write_local_file",
          context={"file_path": file_path, "content_preview": content[:200]}
      )
      if not approved:
          return {"status": "rejected", "message": feedback}
  ```
- **说明**：拦截发生在实际文件写入之前，确保每次写操作都经过人工确认

### 步骤 5：修改 run_terminal_command 工具函数，集成 HITL 审批
- **文件**：`sandbox/v45_hitl/core/tools.py`（或工具函数所在文件）
- **操作**：在 `run_terminal_command` 函数体开头（实际执行命令之前）插入：
  ```python
  from core.hitl_approval import request_human_approval
  from core.config import ENABLE_HITL
  
  if ENABLE_HITL:
      approved, feedback = request_human_approval(
          tool_name="run_terminal_command",
          context={"command": command}
      )
      if not approved:
          return {"status": "rejected", "message": feedback}
  ```
- **说明**：拦截发生在命令实际执行之前，防止高危命令未经确认直接运行

### 步骤 6：检查所有高危工具调用入口，确保拦截全覆盖
- **操作**：扫描 `sandbox/v45_hitl/core/` 下所有工具函数，识别其他可能的高危操作（如文件删除、网络请求等）
- **操作**：对识别出的其他高危工具同样集成 HITL 审批逻辑
- **产出**：确保所有可能造成破坏的操作都经过人工审批

### 步骤 7：执行 check_python_syntax 语法检查
- **操作**：对 `sandbox/v45_hitl/` 目录下的核心 Python 文件执行语法检查
- **检查清单**：
  - `core/config.py` - 配置项语法
  - `core/hitl_approval.py` - 新增模块语法
  - `core/tools.py` - 修改后的工具函数语法
  - 其他被修改的核心文件
- **产出**：确认所有文件语法正确，无 ImportError、SyntaxError 等

### 步骤 8：更新文档说明
- **文件**：`sandbox/v45_hitl/README.md`（或项目文档）
- **操作**：添加 HITL 模式的使用说明：
  - 如何开启/关闭（修改 `ENABLE_HITL` 配置）
  - 交互流程说明
  - 用户输入的三种响应方式及含义

---

## 验收标准
1. ✅ `sandbox/v45_hitl/` 目录存在且包含完整代码副本
2. ✅ `core/config.py` 中存在 `ENABLE_HITL = True`
3. ✅ 调用 `write_local_file` 时，终端弹出审批提示，等待用户输入
4. ✅ 调用 `run_terminal_command` 时，终端弹出审批提示，等待用户输入
5. ✅ 输入 Y → 工具正常执行；输入 N → 返回"执行被用户拒绝"；输入其他 → 作为反馈返回
6. ✅ 所有核心文件通过 Python 语法检查，无 Bug
