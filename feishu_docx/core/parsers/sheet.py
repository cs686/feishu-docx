# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：sheet.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 feishu_docx.core.sdk 的 FeishuSDK
[OUTPUT]: 对外提供 SheetParser 类，将飞书电子表格解析为 Markdown
[POS]: parsers 模块的电子表格解析器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional

from rich.console import Console

from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.schema.models import TableMode

console = Console()


class SheetParser:
    """
    飞书电子表格解析器

    将飞书电子表格解析为 Markdown 格式，每个工作表作为一个章节。
    """

    def __init__(
            self,
            spreadsheet_token: str,
            user_access_token: str,
            table_mode: str = "md",
            sdk: Optional[FeishuSDK] = None,
    ):
        """
        初始化电子表格解析器

        Args:
            spreadsheet_token: 电子表格 token
            user_access_token: 用户访问凭证
            table_mode: 表格输出格式 ("html" 或 "md")
            sdk: 可选的 SDK 实例
        """
        self.sdk = sdk or FeishuSDK()
        self.table_mode = TableMode(table_mode)
        self.user_access_token = user_access_token
        self.spreadsheet_token = spreadsheet_token
        self.block_info = {}

    def parse(self) -> str:
        """
        解析电子表格为 Markdown

        Returns:
            Markdown 格式的内容，每个工作表作为一个章节
        """
        sheets = self.sdk.get_sheet_list(
            spreadsheet_token=self.spreadsheet_token,
            user_access_token=self.user_access_token,
        )

        sections = []
        for sheet in sheets:
            sheet_id = sheet.sheet_id
            sheet_title = sheet.title
            resource_type = sheet.resource_type

            if resource_type == "sheet":
                sheet_data = self.sdk.get_sheet(
                    sheet_token=self.spreadsheet_token,
                    sheet_id=sheet_id,
                    user_access_token=self.user_access_token,
                    table_mode=self.table_mode,
                )
            elif resource_type == "bitable":
                # 获取 block info
                if not self.block_info:
                    blocks = self.sdk.get_sheet_metadata(
                        spreadsheet_token=self.spreadsheet_token,
                        user_access_token=self.user_access_token,
                    )
                    if blocks:
                        for block in blocks:
                            block_info = block.get("blockInfo")
                            if block_info:
                                block_token = block_info.get("blockToken", "")
                                self.block_info[block.get("sheetId")] = block_token

                token = self.block_info.get(sheet_id, "")
                if token:
                    token_parts = token.split("_")
                    if len(token_parts) >= 2:
                        sheet_data = self.sdk.get_bitable(
                            app_token=token_parts[0],
                            table_id=token_parts[1],
                            user_access_token=self.user_access_token,
                            table_mode=self.table_mode,
                        )
                    else:
                        console.print(f"[yellow]跳过无效的 block token: {token}[/yellow]")
                        continue
                else:
                    console.print(f"[yellow]跳过无法获取 block token 的工作表: {sheet_title}[/yellow]")
                    continue
            else:
                console.print(f"[yellow]跳过不支持的资源类型: {resource_type}[/yellow]")
                continue

            if sheet_data:
                sections.append(f"# {sheet_title}\n\n{sheet_data}")

        return "\n\n---\n\n".join(sections)
