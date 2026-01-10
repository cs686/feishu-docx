# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：models.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 pydantic 的数据验证框架
[OUTPUT]: 对外提供飞书 Block 类型枚举和 Pydantic 数据模型
[POS]: schema 模块的核心定义，被 parsers 依赖
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from enum import Enum, IntEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ==============================================================================
# 枚举类型
# ==============================================================================
class TableMode(Enum):
    """表格输出模式"""
    MARKDOWN = "md"
    HTML = "html"


class BlockType(IntEnum):
    """飞书文档 Block 类型枚举"""
    PAGE = 1                    # 页面 Block
    TEXT = 2                    # 文本 Block
    HEADING1 = 3                # 标题 1 Block
    HEADING2 = 4                # 标题 2 Block
    HEADING3 = 5                # 标题 3 Block
    HEADING4 = 6                # 标题 4 Block
    HEADING5 = 7                # 标题 5 Block
    HEADING6 = 8                # 标题 6 Block
    HEADING7 = 9                # 标题 7 Block
    HEADING8 = 10               # 标题 8 Block
    HEADING9 = 11               # 标题 9 Block
    BULLET = 12                 # 无序列表 Block
    ORDERED = 13                # 有序列表 Block
    CODE = 14                   # 代码块 Block
    QUOTE = 15                  # 引用 Block
    TODO = 17                   # 待办事项 Block
    BITABLE = 18                # 多维表格 Block
    CALLOUT = 19                # 高亮块 Block
    CHAT_CARD = 20              # 会话卡片 Block
    DIAGRAM = 21                # 流程图 & UML Block
    DIVIDER = 22                # 分割线 Block
    FILE = 23                   # 文件 Block
    GRID = 24                   # 分栏 Block
    GRID_COLUMN = 25            # 分栏列 Block
    IFRAME = 26                 # 内嵌 Block
    IMAGE = 27                  # 图片 Block
    ISV = 28                    # 开放平台小组件 Block
    MINDNOTE = 29               # 思维笔记 Block
    SHEET = 30                  # 电子表格 Block
    TABLE = 31                  # 表格 Block
    TABLE_CELL = 32             # 表格单元格 Block
    VIEW = 33                   # 视图 Block
    QUOTE_CONTAINER = 34        # 引用容器 Block
    TASK = 35                   # 任务 Block
    OKR = 36                    # OKR Block
    OKR_OBJECTIVE = 37          # OKR Objective Block
    OKR_KEY_RESULT = 38         # OKR Key Result Block
    OKR_PROGRESS = 39           # OKR Progress Block
    ADD_ONS = 40                # 新版文档小组件 Block
    JIRA_ISSUE = 41             # Jira 问题 Block
    WIKI_CATALOG = 42           # Wiki 子页面列表 Block（旧版）
    BOARD = 43                  # 画板 Block
    AGENDA = 44                 # 议程 Block
    AGENDA_ITEM = 45            # 议程项 Block
    AGENDA_ITEM_TITLE = 46      # 议程项标题 Block
    AGENDA_ITEM_CONTENT = 47    # 议程项内容 Block
    LINK_PREVIEW = 48           # 链接预览 Block
    SOURCE_SYNCED = 49          # 源同步块
    REFERENCE_SYNCED = 50       # 引用同步块
    SUB_PAGE_LIST = 51          # Wiki 子页面列表(新版)
    AI_TEMPLATE = 52            # AI 模板
    REFERENCE_BLOCK = 53        # 引用 Block


# ==============================================================================
# 文本元素
# ==============================================================================
class TextElementStyle(BaseModel):
    """文本元素样式"""
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    strikethrough: Optional[bool] = False
    underline: Optional[bool] = False
    inline_code: Optional[bool] = False
    link: Optional[Dict[str, str]] = None
    sequence: Optional[str] = None

    @model_validator(mode="after")
    def check_sequence(self):
        if self.sequence == "auto":
            self.sequence = "1"
        return self


class BlockToken(BaseModel):
    """Block Token"""
    token: str


class TextRun(BaseModel):
    """文本内容"""
    content: str
    text_element_style: Optional[TextElementStyle] = None


class MentionUser(BaseModel):
    """@用户"""
    user_id: str


class MentionDoc(BaseModel):
    """@文档"""
    token: str


class LinkPreviewElement(BaseModel):
    """链接预览元素"""
    url: str


class EquationElement(BaseModel):
    """公式元素"""
    content: str


class TextElement(BaseModel):
    """文本元素（包含多种类型）"""
    text_run: Optional[TextRun] = None
    mention_user: Optional[MentionUser] = None
    mention_doc: Optional[MentionDoc] = None
    link_preview: Optional[LinkPreviewElement] = None
    equation: Optional[EquationElement] = None


class TextStyleBody(BaseModel):
    """通用文本类 Payload 结构"""
    elements: List[TextElement] = []
    style: Optional[TextElementStyle] = None


# ==============================================================================
# 特殊 Payload
# ==============================================================================
class CodeStyle(BaseModel):
    """代码块样式"""
    language: Optional[int] = None


class CodeBody(TextStyleBody):
    """代码块 Payload"""
    style: Optional[CodeStyle] = None


class ImageBody(BlockToken):
    """图片 Payload"""
    width: Optional[int] = None
    height: Optional[int] = None


class TableMergeInfo(BaseModel):
    """表格合并信息"""
    row_span: int = 1
    col_span: int = 1


class TableProperty(BaseModel):
    """表格属性"""
    row_size: int
    column_size: int
    column_width: Optional[List[int]] = None
    merge_info: List[TableMergeInfo] = []


class TableBody(BaseModel):
    """表格 Payload"""
    property: Optional[TableProperty] = None


class TodoStyle(BaseModel):
    """待办事项样式"""
    done: Optional[bool] = False


class TodoBody(TextStyleBody):
    """待办事项 Payload"""
    style: Optional[TodoStyle] = None


class CalloutBody(TextStyleBody):
    """高亮块 Payload"""
    background_color: Optional[int] = None


class BoardBody(BlockToken):
    """画板 Payload"""
    align: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ReferenceBody(BlockToken):
    """引用 Block Payload"""
    layout_mode: Optional[str] = None
    view_id: Optional[str] = None


# ==============================================================================
# 核心 Block 定义
# ==============================================================================
class FeishuBlock(BaseModel):
    """飞书文档 Block"""
    block_id: str
    parent_id: str
    block_type: BlockType
    children: List[str] = []

    # Payload 映射
    page: Optional[TextStyleBody] = None
    text: Optional[TextStyleBody] = None
    heading1: Optional[TextStyleBody] = None
    heading2: Optional[TextStyleBody] = None
    heading3: Optional[TextStyleBody] = None
    heading4: Optional[TextStyleBody] = None
    heading5: Optional[TextStyleBody] = None
    heading6: Optional[TextStyleBody] = None
    heading7: Optional[TextStyleBody] = None
    heading8: Optional[TextStyleBody] = None
    heading9: Optional[TextStyleBody] = None
    bullet: Optional[TextStyleBody] = None
    ordered: Optional[TextStyleBody] = None
    code: Optional[CodeBody] = None
    quote: Optional[TextStyleBody] = None
    todo: Optional[TodoBody] = None
    callout: Optional[CalloutBody] = None
    divider: Optional[Dict] = None
    image: Optional[ImageBody] = None
    bitable: Optional[BlockToken] = None
    table: Optional[TableBody] = None
    sheet: Optional[BlockToken] = None
    board: Optional[BoardBody] = None
    quote_block: Optional[Dict] = None
    reference_base: Optional[ReferenceBody] = None

    # 辅助字段 (解析树构建)
    sub_blocks: List["FeishuBlock"] = Field(default_factory=list, exclude=True)

    class Config:
        extra = "ignore"


# 解决递归引用
FeishuBlock.model_rebuild()
