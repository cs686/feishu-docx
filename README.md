# feishu-docx

<p align="center">
  <a href="./README_zh.md">中文</a> | <strong>English</strong>
</p>

> 🚀 **Feishu/Lark Docs → Markdown | AI Agent-Friendly Knowledge Base Exporter**

[![PyPI version](https://badge.fury.io/py/feishu-docx.svg)](https://badge.fury.io/py/feishu-docx)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Why feishu-docx?

**Let AI Agents read your Feishu/Lark knowledge base.**

- 🤖 **Built for AI** — Works seamlessly with Claude/GPT Skills for document retrieval
- 📄 **Full Coverage** — Documents, Spreadsheets, Bitables, Wiki nodes
- 🔐 **OAuth 2.0** — One-time auth, automatic token refresh
- 🎨 **Dual Interface** — CLI + Beautiful TUI (Textual-based)
- 📦 **Zero Config** — `pip install` and start exporting

---

## ⚡ Quick Start (30 seconds)

```bash
# Install
pip install feishu-docx

# Configure credentials (one-time)
feishu-docx config set --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET

# Authorize
feishu-docx auth

# Export!
feishu-docx export "https://xxx.feishu.cn/wiki/xxx"
```

---

## 🤖 Claude Skills Support

**Enable Claude to access your Feishu knowledge base directly!**

This project includes a Claude Skill at `.skills/feishu-docx/SKILL.md`.

Copy this Skill to your agent project, and Claude can:
- 📖 Read Feishu knowledge base as context
- 🔍 Search and reference internal documents
- 📝 *(Planned)* Write conversation content back to Feishu

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 Document Export | Docx → Markdown with formatting, images, tables |
| 📊 Spreadsheet Export | Sheet → Markdown tables |
| 📋 Bitable Export | Multidimensional tables → Markdown |
| 📚 Wiki Export | Auto-resolve wiki nodes |
| 🖼️ Auto Image Download | Images saved locally with relative paths |
| 🔐 OAuth 2.0 | Browser-based auth, token persistence |
| 🎨 Beautiful TUI | Terminal UI powered by Textual |

---

## 📖 Usage

### CLI

```bash
# Export to specific directory
feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs

# Use token directly
feishu-docx export "URL" -t your_access_token

# Launch TUI
feishu-docx tui
```

### Python API

```python
from feishu_docx import FeishuExporter

# OAuth
exporter = FeishuExporter(app_id="xxx", app_secret="xxx")
path = exporter.export("https://xxx.feishu.cn/wiki/xxx", "./output")

# Or use token directly
exporter = FeishuExporter.from_token("user_access_token")
content = exporter.export_content("https://xxx.feishu.cn/docx/xxx")
```

---

## 🔐 Feishu App Setup

1. Create app at [Feishu Open Platform](https://open.feishu.cn/)
2. Add redirect URL: `http://127.0.0.1:9527/`
3. Request permissions:
   - `docx:document:readonly`
   - `wiki:wiki:readonly`
   - `sheets:spreadsheet:readonly`
   - `bitable:bitable:readonly`
   - `offline_access`

4. Save credentials:
```bash
feishu-docx config set --app-id cli_xxx --app-secret xxx
```

---

## 📖 Commands

| Command | Description |
|---------|-------------|
| `export <URL>` | Export document to Markdown |
| `auth` | OAuth authorization |
| `tui` | Launch TUI interface |
| `config set` | Set credentials |
| `config show` | Show configuration |
| `config clear` | Clear cache |

---

## 🗺️ Roadmap

- [x] Document/Sheet/Wiki export
- [x] OAuth 2.0 + Token refresh
- [x] TUI interface
- [x] Claude Skills support
- [ ] Batch export entire wiki space
- [ ] MCP Server support
- [ ] Write to Feishu (create/update docs)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

**⭐ Star this repo if you find it helpful!**
