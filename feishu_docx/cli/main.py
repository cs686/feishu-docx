# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：main.py
# @Date   ：2026/01/28 19:00
# @Author ：leemysw
# 2025/01/09 18:30   Create
# 2026/01/28 11:10   Support folder url parsing
# 2026/01/28 12:05   Use safe console output
# 2026/01/28 16:00   Add whiteboard metadata export option
# 2026/01/28 18:00   Add workspace schema and wiki batch export commands
# 2026/01/28 19:00   Fix wiki export: support old doc format, preserve hierarchy
# 2026/02/01 19:20   Refactor - 拆分为多个命令模块
# =====================================================
"""
[INPUT]: 依赖 typer, 各命令子模块
[OUTPUT]: 对外提供 app (Typer 应用) 作为 CLI 入口
[POS]: cli 模块的主入口，组装所有命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import typer

from feishu_docx import __version__
from .common import console

# ==============================================================================
# 创建 Typer 应用
# ==============================================================================
app = typer.Typer(
    name="feishu-docx",
    help="🚀 飞书云文档导出 Markdown 工具",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ==============================================================================
# 版本回调
# ==============================================================================
def version_callback(value: bool):
    if value:
        console.print(f"[bold blue]feishu-docx[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


# ==============================================================================
# 主回调
# ==============================================================================
@app.callback()
def main(
        version: bool = typer.Option(
            None,
            "--version",
            "-v",
            help="显示版本号",
            callback=version_callback,
            is_eager=True,
        ),
):
    """
    🚀 飞书云文档导出 Markdown 工具

    支持导出云文档、电子表格、多维表格、知识库文档。
    """
    pass


# ==============================================================================
# 注册命令 - 导出
# ==============================================================================
from .cmd_export import export, export_wiki_space

app.command()(export)
app.command(name="export-wiki-space")(export_wiki_space)

# ==============================================================================
# 注册命令 - 写入
# ==============================================================================
from .cmd_write import create, write, update

app.command()(create)
app.command()(write)
app.command()(update)

# ==============================================================================
# 注册命令 - APaaS
# ==============================================================================
from .cmd_apaas import export_workspace_schema

app.command(name="export-workspace-schema")(export_workspace_schema)

# ==============================================================================
# 注册命令 - 认证
# ==============================================================================
from .cmd_auth import auth

app.command()(auth)

# ==============================================================================
# 配置命令组
# ==============================================================================
from .cmd_config import config_set, config_show, config_clear

config_app = typer.Typer(help="[dim]❄[/] 配置管理", rich_markup_mode="rich")
app.add_typer(config_app, name="config")

config_app.command("set")(config_set)
config_app.command("show")(config_show)
config_app.command("clear")(config_clear)

# ==============================================================================
# 注册命令 - TUI
# ==============================================================================
from .cmd_tui import tui

app.command()(tui)

# ==============================================================================
# 入口点
# ==============================================================================
if __name__ == "__main__":
    app()
