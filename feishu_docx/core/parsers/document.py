# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：document.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 feishu_docx.core.sdk 的 FeishuSDK, 依赖 feishu_docx.schema 的数据模型
[OUTPUT]: 对外提供 DocumentParser 类，将飞书云文档解析为 Markdown
[POS]: parsers 模块的文档解析器，处理 docx 类型文档
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

from rich.console import Console

from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.schema.code_style import CODE_STYLE_MAP
from feishu_docx.schema.models import BlockType, FeishuBlock, TableMode

console = Console()


class DocumentParser:
    """
    飞书云文档解析器

    将飞书 docx 文档解析为 Markdown 格式。

    使用示例：
        parser = DocumentParser(
            document_id="xxxx",
            user_access_token="xxxx"
        )
        markdown_content = parser.parse()
    """

    def __init__(
        self,
        document_id: str,
        user_access_token: str,
        table_mode: str = "md",
        sdk: Optional[FeishuSDK] = None,
        assets_dir: Optional[Path] = None,
    ):
        """
        初始化文档解析器

        Args:
            document_id: 文档 ID
            user_access_token: 用户访问凭证
            table_mode: 表格输出格式 ("html" 或 "md")
            sdk: 可选的 SDK 实例（用于共享临时目录）
            assets_dir: 资源文件保存目录（图片等）
        """
        self.sdk = sdk or FeishuSDK()
        self.table_mode = TableMode(table_mode)
        self.user_access_token = user_access_token
        self.document_id = document_id
        self.assets_dir = assets_dir
        self.show_progress = True  # 控制是否显示进度

        # Block 缓存
        self.blocks_map: Dict[str, FeishuBlock] = {}
        self.root_block: Optional[FeishuBlock] = None

        # 预处理
        self._preprocess()

    def _preprocess(self):
        """预处理：获取 Block 列表并构建树结构"""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # 获取 Block 列表
            progress.add_task(description="获取文档结构...", total=None)
            raw_data_list = self.sdk.get_document_block_list(
                document_id=self.document_id,
                user_access_token=self.user_access_token,
            )

        console.print(f"  [dim]共 {len(raw_data_list)} 个 Block[/dim]")

        # 1. 反序列化
        for item in raw_data_list:
            try:
                block = FeishuBlock(**item)
                self.blocks_map[block.block_id] = block
            except Exception as e:
                console.print(f"[yellow]跳过无法解析的 Block: {item.get('block_id')} - {e}[/yellow]")
                continue

        # 2. 构建树结构
        for block in self.blocks_map.values():
            if block.children:
                ordered_children = []
                for child_id in block.children:
                    child_block = self.blocks_map.get(child_id)
                    if child_block:
                        ordered_children.append(child_block)
                block.sub_blocks = ordered_children

        # 3. 确定根节点
        self.root_block = next(
            (b for b in self.blocks_map.values() if b.block_type == BlockType.PAGE),
            None,
        )
        if not self.root_block and raw_data_list:
            first_id = raw_data_list[0].get("block_id")
            self.root_block = self.blocks_map.get(first_id)

    def parse(self) -> str:
        """
        解析文档为 Markdown

        Returns:
            Markdown 格式的文档内容
        """
        if not self.root_block:
            console.print("[yellow]> 未找到根 Block，无法解析文档[/yellow]")
            return ""

        title = self._render_text_payload(self.root_block.page)
        body = self._recursive_render(self.root_block)
        return f"# {title}\n{body}"

    def _recursive_render(self, block: FeishuBlock, depth: int = 0) -> str:
        """递归渲染 Block 树"""
        content = ""

        # 1. 渲染自身内容
        self_content = self._render_block_self(block)

        # 2. 特殊容器处理
        if block.block_type == BlockType.TABLE:
            return self._render_table(block)

        # 3. 递归渲染子节点
        children_content = []
        for child in block.sub_blocks:
            child_text = self._recursive_render(child, depth + 1)
            if child_text:
                children_content.append(child_text)

        joined_children = "\n\n".join(children_content) if children_content else ""

        # 4. 组合逻辑
        if self_content:
            content += self_content

        if joined_children:
            bt = block.block_type

            # 引用容器 & Callout：给子内容加前缀
            if bt in [BlockType.QUOTE, BlockType.QUOTE_CONTAINER, BlockType.CALLOUT]:
                prefixed = "\n".join([f"> {line}" for line in joined_children.split("\n")])
                content += f"\n{prefixed}"

            # 列表：子内容缩进
            elif bt in [BlockType.BULLET, BlockType.ORDERED, BlockType.TODO]:
                indented = "\n".join([f"    {line}" for line in joined_children.split("\n")])
                content += f"\n{indented}"

            # 其他：直接追加
            else:
                content += f"\n\n{joined_children}"

        return content.strip()

    def _render_block_self(self, block: FeishuBlock) -> str:
        """根据 block_type 渲染对应的 Markdown"""
        bt = block.block_type

        # 文本类
        if bt == BlockType.TEXT:
            return self._render_text_payload(block.text)

        # 标题类 (3-11)
        if BlockType.HEADING1 <= bt <= BlockType.HEADING9:
            level = bt - 2
            payload = getattr(block, f"heading{level}", None)
            return f"{'#' * level} {self._render_text_payload(payload)}"

        # 列表类
        if bt == BlockType.BULLET:
            return f"- {self._render_text_payload(block.bullet)}"

        if bt == BlockType.ORDERED:
            seq = "1"
            if block.ordered and block.ordered.style:
                seq = block.ordered.style.sequence or "1"
            return f"{seq}. {self._render_text_payload(block.ordered)}"

        if bt == BlockType.TODO:
            status = "[x]" if block.todo and block.todo.style and block.todo.style.done else "[ ]"
            return f"- {status} {self._render_text_payload(block.todo)}"

        # 功能类
        if bt == BlockType.CODE:
            lang = "text"
            if block.code and block.code.style and block.code.style.language:
                lang = CODE_STYLE_MAP.get(block.code.style.language, "text")
            return f"```{lang}\n{self._render_text_payload(block.code)}\n```"

        if bt == BlockType.QUOTE:
            return f"> {self._render_text_payload(block.quote)}"

        if bt == BlockType.CALLOUT:
            return f"> 💡 **{self._render_text_payload(block.callout)}**"

        if bt == BlockType.DIVIDER:
            return "---"

        if bt == BlockType.IMAGE:
            if not block.image or not block.image.token:
                return ""
            file_path = self.sdk.get_image(block.image.token, user_access_token=self.user_access_token)
            if file_path:
                # 使用相对路径：资源目录名/文件名
                if self.assets_dir:
                    rel_path = f"{self.assets_dir.name}/{Path(file_path).name}"
                    return f"![image]({rel_path})"
                return f"![image]({file_path})"
            return ""

        if bt == BlockType.BOARD:
            if not block.board or not block.board.token:
                return ""
            file_path = self.sdk.get_whiteboard(block.board.token, user_access_token=self.user_access_token)
            if file_path:
                # 使用相对路径
                if self.assets_dir:
                    rel_path = f"{self.assets_dir.name}/{Path(file_path).name}"
                    return f"![whiteboard]({rel_path})"
                return f"![whiteboard]({file_path})"
            return ""

        # 电子表格
        if bt == BlockType.SHEET:
            if not block.sheet:
                return ""
            token_parts = block.sheet.token.split("_")
            if len(token_parts) >= 2:
                return self.sdk.get_sheet(
                    sheet_token=token_parts[0],
                    sheet_id=token_parts[1],
                    user_access_token=self.user_access_token,
                    table_mode=self.table_mode,
                ) or ""
            return ""

        # 多维表格
        if bt == BlockType.BITABLE:
            if not block.bitable:
                return ""
            token_parts = block.bitable.token.split("_")
            if len(token_parts) >= 2:
                return self.sdk.get_bitable(
                    app_token=token_parts[0],
                    table_id=token_parts[1],
                    user_access_token=self.user_access_token,
                    table_mode=self.table_mode,
                ) or ""
            return ""

        # 引用 Block
        if bt == BlockType.REFERENCE_BLOCK:
            if not block.reference_base:
                return ""
            token_parts = block.reference_base.token.split("_")
            if len(token_parts) == 2 and token_parts[1].startswith("tb"):
                return self.sdk.get_bitable(
                    app_token=token_parts[0],
                    table_id=token_parts[1],
                    view_id=block.reference_base.view_id,
                    user_access_token=self.user_access_token,
                    table_mode=self.table_mode,
                ) or ""
            return ""

        return ""

    def _render_text_payload(self, payload) -> str:
        """渲染文本类 Payload"""
        if not payload or not hasattr(payload, "elements"):
            return ""

        result = []
        for el in payload.elements:
            text = ""
            if el.text_run:
                text = el.text_run.content
                style = el.text_run.text_element_style
                if style:
                    if style.bold:
                        text = f"**{text}**"
                    if style.italic:
                        text = f"*{text}*"
                    if style.strikethrough:
                        text = f"~~{text}~~"
                    if style.inline_code:
                        text = f"`{text}`"
                    if style.underline:
                        text = f"<u>{text}</u>"
                    if style.link:
                        text = f"[{text}]({unquote(style.link.get('url', ''))})"
            elif el.mention_user:
                user_name = self.sdk.get_user_name(el.mention_user.user_id, self.user_access_token)
                text = f"@{user_name}"
            elif el.mention_doc:
                text = f"[{el.mention_doc.token}]"
            elif el.equation:
                text = f"${el.equation.content}$"
            elif el.link_preview:
                text = f"[{el.link_preview.url}]"

            result.append(text)
        return "".join(result)

    def _render_table(self, table_block: FeishuBlock) -> str:
        """渲染表格 Block"""
        if not table_block.table or not table_block.table.property:
            return "[空表格]"

        props = table_block.table.property
        row_count = props.row_size
        col_count = props.column_size
        merge_infos = props.merge_info

        # 获取所有 Cell Block
        all_cell_blocks = table_block.sub_blocks if table_block.sub_blocks else []
        global_cell_cursor = 0

        # 构建网格
        visited = [[False for _ in range(col_count)] for _ in range(row_count)]
        grid_data: List[List[Optional[Tuple[str, int, int]]]] = [
            [None for _ in range(col_count)] for _ in range(row_count)
        ]

        for r_idx in range(row_count):
            for c_idx in range(col_count):
                if visited[r_idx][c_idx]:
                    continue

                flat_index = r_idx * col_count + c_idx
                if flat_index < len(merge_infos):
                    m_info = merge_infos[flat_index]
                    r_span = m_info.row_span
                    c_span = m_info.col_span
                else:
                    r_span, c_span = 1, 1

                # 标记覆盖区域
                for rs in range(r_span):
                    for cs in range(c_span):
                        if r_idx + rs < row_count and c_idx + cs < col_count:
                            visited[r_idx + rs][c_idx + cs] = True

                # 获取内容
                cell_content = ""
                if global_cell_cursor < len(all_cell_blocks):
                    cell_block = all_cell_blocks[global_cell_cursor]
                    inner_texts = [self._recursive_render(child, depth=0) for child in cell_block.sub_blocks]
                    cell_content = "<br>".join(inner_texts)
                    global_cell_cursor += 1

                grid_data[r_idx][c_idx] = (cell_content, r_span, c_span)

        # 渲染输出
        if self.table_mode == TableMode.HTML:
            return self._render_table_html(grid_data, row_count, col_count)
        else:
            return self._render_table_markdown(grid_data, row_count, col_count)

    @staticmethod
    def _render_table_html(grid_data, row_count: int, col_count: int) -> str:
        """渲染 HTML 表格"""
        html = ["<table>"]
        for r in range(row_count):
            html.append("  <tr>")
            for c in range(col_count):
                data = grid_data[r][c]
                if data:
                    content, r_span, c_span = data
                    attrs = ""
                    if r_span > 1:
                        attrs += f' rowspan="{r_span}"'
                    if c_span > 1:
                        attrs += f' colspan="{c_span}"'
                    html.append(f"    <td{attrs}>{content}</td>")
            html.append("  </tr>")
        html.append("</table>")
        return "\n".join(html)

    @staticmethod
    def _render_table_markdown(grid_data, row_count: int, col_count: int) -> str:
        """渲染 Markdown 表格"""
        md_lines = []
        for r in range(row_count):
            row_strs = []
            for c in range(col_count):
                if grid_data[r][c]:
                    content = grid_data[r][c][0]
                    content = content.replace("|", "\\|").replace("\n", "<br>")
                    row_strs.append(content)
                else:
                    row_strs.append(" ")
            md_lines.append("| " + " | ".join(row_strs) + " |")
            if r == 0:
                md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
        return "\n".join(md_lines)
