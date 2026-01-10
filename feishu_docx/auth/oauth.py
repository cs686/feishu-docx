# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：oauth.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 httpx 的 HTTP 客户端，依赖 http.server 的本地回调服务器
[OUTPUT]: 对外提供 OAuth2Authenticator 类，自动完成 OAuth 2.0 授权流程
[POS]: auth 模块的核心实现，负责获取和刷新 user_access_token
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

飞书 OAuth 2.0 流程文档:
- 获取授权码: https://open.feishu.cn/document/authentication-management/access-token/obtain-oauth-code
- 获取 Token: https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token
"""

import json
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from rich.console import Console

console = Console()


# ==============================================================================
# 数据模型
# ==============================================================================
@dataclass
class TokenInfo:
    """Token 信息"""
    access_token: str
    refresh_token: str
    expires_at: float  # Unix 时间戳
    token_type: str = "Bearer"
    scope: str = ""

    def is_expired(self) -> bool:
        """检查 token 是否过期（提前 60 秒）"""
        return time.time() >= self.expires_at - 60

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenInfo":
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=data["expires_at"],
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", ""),
        )


# ==============================================================================
# OAuth 回调服务器
# ==============================================================================
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理 OAuth 回调的 HTTP Handler"""

    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass

    def do_GET(self):
        """处理 GET 请求（OAuth 回调）"""
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if "code" in query:
            # 获取授权码
            self.server.auth_code = query["code"][0]
            self.server.auth_state = query.get("state", [None])[0]
            self._send_success_response()
        else:
            # 授权失败 (用户拒绝授权时 error=access_denied)
            error = query.get("error", ["unknown"])[0]
            self.server.auth_error = error
            self._send_error_response(error)

    def _send_success_response(self):
        """发送成功响应页面"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>授权成功</title>
            <style>
                body { font-family: -apple-system, sans-serif; display: flex; 
                       justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                .card { background: white; padding: 40px 60px; border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; }
                h1 { color: #22c55e; margin-bottom: 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ 授权成功</h1>
                <p>您可以关闭此页面并返回终端</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_error_response(self, error: str):
        """发送错误响应页面"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>授权失败</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; display: flex; 
                       justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: #fee2e2; }}
                .card {{ background: white; padding: 40px 60px; border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.1); text-align: center; }}
                h1 {{ color: #ef4444; margin-bottom: 10px; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>❌ 授权失败</h1>
                <p>错误: {error}</p>
            </div>
        </body>
        </html>
        """
        self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


class OAuthCallbackServer(HTTPServer):
    """OAuth 回调服务器"""

    def __init__(self, port: int = 9527):
        super().__init__(("127.0.0.1", port), OAuthCallbackHandler)  # noqa
        self.auth_code: Optional[str] = None
        self.auth_state: Optional[str] = None
        self.auth_error: Optional[str] = None


# ==============================================================================
# OAuth2 认证器
# ==============================================================================

# 飞书云文档导出所需的权限
DEFAULT_SCOPES = [
    "docx:document:readonly",         # 查看云文档
    "wiki:wiki:readonly",             # 查看知识库
    "drive:drive:readonly",           # 查看云空间文件（图片下载）
    "sheets:spreadsheet:readonly",    # 查看电子表格
    "bitable:app:readonly",           # 查看多维表格
    "board:whiteboard:node:read",     # 查看白板
    "contact:contact.base:readonly",  # 获取用户基本信息（@用户名称）
    "offline_access",                 # 离线访问（获取 refresh_token）
]


class OAuth2Authenticator:
    """
    飞书 OAuth 2.0 认证器

    实现遵循 RFC 6749 标准，支持：
    1. 自动授权：启动本地服务器，打开浏览器完成 OAuth 授权
    2. Token 刷新：使用 refresh_token 自动刷新过期的 access_token
    3. 手动 Token：直接传入 user_access_token

    使用示例：
        # 自动授权
        auth = OAuth2Authenticator(app_id="xxx", app_secret="xxx")
        token = auth.authenticate()

        # 手动 Token
        auth = OAuth2Authenticator.from_token("user_access_token_xxx")
    """

    # 飞书 API 端点 (accounts.feishu.cn 用于授权页面)
    FEISHU_AUTH_URL = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"

    # Lark (海外版) API 端点
    LARK_AUTH_URL = "https://accounts.larksuite.com/open-apis/authen/v1/authorize"
    LARK_TOKEN_URL = "https://open.larksuite.com/open-apis/authen/v2/oauth/token"

    def __init__(
            self,
            app_id: Optional[str] = None,
            app_secret: Optional[str] = None,
            redirect_port: int = 9527,
            cache_dir: Optional[Path] = None,
            scopes: Optional[List[str]] = None,
            is_lark: bool = False,
    ):
        """
        初始化认证器

        Args:
            app_id: 飞书应用 App ID (client_id)
            app_secret: 飞书应用 App Secret (client_secret)
            redirect_port: 本地回调服务器端口
            cache_dir: Token 缓存目录
            scopes: 需要请求的权限列表，默认使用云文档导出所需权限
            is_lark: 是否使用 Lark (海外版)
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://127.0.0.1:{redirect_port}/"
        self.scopes = scopes or DEFAULT_SCOPES
        self.is_lark = is_lark

        # 选择 API 端点
        if is_lark:
            self.auth_url = self.LARK_AUTH_URL
            self.token_url = self.LARK_TOKEN_URL
        else:
            self.auth_url = self.FEISHU_AUTH_URL
            self.token_url = self.FEISHU_TOKEN_URL

        # Token 缓存
        self.cache_dir = cache_dir or Path.home() / ".feishu-docx"
        self.cache_file = self.cache_dir / "token.json"
        self._token_info: Optional[TokenInfo] = None

        # HTTP 客户端
        self._client = httpx.Client(timeout=30)

    @classmethod
    def from_token(cls, access_token: str) -> "OAuth2Authenticator":
        """
        从已有的 user_access_token 创建认证器

        Args:
            access_token: 用户访问凭证

        Returns:
            OAuth2Authenticator 实例
        """
        auth = cls()
        auth._token_info = TokenInfo(
            access_token=access_token,
            refresh_token="",
            expires_at=time.time() + 7200,  # 假设 2 小时有效
        )
        return auth

    def authenticate(self) -> str:
        """
        执行认证流程，获取 user_access_token

        优先从缓存加载，如果过期则自动刷新，否则启动 OAuth 流程。

        Returns:
            user_access_token
        """
        # 1. 尝试从缓存加载
        if self._load_from_cache():
            if not self._token_info.is_expired():
                console.print("[green]✓[/green] 使用缓存的 Token")
                return self._token_info.access_token
            # Token 过期，尝试刷新
            if self._refresh_token():
                console.print("[green]✓[/green] Token 已刷新")
                return self._token_info.access_token

        # 2. 需要重新授权
        if not self.app_id or not self.app_secret:
            raise ValueError("需要提供 app_id 和 app_secret 才能进行 OAuth 授权")

        return self._oauth_flow()

    def get_token(self) -> str:
        """获取当前有效的 token（别名）"""
        return self.authenticate()

    # ==========================================================================
    # 私有方法
    # ==========================================================================
    def _oauth_flow(self) -> str:
        """
        执行完整的 OAuth 授权流程
        
        1. 启动本地 HTTP 服务器监听回调
        2. 构建授权 URL 并打开浏览器
        3. 用户授权后接收 code
        4. 用 code 换取 access_token
        """
        import secrets
        state = secrets.token_urlsafe(16)

        # 1. 启动本地回调服务器
        server = OAuthCallbackServer(self.redirect_port)
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        # 2. 构建授权 URL (遵循飞书文档)
        # https://accounts.feishu.cn/open-apis/authen/v1/authorize?
        #   client_id=xxx&response_type=code&redirect_uri=xxx&scope=xxx&state=xxx
        auth_params = {
            "client_id": self.app_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"

        console.print(f"\n[bold blue]📋 授权链接:[/bold blue]\n{auth_url}\n")
        console.print("[yellow]正在打开浏览器进行授权...[/yellow]")
        webbrowser.open(auth_url)

        # 3. 等待回调
        server_thread.join(timeout=120)  # 最多等待 2 分钟

        if server.auth_error:
            if server.auth_error == "access_denied":
                raise RuntimeError("用户拒绝了授权")
            raise RuntimeError(f"OAuth 授权失败: {server.auth_error}")

        if not server.auth_code:
            raise RuntimeError("OAuth 授权超时，未收到授权码")

        # 验证 state 防止 CSRF
        if server.auth_state != state:
            console.print("[yellow]⚠️ State 不匹配，可能存在安全风险[/yellow]")

        console.print("[green]✓[/green] 收到授权码")

        # 4. 用授权码换取 Token
        return self._exchange_token(server.auth_code)

    def _exchange_token(self, code: str) -> str:
        """
        用授权码换取 access_token
        
        POST https://open.feishu.cn/open-apis/authen/v2/oauth/token
        Content-Type: application/json; charset=utf-8
        """
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        resp = self._client.post(
            self.token_url,
            json=payload,  # 使用 JSON 格式
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        resp.raise_for_status()
        data = resp.json()

        # 检查错误
        if data.get("code", 0) != 0:
            error_msg = data.get("error_description") or data.get("error") or data.get("msg", "未知错误")
            raise RuntimeError(f"获取 Token 失败: {error_msg}")

        if "error" in data:
            raise RuntimeError(f"获取 Token 失败: {data.get('error_description', data['error'])}")

        # 解析 Token
        self._token_info = TokenInfo(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=time.time() + data.get("expires_in", 7200),
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", ""),
        )

        # 保存到缓存
        self._save_to_cache()
        console.print("[green]✓[/green] Token 获取成功并已缓存")
        console.print(f"[dim]权限范围: {self._token_info.scope}[/dim]")

        return self._token_info.access_token

    def _refresh_token(self) -> bool:
        """
        刷新过期的 Token
        
        POST https://open.feishu.cn/open-apis/authen/v2/oauth/token
        grant_type=refresh_token
        """
        if not self._token_info or not self._token_info.refresh_token:
            return False

        if not self.app_id or not self.app_secret:
            return False

        try:
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "refresh_token": self._token_info.refresh_token,
            }

            resp = self._client.post(
                self.token_url,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("code", 0) != 0 or "error" in data:
                return False

            # 注意：刷新后会返回新的 refresh_token，旧的 refresh_token 失效
            self._token_info = TokenInfo(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", ""),
                expires_at=time.time() + data.get("expires_in", 7200),
                token_type=data.get("token_type", "Bearer"),
                scope=data.get("scope", self._token_info.scope),
            )
            self._save_to_cache()
            return True

        except Exception as e:
            console.print(f"[dim]Token 刷新失败: {e}[/dim]")
            return False

    def _load_from_cache(self) -> bool:
        """从缓存加载 Token"""
        if not self.cache_file.exists():
            return False

        try:
            data = json.loads(self.cache_file.read_text())
            self._token_info = TokenInfo.from_dict(data)
            return True
        except Exception:  # noqa
            return False

    def _save_to_cache(self):
        """保存 Token 到缓存"""
        if not self._token_info:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self._token_info.to_dict(), indent=2))
