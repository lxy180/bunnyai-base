# JSON 与 Markdown 双向转换工具

这个工具用于在块级 JSON 文档和 Markdown 文档之间相互转换。

适合场景：

- 用 JSON 作为结构化数据源，再生成 Markdown 文档。
- 将已有 Markdown 文档解析成 JSON，便于程序处理、批量修改或后续同步。
- 通过 `block id` 标记保留文档块的稳定定位信息。

## 文件位置

```text
app/tools/json_to_md/
  json_to_md.py
  test_json_to_md.py
  README.md
```

## 基本用法

从 JSON 转 Markdown：

```bash
python3 app/tools/json_to_md/json_to_md.py input.json output.md
```

从 Markdown 转 JSON：

```bash
python3 app/tools/json_to_md/json_to_md.py input.md output.json
```

工具默认会根据输入文件后缀判断转换方向：

- `.json`：转换为 Markdown。
- `.md` / `.markdown`：转换为 JSON。

如果输入文件后缀无法判断，可以显式指定方向：

```bash
python3 app/tools/json_to_md/json_to_md.py input.txt output.json --direction md-to-json
python3 app/tools/json_to_md/json_to_md.py input.data output.md --direction json-to-md
```

## 自定义输出路径

转换结果的文件名始终与输入文件名保持一致，只会替换为目标格式后缀。

可以使用第二个位置参数指定输出目录：

```bash
python3 app/tools/json_to_md/json_to_md.py docs/content.md dist
```

也可以使用 `-o` 或 `--output` 指定输出目录：

```bash
python3 app/tools/json_to_md/json_to_md.py docs/content.md -o dist
python3 app/tools/json_to_md/json_to_md.py docs/content.md --output dist
```

上面的命令都会生成：

```text
dist/content.json
```

如果传入的是文件路径，工具也只使用它的目录部分，文件名仍然来自输入文件：

```bash
python3 app/tools/json_to_md/json_to_md.py docs/content.md -o dist/custom.json
```

上面的命令仍然会生成：

```text
dist/content.json
```

如果不传输出路径，工具会在输入文件同目录下生成同名反向格式文件：

```bash
python3 app/tools/json_to_md/json_to_md.py docs/content.md
```

上面的命令会生成：

```text
docs/content.json
```

## JSON 结构

JSON 根对象必须包含 `blocks` 数组：

```json
{
  "blocks": [
    {
      "id": "title",
      "type": "heading",
      "level": 1,
      "text": "产品说明"
    },
    {
      "id": "intro",
      "type": "paragraph",
      "text": "这是产品的基础介绍。"
    },
    {
      "id": "install",
      "type": "code",
      "language": "bash",
      "content": "npm install"
    }
  ]
}
```

## 支持的块类型

### 标题

```json
{
  "type": "heading",
  "level": 2,
  "text": "安装"
}
```

生成：

```md
## 安装
```

### 段落

```json
{
  "type": "paragraph",
  "text": "这是正文内容。"
}
```

### 代码块

```json
{
  "type": "code",
  "language": "bash",
  "content": "npm install"
}
```

### 列表

无序列表：

```json
{
  "type": "list",
  "items": ["安装依赖", "运行脚本"]
}
```

有序列表：

```json
{
  "type": "list",
  "ordered": true,
  "items": ["安装依赖", "运行脚本"]
}
```

嵌套列表和多级混合列表：

```json
{
  "type": "list",
  "items": [
    {
      "text": "准备环境",
      "children": {
        "type": "list",
        "ordered": true,
        "items": ["安装依赖", "运行测试"]
      }
    },
    "完成转换"
  ]
}
```

生成：

```md
- 准备环境
  1. 安装依赖
  2. 运行测试
- 完成转换
```

### 引用

```json
{
  "type": "quote",
  "text": "这是一段引用。"
}
```

### 表格

```json
{
  "type": "table",
  "headers": ["字段", "说明"],
  "rows": [
    ["type", "块类型"],
    ["text", "文本内容"]
  ]
}
```

生成：

```md
| 字段 | 说明 |
| --- | --- |
| type | 块类型 |
| text | 文本内容 |
```

### 链接引用定义

```json
{
  "type": "link_reference",
  "label": "转换工具",
  "url": "app/tools/json_to_md/README.md",
  "title": "工具说明"
}
```

生成：

```md
[转换工具]: app/tools/json_to_md/README.md "工具说明"
```

### Markdown Frontmatter

```json
{
  "type": "frontmatter",
  "content": "title: 产品说明\ntags:\n  - 工具"
}
```

生成：

```md
---
title: 产品说明
tags:
  - 工具
---
```

### 任务列表

```json
{
  "type": "task_list",
  "items": [
    {"text": "完成转换", "checked": true},
    {"text": "补充文档", "checked": false}
  ]
}
```

生成：

```md
- [x] 完成转换
- [ ] 补充文档
```

### 脚注

```json
{
  "type": "footnote",
  "label": "note1",
  "text": "这是脚注内容。"
}
```

生成：

```md
[^note1]: 这是脚注内容。
```

### HTML 片段

```json
{
  "type": "html",
  "content": "<div class=\"note\">\n  <p>提示</p>\n</div>"
}
```

生成：

```html
<div class="note">
  <p>提示</p>
</div>
```

## 块标记

JSON 转 Markdown 时，可以加 `--markers` 输出块标记：

```bash
python3 app/tools/json_to_md/json_to_md.py input.json output.md --markers
```

示例输出：

```md
<!-- block:intro -->
这是产品的基础介绍。
<!-- /block:intro -->
```

块标记也可以包裹多个 Markdown 块，对应 JSON 中的 `group`：

```json
{
  "id": "overview",
  "type": "group",
  "blocks": [
    {"type": "heading", "level": 2, "text": "概述"},
    {"type": "paragraph", "text": "这是概述内容。"}
  ]
}
```

生成：

```md
<!-- block:overview -->
## 概述

这是概述内容。
<!-- /block:overview -->
```

开启 `--markers` 时，JSON 中每个 block 都必须提供 `id`。

Markdown 转 JSON 时，如果 Markdown 中已经存在块标记，工具会保留对应 `id`。

## 调用日志

通过命令行调用工具时，会在工具目录下写入调用日志：

```text
app/tools/json_to_md/call-log.log
```

日志文件使用 `.log` 格式，每一行是一条 JSON 记录。成功和失败都会记录，最多保留最近 50 条。

日志字段：

- `timestamp`：调用时间，格式为 `YYYY-MM-DD HH:mm:ss`。
- `status`：调用结果，值为 `success` 或 `failure`。
- `input`：输入路径。
- `output_argument`：用户传入的输出路径参数。
- `output`：实际生成的输出路径，失败时为 `null`。
- `direction`：显式指定的转换方向，未指定时为 `null`。
- `with_markers`：是否开启块标记输出。
- `error`：失败原因，成功时为 `null`。

示例：

```log
{"timestamp":"2026-05-26 16:00:00","status":"success","input":"docs/content.md","output_argument":"dist","output":"dist/content.json","direction":null,"with_markers":false,"error":null}
```

## Python 调用

```python
from app.tools.json_to_md import convert_file, parse_markdown, render_markdown, run_conversion

convert_file("docs/content.md", "dist/content.json")
convert_file("data/content.json", "dist/content.md", with_markers=True)
run_conversion("docs/content.md", "dist")

document = parse_markdown("# 产品说明\n")
markdown = render_markdown(document)
```

## 测试

运行单元测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest app.tools.json_to_md.test_json_to_md
```
