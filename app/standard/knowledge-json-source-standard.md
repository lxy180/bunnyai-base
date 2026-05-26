# 知识库 Markdown 的 JSON 源数据规范

## 适用范围

本规范适用于知识库 Markdown 文档对应的 JSON 源数据文件。

JSON 源数据用于作为结构化内容来源，并通过 `app/tools/json_to_md/json_to_md.py` 生成 Markdown 文档。为了保证可同步、可解析、可还原，JSON 必须遵守本文档定义的块级结构。

## 基本原则

- JSON 文件必须使用 UTF-8 编码。
- JSON 根对象必须包含 `blocks` 数组。
- `blocks` 数组中的每个元素代表一个独立 Markdown 块。
- 一个 block 只表达一种块类型，不允许混合多种 Markdown 结构。
- 如果需要生成带块标记的 Markdown，每个 block 都必须提供唯一 `id`。
- 字段名固定使用英文，字段值中的说明性文本必须使用简体中文。
- 不允许在 JSON 中保存转换工具不支持的 Markdown 结构。

## 文件命名规则

JSON 源数据文件名必须与对应 Markdown 文件名保持一致，只替换后缀。

示例：

```text
user-login.md
user-login.json
```

转换工具生成输出时，也必须遵守这个规则。

## 根对象结构

最小结构如下：

```json
{
  "blocks": []
}
```

完整示例：

```json
{
  "blocks": [
    {
      "id": "title",
      "type": "heading",
      "level": 1,
      "text": "用户登录说明"
    },
    {
      "id": "intro",
      "type": "paragraph",
      "text": "本文说明用户登录相关的基础规则。"
    },
    {
      "id": "rules",
      "type": "list",
      "items": [
        "用户必须先完成账号注册。",
        "密码错误次数过多时需要等待后重试。"
      ]
    }
  ]
}
```

## 通用字段

### id

`id` 用于标识一个稳定内容块。

```json
{
  "id": "intro",
  "type": "paragraph",
  "text": "这是产品的基础介绍。"
}
```

要求：

- 如果需要使用 `--markers` 生成 Markdown，`id` 必填。
- 同一个 JSON 文件内，`id` 必须唯一。
- `id` 必须使用英文小写、数字和连字符。
- `id` 应表达内容用途，不要使用无意义编号。

推荐：

```text
title
intro
background
rules
example-command
notice
```

不推荐：

```text
block1
aaa
temp
新段落
```

### type

`type` 表示 Markdown 块类型，必填。

当前允许值：

```text
heading
paragraph
code
list
quote
table
link_reference
frontmatter
group
task_list
footnote
html
```

## 块类型规范

### heading

用于生成 Markdown 标题。

```json
{
  "id": "title",
  "type": "heading",
  "level": 1,
  "text": "用户登录说明"
}
```

字段要求：

- `type`：必填，字符串，固定为 `heading`。
- `level`：选填，数字，标题级别范围为 `1` 到 `6`，默认 `1`。
- `text`：必填，字符串，标题文本。
- `id`：视场景必填，字符串，生成块标记时必填。

生成结果：

```md
# 用户登录说明
```

### paragraph

用于生成普通段落。

```json
{
  "id": "intro",
  "type": "paragraph",
  "text": "本文说明用户登录相关的基础规则。"
}
```

字段要求：

- `type`：必填，字符串，固定为 `paragraph`。
- `text`：必填，字符串，段落文本。
- `id`：视场景必填，字符串，生成块标记时必填。

要求：

- `text` 可以包含换行，但不应用换行表达列表、代码块或引用。
- 如果内容已经是列表、代码或引用，应使用对应 block 类型。

### code

用于生成围栏代码块。

```json
{
  "id": "install-command",
  "type": "code",
  "language": "bash",
  "content": "python3 app/tools/json_to_md/json_to_md.py input.md -o dist"
}
```

字段要求：

- `type`：必填，字符串，固定为 `code`。
- `language`：选填，字符串，代码语言，例如 `bash`、`json`、`text`。
- `content`：必填，字符串，代码块内容。
- `id`：视场景必填，字符串，生成块标记时必填。

生成结果：

````md
```bash
python3 app/tools/json_to_md/json_to_md.py input.md -o dist
```
````

### list

用于生成无序列表或有序列表。

无序列表示例：

```json
{
  "id": "rules",
  "type": "list",
  "items": [
    "规则一",
    "规则二"
  ]
}
```

有序列表示例：

```json
{
  "id": "steps",
  "type": "list",
  "ordered": true,
  "items": [
    "打开输入文件",
    "执行转换命令"
  ]
}
```

字段要求：

- `type`：必填，字符串，固定为 `list`。
- `items`：必填，数组，列表项数组。数组项可以是字符串，也可以是包含 `text` 和 `children` 的对象。
- `ordered`：选填，布尔值，为 `true` 时生成有序列表，否则生成无序列表。
- `id`：视场景必填，字符串，生成块标记时必填。

要求：

- `items` 中每一项必须是单行文本。
- 如果列表项需要子列表，使用对象项的 `children` 字段。
- `children` 必须是一个 `type` 为 `list` 的对象。
- 不允许在 `items` 中嵌套代码块、引用、表格或段落。

嵌套列表和多级混合列表示例：

```json
{
  "id": "steps",
  "type": "list",
  "items": [
    {
      "text": "准备环境",
      "children": {
        "type": "list",
        "ordered": true,
        "items": [
          "安装依赖",
          "运行测试"
        ]
      }
    },
    "完成转换"
  ]
}
```

### quote

用于生成 Markdown 引用。

```json
{
  "id": "notice",
  "type": "quote",
  "text": "转换前请确认文档只使用已支持的 Markdown 块。"
}
```

字段要求：

- `type`：必填，字符串，固定为 `quote`。
- `text`：必填，字符串，引用文本。
- `id`：视场景必填，字符串，生成块标记时必填。

生成结果：

```md
> 转换前请确认文档只使用已支持的 Markdown 块。
```

### table

用于生成 Markdown 表格。

```json
{
  "id": "field-table",
  "type": "table",
  "headers": [
    "字段",
    "说明"
  ],
  "rows": [
    [
      "type",
      "块类型"
    ],
    [
      "text",
      "文本内容"
    ]
  ]
}
```

字段要求：

- `type`：必填，字符串，固定为 `table`。
- `headers`：必填，字符串数组，表头。
- `rows`：必填，二维数组，表格数据行。
- `id`：视场景必填，字符串，生成块标记时必填。

要求：

- `headers` 必须至少包含一个表头。
- `rows` 中每一行都必须是数组。
- 每一行的列数应与 `headers` 保持一致。
- 单元格内容应使用普通文本，不要在单元格中嵌入复杂 Markdown 结构。
- 当前工具不保存表格对齐信息。

生成结果：

```md
| 字段 | 说明 |
| --- | --- |
| type | 块类型 |
| text | 文本内容 |
```

### link_reference

用于生成 Markdown 链接引用定义。

```json
{
  "id": "tool-link",
  "type": "link_reference",
  "label": "转换工具",
  "url": "app/tools/json_to_md/README.md",
  "title": "工具说明"
}
```

字段要求：

- `type`：必填，字符串，固定为 `link_reference`。
- `label`：必填，字符串，引用标签。
- `url`：必填，字符串，链接地址。
- `title`：选填，字符串，链接标题。
- `id`：视场景必填，字符串，生成块标记时必填。

生成结果：

```md
[转换工具]: app/tools/json_to_md/README.md "工具说明"
```

### frontmatter

用于生成 Markdown Frontmatter。

```json
{
  "type": "frontmatter",
  "content": "title: 产品说明\ntags:\n  - 工具"
}
```

字段要求：

- `type`：必填，字符串，固定为 `frontmatter`。
- `content`：必填，字符串，Frontmatter 内部原始文本。

要求：

- Frontmatter 应放在 `blocks` 数组第一项。
- 当前工具只保存原始文本，不解析字段语义。

### group

用于表达一个块标记包裹多个 Markdown 块。

```json
{
  "id": "overview",
  "type": "group",
  "blocks": [
    {
      "type": "heading",
      "level": 2,
      "text": "概述"
    },
    {
      "type": "paragraph",
      "text": "这是概述内容。"
    }
  ]
}
```

字段要求：

- `type`：必填，字符串，固定为 `group`。
- `id`：必填，字符串，块标记 id。
- `blocks`：必填，数组，块标记内部包含的 Markdown 块。

### task_list

用于生成 Markdown 任务列表。

```json
{
  "type": "task_list",
  "items": [
    {
      "text": "完成转换",
      "checked": true
    },
    {
      "text": "补充文档",
      "checked": false
    }
  ]
}
```

字段要求：

- `type`：必填，字符串，固定为 `task_list`。
- `items`：必填，数组，任务项数组。
- `items[].text`：必填，字符串，任务文本。
- `items[].checked`：必填，布尔值，是否完成。

### footnote

用于生成 Markdown 脚注定义。

```json
{
  "type": "footnote",
  "label": "note1",
  "text": "这是脚注内容。"
}
```

字段要求：

- `type`：必填，字符串，固定为 `footnote`。
- `label`：必填，字符串，脚注标签。
- `text`：必填，字符串，脚注内容。

### html

用于保存 HTML 片段。

```json
{
  "type": "html",
  "content": "<div class=\"note\">\n  <p>提示</p>\n</div>"
}
```

字段要求：

- `type`：必填，字符串，固定为 `html`。
- `content`：必填，字符串，HTML 原始内容。

## 块标记与 id 同步规则

当执行以下命令时：

```bash
python3 app/tools/json_to_md/json_to_md.py input.json output.md --markers
```

每个 block 都必须提供 `id`。

JSON：

```json
{
  "id": "intro",
  "type": "paragraph",
  "text": "这是产品的基础介绍。"
}
```

生成 Markdown：

```md
<!-- block:intro -->
这是产品的基础介绍。
<!-- /block:intro -->
```

Markdown 再转换回 JSON 时，会保留这个 `id`。

## 不允许的数据结构

当前 JSON 源数据中不允许出现以下结构：

- 图片类型
- 内联链接类型
- 一个 block 中同时包含标题和正文
- 未在本规范中定义的 `type`

如果知识库需要支持这些结构，应先扩展转换工具，再同步更新本规范。

## 转换命令示例

JSON 转 Markdown：

```bash
python3 app/tools/json_to_md/json_to_md.py knowledge/user-login.json -o dist
```

输出：

```text
dist/user-login.md
```

Markdown 转 JSON：

```bash
python3 app/tools/json_to_md/json_to_md.py knowledge/user-login.md -o dist
```

输出：

```text
dist/user-login.json
```

## 编写检查清单

- 根对象是否包含 `blocks` 数组。
- 每个 block 是否都有合法 `type`。
- 需要块标记时，每个 block 是否都有唯一 `id`。
- `heading.level` 是否在 `1` 到 `6` 之间。
- `paragraph.text`、`heading.text`、`quote.text` 是否为字符串。
- `code.content` 是否为字符串。
- `list.items` 是否为字符串数组，或包含 `text` / `children` 的对象数组。
- 是否没有使用未支持的结构。
- 文件名是否与对应 Markdown 文件名一致。
