# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_export.py
# @Date   ：2026/02/01 19:15
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.core.exporter
[OUTPUT]: 对外提供 export, export_wiki_space 命令
[POS]: cli 模块的导出命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from feishu_docx.core.exporter import FeishuExporter
from .common import console, get_credentials

# ==============================================================================
# export 命令
# ==============================================================================


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
        auth_mode: Optional[str] = typer.Option(
            None,
            "--auth-mode",
            help="认证模式: tenant / oauth（覆盖配置文件）",
        ),
        stdout: bool = typer.Option(
            False,
            "--stdout",
            "-c",
            help="直接输出内容到 stdout（不保存文件，适合 AI Agent 使用）",
        ),
        with_block_ids: bool = typer.Option(
            False,
            "--with-block-ids",
            "-b",
            help="在导出的 Markdown 中嵌入 Block ID 注释（用于后续更新文档）",
        ),
        export_board_metadata: bool = typer.Option(
            False,
            "--export-board-metadata",
            help="导出画板节点元数据（包含位置、大小、类型等信息）",
        ),
):
    """
    [green]▶[/] 导出飞书文档为 Markdown


    示例:

        # 使用已配置的凭证导出（推荐，需先运行 feishu-docx config set）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx"

        # 使用 Token (如: user_access_token) 导出 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -t your_token

        # 使用 OAuth 授权（覆盖配置）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --app-id xxx --app-secret xxx

        # 导出到指定目录 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs -n my_doc

        # 直接输出内容（适合 AI Agent）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --stdout

        # 同时导出画板图片和元数据 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --export-board-metadata
    """
    try:
        # 创建导出器
        if token:
            exporter = FeishuExporter.from_token(token)
        else:
            # 获取凭证（命令行参数 > 环境变量 > 配置文件）
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)

            if final_app_id and final_app_secret:
                exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark, auth_mode=final_auth_mode)
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
        if stdout:
            # 直接输出内容到 stdout
            content = exporter.export_content(
                url=url,
                table_format=table_format,  # type: ignore
                export_board_metadata=export_board_metadata,
            )
            print(content)
        else:
            # 保存到文件
            output_path = exporter.export(
                url=url,
                output_dir=output,
                filename=filename,
                table_format=table_format,  # type: ignore
                with_block_ids=with_block_ids,
                export_board_metadata=export_board_metadata,
            )
            console.print(Panel(f"✅ 导出完成: [green]{output_path}[/green]", border_style="green"))

    except ValueError as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 导出失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# export-wiki-space 命令
# ==============================================================================


def export_wiki_space(
        space_id_or_url: str = typer.Argument(..., help="知识空间 ID、Wiki URL 或 my_library"),
        output: Path = typer.Option(
            Path("./wiki_export"),
            "-o",
            "--output",
            help="输出目录",
        ),
        parent_node: Optional[str] = typer.Option(
            None,
            "--parent-node",
            help="父节点 token（不传则导出根节点下所有文档）",
        ),
        max_depth: int = typer.Option(
            3,
            "--max-depth",
            help="最大遍历深度",
        ),
        token: Optional[str] = typer.Option(
            None,
            "-t",
            "--token",
            envvar="FEISHU_ACCESS_TOKEN",
            help="用户访问凭证",
        ),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """
    [green]▶[/] 批量导出知识空间下的所有文档

    支持直接输入 Wiki URL，自动提取知识空间 ID。

    示例:

        # 使用 Wiki URL（自动提取 space_id）\\\\n
        feishu-docx export-wiki-space "https://my.feishu.cn/wiki/<token>"

        # 直接使用知识空间 ID\\\\n
        feishu-docx export-wiki-space <space_id>

        # 导出我的文档库\\\\n
        feishu-docx export-wiki-space my_library -o ./my_docs

        # 限制遍历深度\\\\n
        feishu-docx export-wiki-space my_library --max-depth 2
    """
    try:
        # 获取凭证
        if token:
            exporter = FeishuExporter.from_token(token)
            access_token = token
        else:
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
            if not final_app_id or not final_app_secret:
                console.print("[red]❌ 需要提供凭证[/red]")
                raise typer.Exit(1)
            exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark, auth_mode=final_auth_mode)
            access_token = exporter.get_access_token()

        # 解析输入参数，支持 URL、space_id 或 my_library
        space_id = space_id_or_url

        if space_id_or_url.startswith(("http://", "https://")):
            # 输入是 URL，解析并获取 space_id
            console.print("[yellow]> 检测到 Wiki URL，正在自动提取知识空间 ID...[/yellow]")

            try:
                doc_info = exporter.parse_url(space_id_or_url)
            except ValueError as e:
                console.print(f"[red]❌ URL 格式错误: {e}[/red]")
                raise typer.Exit(1)

            if doc_info.doc_type != "wiki":
                console.print(
                    f"[red]❌ 输入的不是 Wiki 链接（类型: {doc_info.doc_type}）[/red]\n"
                    f"[yellow]💡 提示: 请提供 Wiki URL 或直接使用 space_id[/yellow]"
                )
                raise typer.Exit(1)

            node_token = doc_info.doc_id
            console.print(f"[dim]  节点 Token: {node_token}[/dim]")

            # 获取节点信息并提取 space_id
            node_info = exporter.sdk.wiki.get_wiki_node_by_token(
                token=node_token,
                access_token=access_token,
            )

            if not node_info or not node_info.get("space_id"):
                console.print("[red]❌ 无法获取知识空间信息[/red]")
                raise typer.Exit(1)

            space_id = node_info.get("space_id")
            console.print(f"[green]✓ 成功提取知识空间 ID:[/green] {space_id}")

            if node_info.get("title"):
                console.print(f"[dim]  页面标题: {node_info.get('title')}[/dim]")

        console.print(f"[blue]> 知识空间 ID:[/blue] {space_id}")
        console.print(f"[blue]> 输出目录:[/blue] {output}")
        console.print(f"[blue]> 最大深度:[/blue] {max_depth}")

        # 创建输出目录
        output.mkdir(parents=True, exist_ok=True)

        exported_count = 0
        failed_count = 0

        # 确定域名
        domain = "larksuite.com" if lark else "my.feishu.cn"

        # 递归遍历节点
        def traverse_nodes(parent_token: Optional[str] = None, depth: int = 0, current_path: Path = output):
            nonlocal exported_count, failed_count

            if depth > max_depth:
                return

            console.print(f"[yellow]> 正在遍历第 {depth} 层: {current_path.name}...[/yellow]")

            # 获取子节点列表
            nodes = exporter.sdk.wiki.get_all_wiki_space_nodes(
                space_id=space_id,
                access_token=access_token,
                parent_node_token=parent_token,
            )

            if not nodes:
                return

            for node in nodes:
                node_token = node.get("node_token")
                obj_type = node.get("obj_type")
                obj_token = node.get("obj_token")
                title = node.get("title", "untitled")
                has_child = node.get("has_child", False)

                # 清理文件名中的非法字符
                safe_title = title.replace("/", "_").replace("\\", "_")

                # 判断是否为文档类型
                if obj_type in ["doc", "docx", "sheet", "bitable"]:
                    try:
                        # 构建文档 URL
                        url = f"https://{domain}/{obj_type}/{obj_token}"

                        # 如果有子节点，创建子目录并导出
                        if has_child:
                            # 创建以文档名命名的子目录
                            doc_dir = current_path / safe_title
                            doc_dir.mkdir(parents=True, exist_ok=True)

                            # 导出文档到子目录
                            file_path = exporter.export(
                                url=url,
                                output_dir=doc_dir,
                                filename=safe_title,
                                silent=True,
                            )
                            exported_count += 1
                            console.print(f"[green]✓ 已导出:[/green] {safe_title} → {doc_dir.relative_to(output)}")

                            # 递归处理子节点
                            traverse_nodes(node_token, depth + 1, doc_dir)
                        else:
                            # 无子节点，直接导出到当前目录
                            file_path = exporter.export(
                                url=url,
                                output_dir=current_path,
                                filename=safe_title,
                                silent=True,
                            )
                            exported_count += 1
                            console.print(f"[green]✓ 已导出:[/green] {safe_title}")
                    except Exception as e:
                        failed_count += 1
                        console.print(f"[red]✗ 导出失败:[/red] {safe_title} - {e}")
                else:
                    # 非文档类型（如文件夹），只递归处理子节点
                    if has_child:
                        # 为文件夹创建子目录
                        folder_dir = current_path / safe_title
                        folder_dir.mkdir(parents=True, exist_ok=True)
                        console.print(f"[cyan]📁 文件夹:[/cyan] {safe_title}")
                        traverse_nodes(node_token, depth + 1, folder_dir)

        # 开始遍历
        traverse_nodes(parent_node)

        # 输出统计
        console.print(Panel(
            f"✅ 导出完成!\n\n"
            f"[green]成功:[/green] {exported_count} 个文档\n"
            f"[red]失败:[/red] {failed_count} 个文档\n"
            f"[blue]输出目录:[/blue] {output}",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"[red]❌ 批量导出失败: {e}[/red]")
        raise typer.Exit(1)
