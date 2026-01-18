# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：md_to_blocks.py
# @Date   ：2026/01/18 15:40
# @Author ：leemysw
# 2026/01/18 15:40   Create
# =====================================================
"""
Markdown → 飞书 Block 转换器

[INPUT]: 依赖 mistune 的 Markdown 解析器
[OUTPUT]: 对外提供 MarkdownToBlocks 类，将 Markdown 转换为飞书 Block 结构
[POS]: converters 模块的核心转换器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Any, Dict, List, Optional

import mistune


class MarkdownToBlocks:
    """
    Markdown → 飞书 Block 转换器

    使用 mistune 解析 Markdown，转换为飞书文档 Block 结构。
    支持：标题、段落、列表、代码块、引用、分割线、文本样式。
    """

    # Block 类型映射
    BLOCK_TYPE_TEXT = 2
    BLOCK_TYPE_HEADING1 = 3
    BLOCK_TYPE_HEADING2 = 4
    BLOCK_TYPE_HEADING3 = 5
    BLOCK_TYPE_HEADING4 = 6
    BLOCK_TYPE_HEADING5 = 7
    BLOCK_TYPE_HEADING6 = 8
    BLOCK_TYPE_BULLET = 12
    BLOCK_TYPE_ORDERED = 13
    BLOCK_TYPE_CODE = 14
    BLOCK_TYPE_QUOTE = 15
    BLOCK_TYPE_DIVIDER = 22

    # 代码语言映射
    LANGUAGE_MAP = {
        "python": 49,
        "javascript": 22,
        "typescript": 75,
        "java": 21,
        "go": 13,
        "rust": 56,
        "c": 5,
        "cpp": 7,
        "csharp": 8,
        "ruby": 55,
        "php": 46,
        "swift": 68,
        "kotlin": 25,
        "sql": 64,
        "shell": 61,
        "bash": 3,
        "json": 23,
        "yaml": 81,
        "xml": 79,
        "html": 17,
        "css": 9,
        "markdown": 34,
    }

    def __init__(self):
        """初始化转换器"""
        self._md = mistune.create_markdown(renderer=None)

    def convert(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        将 Markdown 文本转换为飞书 Block 列表

        Args:
            markdown_text: Markdown 文本

        Returns:
            飞书 Block 列表（可直接传给 create_blocks API）
        """
        tokens = self._md(markdown_text)
        blocks = []

        for token in tokens:
            block = self._convert_token(token)
            if block:
                if isinstance(block, list):
                    blocks.extend(block)
                else:
                    blocks.append(block)

        return blocks

    def convert_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        读取 Markdown 文件并转换

        Args:
            file_path: 文件路径

        Returns:
            飞书 Block 列表
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return self.convert(f.read())

    def _convert_token(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换单个 token"""
        token_type = token.get("type")

        if token_type == "heading":
            return self._make_heading(token)
        elif token_type == "paragraph":
            return self._make_paragraph(token)
        elif token_type == "list":
            return self._make_list(token)
        elif token_type == "block_code":
            return self._make_code_block(token)
        elif token_type == "block_quote":
            return self._make_quote(token)
        elif token_type == "thematic_break":
            return self._make_divider()

        return None

    def _make_heading(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """创建标题 Block"""
        level = token.get("attrs", {}).get("level", 1)
        level = min(max(level, 1), 6)  # 限制 1-6
        block_type = self.BLOCK_TYPE_HEADING1 + level - 1

        elements = self._extract_text_elements(token.get("children", []))

        heading_key = f"heading{level}"
        return {
            "block_type": block_type,
            heading_key: {"elements": elements},
        }

    def _make_paragraph(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """创建段落 Block"""
        elements = self._extract_text_elements(token.get("children", []))
        return {
            "block_type": self.BLOCK_TYPE_TEXT,
            "text": {"elements": elements},
        }

    def _make_list(self, token: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建列表 Block（每个列表项一个 Block）"""
        ordered = token.get("attrs", {}).get("ordered", False)
        block_type = self.BLOCK_TYPE_ORDERED if ordered else self.BLOCK_TYPE_BULLET
        list_key = "ordered" if ordered else "bullet"

        blocks = []
        for item in token.get("children", []):
            if item.get("type") == "list_item":
                elements = []
                for child in item.get("children", []):
                    if child.get("type") == "paragraph":
                        elements.extend(
                            self._extract_text_elements(child.get("children", []))
                        )

                blocks.append({
                    "block_type": block_type,
                    list_key: {"elements": elements},
                })

        return blocks

    def _make_code_block(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """创建代码块 Block"""
        raw_text = token.get("raw", "")
        lang = token.get("attrs", {}).get("info", "").lower()
        lang_code = self.LANGUAGE_MAP.get(lang, 1)  # 1 = PlainText

        return {
            "block_type": self.BLOCK_TYPE_CODE,
            "code": {
                "elements": [{"text_run": {"content": raw_text}}],
                "style": {"language": lang_code},
            },
        }

    def _make_quote(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """创建引用 Block"""
        elements = []
        for child in token.get("children", []):
            if child.get("type") == "paragraph":
                elements.extend(
                    self._extract_text_elements(child.get("children", []))
                )

        return {
            "block_type": self.BLOCK_TYPE_QUOTE,
            "quote": {"elements": elements},
        }

    def _make_divider(self) -> Dict[str, Any]:
        """创建分割线 Block"""
        return {
            "block_type": self.BLOCK_TYPE_DIVIDER,
            "divider": {},
        }

    def _extract_text_elements(self, children: List[Dict]) -> List[Dict[str, Any]]:
        """从 children 提取文本元素"""
        elements = []

        for child in children:
            child_type = child.get("type")

            if child_type == "text":
                elements.append({
                    "text_run": {"content": child.get("raw", "")}
                })

            elif child_type == "codespan":
                elements.append({
                    "text_run": {
                        "content": child.get("raw", ""),
                        "text_element_style": {"inline_code": True},
                    }
                })

            elif child_type == "strong":
                for sub in child.get("children", []):
                    if sub.get("type") == "text":
                        elements.append({
                            "text_run": {
                                "content": sub.get("raw", ""),
                                "text_element_style": {"bold": True},
                            }
                        })

            elif child_type == "emphasis":
                for sub in child.get("children", []):
                    if sub.get("type") == "text":
                        elements.append({
                            "text_run": {
                                "content": sub.get("raw", ""),
                                "text_element_style": {"italic": True},
                            }
                        })

            elif child_type == "strikethrough":
                for sub in child.get("children", []):
                    if sub.get("type") == "text":
                        elements.append({
                            "text_run": {
                                "content": sub.get("raw", ""),
                                "text_element_style": {"strikethrough": True},
                            }
                        })

            elif child_type == "link":
                url = child.get("attrs", {}).get("url", "")
                text = ""
                for sub in child.get("children", []):
                    if sub.get("type") == "text":
                        text = sub.get("raw", "")
                        break

                elements.append({
                    "text_run": {
                        "content": text or url,
                        "text_element_style": {"link": {"url": url}},
                    }
                })

        return elements
