# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：writer.py
# @Date   ：2026/01/18 17:55
# @Author ：leemysw
# 2026/01/18 17:55   Create
# =====================================================
"""
飞书文档写入器

[INPUT]: 依赖 sdk.py 和 converters/md_to_blocks.py
[OUTPUT]: 对外提供 FeishuWriter 类，支持创建文档和写入 Markdown
[POS]: core 模块的高层写入接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from feishu_docx.core.converters import MarkdownToBlocks
from feishu_docx.core.sdk import FeishuSDK


class FeishuWriter:
    """
    飞书文档写入器

    提供高层接口：
    - 创建文档并写入 Markdown 内容
    - 向现有文档追加内容
    - 更新文档特定 Block
    """

    def __init__(self, sdk: Optional[FeishuSDK] = None):
        """
        初始化写入器

        Args:
            sdk: FeishuSDK 实例，不传则自动创建
        """
        self.sdk = sdk or FeishuSDK()
        self.converter = MarkdownToBlocks()

    def create_document(
        self,
        title: str,
        content: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None,
        folder_token: Optional[str] = None,
        user_access_token: str = "",
    ) -> Dict:
        """
        创建文档并写入 Markdown 内容

        Args:
            title: 文档标题
            content: Markdown 内容字符串（与 file_path 二选一）
            file_path: Markdown 文件路径（与 content 二选一）
            folder_token: 目标文件夹 token
            user_access_token: 用户访问凭证

        Returns:
            包含 document_id, url 的字典
        """
        # 创建空白文档
        doc = self.sdk.create_document(title, user_access_token, folder_token)
        document_id = doc["document_id"]

        # 写入内容
        if content or file_path:
            self.write_content(
                document_id=document_id,
                content=content,
                file_path=file_path,
                user_access_token=user_access_token,
            )

        return {
            "document_id": document_id,
            "url": f"https://feishu.cn/docx/{document_id}",
            "title": title,
        }

    def write_content(
        self,
        document_id: str,
        content: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None,
        user_access_token: str = "",
        append: bool = True,
        use_native_api: bool = True,
    ) -> List[Dict]:
        """
        向文档写入 Markdown 内容

        Args:
            document_id: 文档 ID
            content: Markdown 内容字符串
            file_path: Markdown 文件路径
            user_access_token: 用户访问凭证
            append: True 追加到末尾，False 清空后写入
            use_native_api: 使用飞书原生 API 转换（推荐）

        Returns:
            创建的 Block 列表
        """
        # 读取内容
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()
        elif content:
            md_content = content
        else:
            raise ValueError("必须提供 content 或 file_path")

        # 转换为 Block
        if use_native_api:
            # 使用飞书原生 API（更可靠）
            blocks = self.sdk.convert_markdown(md_content, user_access_token)
        else:
            # 使用本地转换器（离线可用）
            blocks = self.converter.convert(md_content)

        if not blocks:
            return []

        # 写入 Block（使用 document_id 作为父 Block）
        return self.sdk.create_blocks(
            document_id=document_id,
            block_id=document_id,
            children=blocks,
            user_access_token=user_access_token,
        )

    def update_block(
        self,
        document_id: str,
        block_id: str,
        content: str,
        user_access_token: str = "",
    ) -> Dict:
        """
        更新指定 Block 的内容

        Args:
            document_id: 文档 ID
            block_id: Block ID
            content: 新的文本内容
            user_access_token: 用户访问凭证

        Returns:
            更新后的 Block
        """
        update_body = {
            "text": {
                "elements": [{"text_run": {"content": content}}]
            }
        }
        return self.sdk.update_block(
            document_id=document_id,
            block_id=block_id,
            update_body=update_body,
            user_access_token=user_access_token,
        )

    def append_markdown(
        self,
        document_id: str,
        content: str,
        user_access_token: str = "",
    ) -> List[Dict]:
        """
        追加 Markdown 内容到文档末尾

        Args:
            document_id: 文档 ID
            content: Markdown 内容
            user_access_token: 用户访问凭证

        Returns:
            创建的 Block 列表
        """
        return self.write_content(
            document_id=document_id,
            content=content,
            user_access_token=user_access_token,
            append=True,
        )
