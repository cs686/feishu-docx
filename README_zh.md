# feishu-docx

<p align="center">
  <strong>中文</strong> | <a href="./README.md">English</a>
</p>

> 🚀 **飞书云文档 → Markdown | AI Agent 友好型知识库导出工具**

[![PyPI version](https://badge.fury.io/py/feishu-docx.svg)](https://badge.fury.io/py/feishu-docx)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 为什么选择 feishu-docx？

**让 AI Agent 读懂你的飞书知识库。**

- 🤖 **为 AI 而生** — 完美支持 Claude/GPT Skills，让 Agent 直接查询飞书文档
- 📄 **全类型覆盖** — 云文档、电子表格、多维表格、知识库，一网打尽
- 🔐 **OAuth 2.0** — 一次授权，Token 自动刷新，告别手动管理
- 🎨 **双重界面** — CLI 命令行 + TUI 终端图形界面，任君选择
- 📦 **开箱即用** — `pip install` 即可使用，零配置开始导出

---

## ⚡ 30秒快速开始

```bash
# 安装
pip install feishu-docx

# 配置凭证（只需一次）
feishu-docx config set --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET

# 授权
feishu-docx auth

# 导出！
feishu-docx export "https://xxx.feishu.cn/wiki/xxx"
```

---

## 🤖 Claude Skills 支持

**让 Claude 直接访问你的飞书知识库！**

本项目已包含 Claude Skills 配置，位于 `.skills/feishu-docx/SKILL.md`。

将此 Skill 复制到你的 Agent 项目中，Claude 就能：
- 📖 读取飞书知识库作为上下文
- 🔍 搜索和引用内部文档
- 📝 *（规划中）* 将对话内容写入飞书

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 📄 云文档导出 | Docx → Markdown，保留格式、图片、表格 |
| 📊 电子表格导出 | Sheet → Markdown 表格 |
| 📋 多维表格导出 | Bitable → Markdown 表格 |
| 📚 知识库导出 | Wiki 节点自动解析，支持嵌套结构 |
| 🖼️ 自动下载图片 | 图片保存到本地，Markdown 相对路径引用 |
| 🔐 OAuth 2.0 | 自动打开浏览器授权，Token 持久化缓存 |
| 🎨 精美 TUI | 基于 Textual 的终端图形界面 |

---

## 📖 使用方式

### CLI 命令行

```bash
# 导出到指定目录
feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs

# 使用 Token（临时）
feishu-docx export "URL" -t your_access_token

# 启动 TUI 界面
feishu-docx tui
```

### Python API

```python
from feishu_docx import FeishuExporter

# OAuth 授权
exporter = FeishuExporter(app_id="xxx", app_secret="xxx")
path = exporter.export("https://xxx.feishu.cn/wiki/xxx", "./output")

# 或直接使用 Token
exporter = FeishuExporter.from_token("user_access_token")
content = exporter.export_content("https://xxx.feishu.cn/docx/xxx")
```

---

## 🔐 配置飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/) 创建应用
2. 添加重定向 URL：`http://127.0.0.1:9527/`
3. 申请以下权限：
   - `docx:document:readonly` - 云文档
   - `wiki:wiki:readonly` - 知识库
   - `sheets:spreadsheet:readonly` - 电子表格
   - `bitable:bitable:readonly` - 多维表格
   - `offline_access` - Token 刷新

4. 保存凭证：
```bash
feishu-docx config set --app-id cli_xxx --app-secret xxx
```

---

## 📖 命令参考

| 命令 | 描述 |
|------|------|
| `export <URL>` | 导出文档为 Markdown |
| `auth` | OAuth 授权 |
| `tui` | TUI 交互界面 |
| `config set` | 设置凭证 |
| `config show` | 查看配置 |
| `config clear` | 清除缓存 |

---

## 🛠️ 开发

```bash
git clone https://github.com/leemysw/feishu-docx.git
cd feishu-docx
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 🗺️ Roadmap

- [x] 云文档/表格/知识库导出
- [x] OAuth 2.0 + Token 刷新
- [x] TUI 终端界面
- [x] Claude Skills 支持
- [ ] 批量导出整个知识空间
- [ ] MCP Server 支持
- [ ] 写入飞书（创建/更新文档）

---

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

---

**⭐ 如果这个项目对你有帮助，请给一个 Star！**
