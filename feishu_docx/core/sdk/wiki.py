# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：wiki.py
# @Date   ：2026/01/29 15:10
# @Author ：leemysw
# 2026/02/01 18:30   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 WikiAPI
[POS]: SDK 知识库相关 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
from typing import List, Optional

import lark_oapi as lark
from lark_oapi.api.wiki.v2 import (
    GetNodeSpaceRequest,
    GetNodeSpaceResponse,
    Node,
)
from lark_oapi.core import BaseResponse

from feishu_docx.utils.console import get_console
from .base import SubModule

console = get_console()


class WikiAPI(SubModule):
    """Wiki 知识库 API"""

    def get_node_metadata(self, node_token: str, access_token: str) -> Optional[Node]:
        """获取知识库节点元数据"""
        request = (
            GetNodeSpaceRequest.builder()
            .token(node_token)
            .obj_type("wiki")
            .build()
        )
        option = self._build_option(access_token)
        response: GetNodeSpaceResponse = self.client.wiki.v2.space.get_node(request, option)

        if not response.success():
            self._log_error("wiki.v2.space.get_node", response)
            raise RuntimeError("获取知识库节点失败")

        return response.data.node

    def get_space_nodes(
            self,
            space_id: str,
            access_token: str,
            parent_node_token: Optional[str] = None,
            page_size: int = 50,
            page_token: Optional[str] = None,
    ) -> Optional[dict]:
        """获取知识空间子节点列表"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(f"/open-apis/wiki/v2/spaces/{space_id}/nodes")
            .token_types({self._get_token_type()})
            .build()
        )

        request.add_query("page_size", str(page_size))
        if page_token:
            request.add_query("page_token", page_token)
        if parent_node_token:
            request.add_query("parent_node_token", parent_node_token)

        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("wiki.v2.spaces.nodes.list", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            return resp_json.get("data", {})
        except Exception as e:
            console.print(f"[red]解析知识空间节点列表失败: {e}[/red]")
            return None

    def get_all_space_nodes(
            self,
            space_id: str,
            access_token: str,
            parent_node_token: Optional[str] = None,
    ) -> List[dict]:
        """获取知识空间下的所有子节点"""
        all_nodes = []
        page_token = None
        has_more = True

        while has_more:
            result = self.get_space_nodes(
                space_id=space_id,
                access_token=access_token,
                parent_node_token=parent_node_token,
                page_token=page_token,
            )
            if not result:
                break

            all_nodes.extend(result.get("items", []))
            has_more = result.get("has_more", False)
            page_token = result.get("page_token")

        return all_nodes

    def get_node_by_token(
            self,
            token: str,
            access_token: str,
            obj_type: str = "wiki",
    ) -> Optional[dict]:
        """获取知识空间节点信息"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri("/open-apis/wiki/v2/spaces/get_node")
            .token_types({self._get_token_type()})
            .build()
        )

        request.add_query("token", token)
        if obj_type != "wiki":
            request.add_query("obj_type", obj_type)

        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("wiki.v2.spaces.get_node", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            return resp_json.get("data", {}).get("node", {})
        except Exception as e:
            console.print(f"[red]解析知识空间节点信息失败: {e}[/red]")
            return None
