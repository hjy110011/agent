# tools package
from .file_tools import (
    read_local_file, read_file_by_lines, write_local_file,
    run_terminal_command, list_directory_tree, pip_install,
    check_python_syntax, search_code_ast, grep_search,
    _detect_file_encoding, _run_grep_powershell,
)
from .git_tools import (
    git_init_repo, git_create_branch, git_commit,
    git_diff, git_status, git_log, git_checkout, git_branch_list,
    _find_git, _get_git_env, _run_git,
)
from .db_tools import (
    inspect_database, _inspect_sqlite, _inspect_mysql,
)
from .data_tools import (
    data_format_tool, file_backup_tool, code_format_tool,
    _parse_csv_line, _json_query, _json_to_yaml, _json_to_csv, _csv_query,
)
from .search_tools import (
    read_webpage, web_search,
)
from .memory_tools import (
    agent_memory_archive, agent_memory_retrieve,
    archive_history_step, plan_progress,
)

# 所有工具的完整列表，供 main_agent.py 注册
all_tools = [
    # file_tools
    read_local_file, read_file_by_lines, write_local_file,
    run_terminal_command, list_directory_tree, pip_install,
    check_python_syntax, search_code_ast, grep_search,
    # git_tools
    git_init_repo, git_create_branch, git_commit,
    git_diff, git_status, git_log, git_checkout, git_branch_list,
    # db_tools
    inspect_database,
    # data_tools
    data_format_tool, file_backup_tool, code_format_tool,
    # search_tools
    read_webpage, web_search,
    # memory_tools
    agent_memory_archive, agent_memory_retrieve,
    archive_history_step, plan_progress,
]
