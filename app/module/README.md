# 模块说明

`app/module` 用于存放 BunnyAI 的业务模块。每个一级目录代表一个相对独立的模块，模块内可以包含配置文件、功能参数输入与响应规范、模块级 README 或实现代码。

## 模块清单

| 模块 | 说明 | 主要文件 |
| --- | --- | --- |
| `ai_cli` | AI CLI 统一调用入口，用于对接 Claude Code、Codex CLI、Gemini CLI 等命令行 AI 工具。 | `README.md`、`config.json`、`function-parameter-response-standard.md` |
| `hot_item_analysis` | 分析爆款模块，用于分析已有爆款视频，并在成功后写入知识库 Markdown。 | `README.md`、`config.json`、`function-parameter-response-standard.md` |
| `hot_item_collection` | 爆款采集模块，用于承载爆款商品、爆款内容或爆款线索的采集相关能力。 | `README.md`、`config.json`、`function-parameter-response-standard.md` |
| `product_info` | 产品信息模块，用于定义产品信息文档和产品报告的功能参数输入与响应规范，并维护产品信息与产品报告的 SQLite 索引关系。 | `config.json`、`function-parameter-response-standard.md`、`database.py`、`init_database.py` |

## 通用约定

- 新增模块时，应在 `app/module` 下创建独立目录。
- 模块涉及功能参数输入与响应约束时，应提供 `function-parameter-response-standard.md`。
- 模块存在运行配置时，应提供 `config.json`，并避免提交真实账号、密码、密钥等敏感信息。
- 模块说明、规范文档、错误提示和注释必须使用简体中文。
- 模块文档只描述当前已经确定的能力，不记录未确认的功能设想。
