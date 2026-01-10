# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：main.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 typer 的 CLI 框架，依赖 feishu_docx.core.exporter 的导出器
[OUTPUT]: 对外提供 app (Typer 应用) 作为 CLI 入口
[POS]: cli 模块的主入口，定义所有命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from feishu_docx import __version__
from feishu_docx.core.exporter import FeishuExporter
from feishu_docx.auth.oauth import OAuth2Authenticator
from feishu_docx.utils.config import AppConfig, get_config_dir

console = Console()

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
# 辅助函数
# ==============================================================================
def get_credentials(
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    获取凭证（优先级：命令行参数 > 环境变量 > 配置文件）

    Returns:
        (app_id, app_secret)
    """
    # 1. 命令行参数优先
    final_app_id = app_id
    final_app_secret = app_secret

    # 2. 环境变量次之
    if not final_app_id:
        final_app_id = os.getenv("FEISHU_APP_ID")
    if not final_app_secret:
        final_app_secret = os.getenv("FEISHU_APP_SECRET")

    # 3. 配置文件最后
    if not final_app_id or not final_app_secret:
        config = AppConfig.load()
        if not final_app_id:
            final_app_id = config.app_id
        if not final_app_secret:
            final_app_secret = config.app_secret

    return final_app_id, final_app_secret


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
# export 命令
# ==============================================================================
@app.command()
def export(
        url: str = typer.Argument(..., help="飞书文档 URL"),
        output: Path = typer.Option(
            Path("./output"),
            "-o",
            "--output",
            help="输出目录",
            file_okay=False,
            dir_okay=True,
        ),
        filename: Optional[str] = typer.Option(
            None,
            "-n",
            "--name",
            help="输出文件名（不含扩展名）",
        ),
        token: Optional[str] = typer.Option(
            None,
            "-t",
            "--token",
            envvar="FEISHU_ACCESS_TOKEN",
            help="用户访问凭证（或设置环境变量 FEISHU_ACCESS_TOKEN）",
        ),
        app_id: Optional[str] = typer.Option(
            None,
            "--app-id",
            help="飞书应用 App ID（覆盖配置文件）",
        ),
        app_secret: Optional[str] = typer.Option(
            None,
            "--app-secret",
            help="飞书应用 App Secret（覆盖配置文件）",
        ),
        table_format: str = typer.Option(
            "md",
            "--table",
            help="表格输出格式: html / md",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
):
    """
    [green]▶[/] 导出飞书文档为 Markdown


    示例:

        # 使用已配置的凭证导出（推荐，需先运行 feishu-docx config set）\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx"

        # 使用 Token (如: user_access_token) 导出 \n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -t your_token

        # 使用 OAuth 授权（覆盖配置）\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --app-id xxx --app-secret xxx

        # 导出到指定目录 \n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs -n my_doc
    """
    try:
        # 创建导出器
        if token:
            exporter = FeishuExporter.from_token(token)
        else:
            # 获取凭证（命令行参数 > 环境变量 > 配置文件）
            final_app_id, final_app_secret = get_credentials(app_id, app_secret)

            if final_app_id and final_app_secret:
                exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark)
            else:
                console.print(
                    "[red]❌ 需要提供 Token 或 OAuth 凭证[/red]\n\n"
                    "方式一：先配置凭证（推荐）\n"
                    "  [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]\n\n"
                    "方式二：使用 Token (如: user_access_token)\n"
                    "  [cyan]feishu-docx export URL -t your_token[/cyan]\n\n"
                    "方式三：命令行传入\n"
                    "  [cyan]feishu-docx export URL --app-id xxx --app-secret xxx[/cyan]"
                )
                raise typer.Exit(1)

        # 执行导出
        output_path = exporter.export(
            url=url,
            output_dir=output,
            filename=filename,
            table_format=table_format,  # type: ignore
        )

        console.print(Panel(f"✅ 导出完成: [green]{output_path}[/green]", border_style="green"))

    except ValueError as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 导出失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# auth 命令
# ==============================================================================
@app.command()
def auth(
        app_id: Optional[str] = typer.Option(
            None,
            "--app-id",
            help="飞书应用 App ID（覆盖配置文件）",
        ),
        app_secret: Optional[str] = typer.Option(
            None,
            "--app-secret",
            help="飞书应用 App Secret（覆盖配置文件）",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
):
    """
    [yellow]❁[/] 获取授权，获取并缓存 Token

    首次使用前运行此命令进行授权：

        # 使用已配置的凭证（推荐，需先运行 feishu-docx config set）
        feishu-docx auth

        # 或指定凭证
        feishu-docx auth --app-id xxx --app-secret xxx

    授权成功后，Token 将被缓存，后续导出无需再次授权。
    """
    try:
        # 获取凭证
        final_app_id, final_app_secret = get_credentials(app_id, app_secret)

        if not final_app_id or not final_app_secret:
            console.print(
                "[red]❌ 需要提供 OAuth 凭证[/red]\n\n"
                "方式一：先配置凭证（推荐）\n"
                "  [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]\n\n"
                "方式二：命令行传入\n"
                "  [cyan]feishu-docx auth --app-id xxx --app-secret xxx[/cyan]"
            )
            raise typer.Exit(1)

        authenticator = OAuth2Authenticator(
            app_id=final_app_id,
            app_secret=final_app_secret,
            is_lark=lark,
        )

        console.print("[yellow]>[/yellow] 正在进行 OAuth 授权...")
        token = authenticator.authenticate()

        console.print(Panel(
            f"✅ 授权成功！\n\n"
            f"Token 已缓存至: [cyan]{authenticator.cache_file}[/cyan]\n\n"
            f"后续使用 [green]feishu-docx export[/green] 命令将自动使用缓存的 Token。",
            title="授权成功",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"[red]❌ 授权失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# tui 命令
# ==============================================================================
@app.command()
def tui():
    """
    [magenta]✪[/] TUI 交互界面

    提供终端图形界面进行文档导出操作。
    """
    try:
        from feishu_docx.tui.app import FeishuDocxApp
        app_tui = FeishuDocxApp()
        app_tui.run()
    except ImportError as e:
        console.print(f"[red]❌ TUI 模块加载失败: {e}[/red]")
        console.print("[yellow]请确保已安装 textual: pip install textual[/yellow]")
        raise typer.Exit(1)


# ==============================================================================
# config 命令组
# ==============================================================================
config_app = typer.Typer(help="[dim]❄[/] 配置管理", rich_markup_mode="rich")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
        app_id: Optional[str] = typer.Option(
            None,
            "--app-id",
            help="飞书应用 App ID",
        ),
        app_secret: Optional[str] = typer.Option(
            None,
            "--app-secret",
            help="飞书应用 App Secret",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
):
    """
    设置飞书应用凭证

    配置后，export 和 auth 命令将自动使用这些凭证，无需每次传入。

    示例:
        feishu-docx config set --app-id cli_xxx --app-secret xxx
    """
    config = AppConfig.load()

    # 更新配置（只更新传入的值）
    if app_id:
        config.app_id = app_id
    if app_secret:
        config.app_secret = app_secret
    if lark:
        config.is_lark = lark

    # 交互式输入缺失的值
    if not config.app_id:
        config.app_id = typer.prompt("App ID")
    if not config.app_secret:
        config.app_secret = typer.prompt("App Secret", hide_input=True)

    config.save()

    console.print(Panel(
        f"✅ 配置已保存至: [cyan]{config.config_file}[/cyan]\n\n"
        f"App ID: [green]{config.app_id[:10]}...{config.app_id[-4:]}[/green]\n"
        f"App Secret: [dim]已保存（已隐藏）[/dim]\n"
        f"Lark 模式: {'是' if config.is_lark else '否'}\n\n"
        "现在你可以直接运行：\n"
        "  [cyan]feishu-docx auth[/cyan] - 进行 OAuth 授权\n"
        "  [cyan]feishu-docx export URL[/cyan] - 导出文档",
        title="配置成功",
        border_style="green",
    ))


@config_app.command("show")
def config_show():
    """显示当前配置"""
    config = AppConfig.load()

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("来源", style="dim")
    table.add_column("值", style="green")

    # App ID
    app_id_env = os.getenv("FEISHU_APP_ID")
    if app_id_env:
        table.add_row("App ID", "环境变量",
                      f"{app_id_env[:10]}...{app_id_env[-4:]}" if len(app_id_env) > 14 else app_id_env)
    elif config.app_id:
        table.add_row("App ID", "配置文件",
                      f"{config.app_id[:10]}...{config.app_id[-4:]}" if len(config.app_id) > 14 else config.app_id)
    else:
        table.add_row("App ID", "-", "[dim]未设置[/dim]")

    # App Secret
    app_secret_env = os.getenv("FEISHU_APP_SECRET")
    if app_secret_env:
        table.add_row("App Secret", "环境变量", "[dim]已设置（已隐藏）[/dim]")
    elif config.app_secret:
        table.add_row("App Secret", "配置文件", "[dim]已设置（已隐藏）[/dim]")
    else:
        table.add_row("App Secret", "-", "[dim]未设置[/dim]")

    # Access Token
    if os.getenv("FEISHU_ACCESS_TOKEN"):
        table.add_row("Access Token", "环境变量", "[dim]已设置（已隐藏）[/dim]")
    else:
        table.add_row("Access Token", "-", "[dim]未设置[/dim]")

    # Lark 模式
    table.add_row("Lark 模式", "配置文件", "是" if config.is_lark else "否")

    # 缓存位置
    cache_dir = get_config_dir()
    table.add_row("配置文件", "-", "存在" if config.config_file.exists() else "❌ 不存在")
    table.add_row("Token 缓存", "-", "存在" if (cache_dir / "token.json").exists() else "❌ 不存在")
    table.add_row("配置目录", "-", str(cache_dir))

    console.print(table)

    # 提示
    if not config.has_credentials() and not app_id_env:
        console.print("\n[yellow]💡 提示: 运行以下命令配置凭证[/yellow]")
        console.print("   [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]")


@config_app.command("clear")
def config_clear(
        force: bool = typer.Option(False, "--force", "-f", help="跳过确认"),
        token: bool = typer.Option(True, "--token", "-t", help="清除 Token 缓存"),
        config: bool = typer.Option(False, "--config", "-c", help="清除配置文件"),
        all: bool = typer.Option(False, "--all", "-a", help="同时清除配置和 Token 缓存"),
):
    """清除配置和缓存"""
    app_config = AppConfig.load()
    cache_dir = get_config_dir()
    token_file = cache_dir / "token.json"

    has_config = app_config.config_file.exists()
    has_token = token_file.exists()

    if not has_config and not has_token:
        console.print("[yellow]没有可清除的配置或缓存[/yellow]")
        return

    # 确认
    if not force:
        if all or (config and token):
            msg = "确定要清除配置文件和 Token 缓存吗？"
        elif config:
            msg = "确定要清除配置文件吗？（Token 缓存保留，使用 --all 同时清除配置）"
        else:
            msg = "确定要清除 Token 缓存吗？（配置文件保留，使用 --all 同时清除配置）"
        confirm = typer.confirm(msg)
        if not confirm:
            console.print("已取消")
            raise typer.Abort()

    # 清除
    if (all or config) and has_config:
        app_config.clear()
        console.print("[green]✅ 配置文件已清除[/green]")

    if (token or all) and has_token:
        token_file.unlink()
        console.print("[green]✅ Token 缓存已清除[/green]")


# ==============================================================================
# 入口点
# ==============================================================================
if __name__ == "__main__":
    app()
