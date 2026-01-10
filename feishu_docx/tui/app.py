# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：app.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 textual 的 TUI 框架，依赖 feishu_docx.core.exporter 导出器
[OUTPUT]: 对外提供 FeishuDocxApp 类
[POS]: tui 模块的主应用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Log,
    RadioButton,
    RadioSet,
    Static,
)

from feishu_docx.core.exporter import FeishuExporter


# ==============================================================================
# 主屏幕
# ==============================================================================
class MainScreen(Screen):
    """主屏幕"""

    CSS = """
    #main-container {
        padding: 1 2;
        height: 100%;
    }
    
    #title-box {
        height: 5;
        content-align: center middle;
        background: $primary-background;
        border: round $primary;
        margin-bottom: 1;
    }
    
    #title-text {
        text-style: bold;
        color: $text;
    }
    
    .section {
        margin-bottom: 1;
        padding: 1;
        border: round $surface;
    }
    
    .section-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input-row {
        height: auto;
        margin-bottom: 1;
    }
    
    .input-label {
        width: 12;
        padding-right: 1;
    }
    
    .input-field {
        width: 1fr;
    }
    
    #url-input {
        width: 100%;
    }
    
    #output-dir-input {
        width: 100%;
    }
    
    #token-input {
        width: 100%;
    }
    
    #app-id-input {
        width: 50%;
    }
    
    #app-secret-input {
        width: 50%;
    }
    
    #log-container {
        height: 1fr;
        border: round $surface;
        margin-top: 1;
    }
    
    #export-log {
        height: 100%;
        padding: 1;
    }
    
    #button-row {
        height: auto;
        margin-top: 1;
        align: center middle;
    }
    
    #export-btn {
        width: 20;
        margin-right: 2;
    }
    
    #clear-btn {
        width: 16;
    }
    
    RadioSet {
        height: auto;
        width: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # 标题
            with Container(id="title-box"):
                yield Static("🚀 飞书云文档导出 Markdown", id="title-text")

            # 文档 URL
            with Vertical(classes="section"):
                yield Label("📄 文档 URL", classes="section-title")
                yield Input(
                    placeholder="粘贴飞书文档 URL，如 https://xxx.feishu.cn/docx/xxx",
                    id="url-input",
                )

            # 输出设置
            with Vertical(classes="section"):
                yield Label("📁 输出设置", classes="section-title")
                with Horizontal(classes="input-row"):
                    yield Label("输出目录:", classes="input-label")
                    yield Input(
                        value=str(Path.cwd()),
                        id="output-dir-input",
                        classes="input-field",
                    )
                with Horizontal(classes="input-row"):
                    yield Label("表格格式:", classes="input-label")
                    with RadioSet(id="table-format"):
                        yield RadioButton("HTML", value=True, id="format-html")
                        yield RadioButton("Markdown", id="format-md")

            # 认证设置
            with Vertical(classes="section"):
                yield Label("🔐 认证设置", classes="section-title")
                with Horizontal(classes="input-row"):
                    yield Label("Token:", classes="input-label")
                    yield Input(
                        placeholder="user_access_token（可选，优先使用）",
                        password=True,
                        id="token-input",
                        classes="input-field",
                    )
                with Horizontal(classes="input-row"):
                    yield Label("App ID:", classes="input-label")
                    yield Input(
                        placeholder="飞书应用 App ID",
                        value=os.getenv("FEISHU_APP_ID", ""),
                        id="app-id-input",
                    )
                    yield Label("App Secret:", classes="input-label")
                    yield Input(
                        placeholder="飞书应用 App Secret",
                        password=True,
                        value=os.getenv("FEISHU_APP_SECRET", ""),
                        id="app-secret-input",
                    )

            # 日志区域
            with Container(id="log-container"):
                yield Log(id="export-log", highlight=True, auto_scroll=True)

            # 按钮
            with Horizontal(id="button-row"):
                yield Button("📥 开始导出", variant="primary", id="export-btn")
                yield Button("🗑️ 清空日志", variant="default", id="clear-btn")

        yield Footer()

    # def log(self, message: str):
    #     """写入日志"""
    #     log_widget = self.query_one("#export-log", Log)
    #     log_widget.write_line(message)

    @on(Button.Pressed, "#export-btn")
    def handle_export(self):
        """处理导出按钮点击"""
        url = self.query_one("#url-input", Input).value.strip()
        output_dir = self.query_one("#output-dir-input", Input).value.strip()
        token = self.query_one("#token-input", Input).value.strip()
        app_id = self.query_one("#app-id-input", Input).value.strip()
        app_secret = self.query_one("#app-secret-input", Input).value.strip()

        # 获取表格格式
        table_format = "html"
        if self.query_one("#format-md", RadioButton).value:
            table_format = "md"

        if not url:
            self.log("[red]❌ 请输入文档 URL[/red]")
            return

        self.log(f"[blue]📄 开始导出: {url}[/blue]")

        try:
            # 创建导出器
            if token:
                self.log("[dim]使用 Token 认证[/dim]")
                exporter = FeishuExporter.from_token(token)
            elif app_id and app_secret:
                self.log("[dim]使用 OAuth 授权[/dim]")
                exporter = FeishuExporter(app_id=app_id, app_secret=app_secret)
            else:
                self.log("[red]❌ 请提供 Token 或 OAuth 凭证[/red]")
                return

            # 执行导出
            output_path = exporter.export(
                url=url,
                output_dir=output_dir,
                table_format=table_format,  # type: ignore
            )

            self.log(f"[green]✅ 导出成功: {output_path}[/green]")

        except Exception as e:
            self.log(f"[red]❌ 导出失败: {e}[/red]")

    @on(Button.Pressed, "#clear-btn")
    def handle_clear(self):
        """清空日志"""
        log_widget = self.query_one("#export-log", Log)
        log_widget.clear()


# ==============================================================================
# 主应用
# ==============================================================================
class FeishuDocxApp(App):
    """飞书文档导出器 TUI 应用"""

    TITLE = "Feishu Docx"
    SUB_TITLE = "飞书云文档导出 Markdown"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("ctrl+c", "quit", "退出"),
    ]

    def on_mount(self):
        """挂载时推送主屏幕"""
        self.push_screen(MainScreen())


# ==============================================================================
# 入口点
# ==============================================================================
if __name__ == "__main__":
    app = FeishuDocxApp()
    app.run()
