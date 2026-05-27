# 分析爆款模块功能参数输入与响应规范

## 适用范围

本文档用于定义 `app/module/hot_item_analysis` 模块统一的功能参数输入与响应格式。

本文档只描述数据结构、字段类型、必填规则和填写约束，不描述具体业务流程或代码实现。

## 功能范围

本模块当前只定义一个功能：分析已有的爆款视频。

调用方传入来源关联 ID 和本地爆款视频路径后，模块返回分析任务状态。任务分析成功后，模块必须把分析结果写入 `knowledge/分析爆款` 目录下的 Markdown 文档。

## 基本约定

- 输入使用 JSON object 作为根节点。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。
- 时间字段统一使用 `yyyy-MM-dd HH:mm:ss` 格式。
- `taskId` 必须通过 `app/tools/id_generator` 的 `generate_id()` 生成。
- `taskId` 对外响应和数据库存储时统一使用十进制字符串，避免 JSON 大整数精度问题。
- 本模块的大模型调用必须通过 `app/module/ai_cli` 模块完成。
- 本模块不得直接拼接或执行 `codex`、`claude`、`gemini` 等底层 AI CLI 命令。
- 关联视频文件必须通过 `ai_cli` 模块的 `files` 字段传递，不允许把视频路径或视频内容拼接到 `prompt`。

## 输入规范

### 输入根对象

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `sourceRelationId` | `str` | 是 | 无 | 来源关联 ID，用于关联上游采集结果或来源数据。 |
| `localHotVideoPath` | `str` | 是 | 无 | 本地爆款视频文件路径，对应用户示例中的“本地爆款视频路径”。 |

### 输入校验规则

1. 根对象必须是 JSON object，不允许使用数组作为根节点。
2. `sourceRelationId` 必须是非空字符串。
3. `localHotVideoPath` 必须是非空字符串。
4. `localHotVideoPath` 必须指向已存在的本地视频文件，不允许传入目录。
5. 同一个 `sourceRelationId` 对应的分析结果文件名必须稳定，不应在重复分析时生成多个无关文件名。
6. 字段名必须使用 `sourceRelationId` 和 `localHotVideoPath`，不使用中文字段名作为正式协议字段。

### 输入示例

```json
{
  "sourceRelationId": "video-001",
  "localHotVideoPath": "/Users/lexiyue/software/bunnyai-base/app/result/hot_item_collection/videos/video-001.mp4"
}
```

## 响应规范

### 任务状态响应

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `taskId` | `str` | 是 | 无 | 分析任务 ID，由 `app/tools/id_generator` 生成后转为十进制字符串。 |
| `sourceRelationId` | `str` | 是 | 无 | 来源关联 ID。 |
| `status` | `str` | 是 | 无 | 任务状态，支持 `pending`、`running`、`succeeded`、`failed`。 |
| `message` | `str` | 是 | `""` | 任务状态说明或失败原因。 |
| `outputMarkdownPath` | `str` | 是 | `""` | 分析成功后生成的 Markdown 文件路径；未成功时为空字符串。 |
| `createdAt` | `str` | 是 | 无 | 任务创建时间。 |
| `startedAt` | `str` | 否 | `""` | 任务开始时间。 |
| `finishedAt` | `str` | 否 | `""` | 任务结束时间。 |

### 响应示例

```json
{
  "taskId": "189560285962577920",
  "sourceRelationId": "video-001",
  "status": "running",
  "message": "分析任务已创建。",
  "outputMarkdownPath": "",
  "createdAt": "2026-05-27 15:30:00",
  "startedAt": "2026-05-27 15:30:01",
  "finishedAt": ""
}
```

### 响应校验规则

1. `status` 只能使用 `pending`、`running`、`succeeded`、`failed`。
2. `status` 为 `succeeded` 时，`outputMarkdownPath` 必须是已写入的 Markdown 文件路径。
3. `status` 为 `failed` 时，`message` 必须说明失败原因。
4. 响应内容不得虚构输入、采集结果或视频分析过程中不存在的数据。

## 配置规范

### 配置文件

模块配置文件为 `app/module/hot_item_analysis/config.json`。

### 配置字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `analysisCliProvider` | `str` | 是 | `codex` | 分析视频时使用的 AI CLI，取值必须符合 `ai_cli` 模块支持的 `provider`。 |
| `aiCliConfigPath` | `str` | 是 | `app/module/ai_cli/config.json` | `ai_cli` 模块配置文件路径。 |
| `databasePath` | `str` | 是 | `app/module/hot_item_analysis/hot_item_analysis.sqlite3` | SQLite 数据库文件路径，用于记录分析任务与结果文件的关系。 |
| `knowledgeOutputDirectory` | `str` | 是 | `knowledge/分析爆款` | 分析结果 Markdown 写入目录。 |
| `executionMode` | `str` | 是 | `headless` | 调用 AI CLI 时使用的执行模式。 |
| `timeoutSeconds` | `int` | 是 | `600` | 单次 AI CLI 调用超时时间，单位为秒。 |

### 配置示例

```json
{
  "analysisCliProvider": "codex",
  "aiCliConfigPath": "app/module/ai_cli/config.json",
  "databasePath": "app/module/hot_item_analysis/hot_item_analysis.sqlite3",
  "knowledgeOutputDirectory": "knowledge/分析爆款",
  "executionMode": "headless",
  "timeoutSeconds": 600
}
```

### 配置校验规则

1. `analysisCliProvider` 必须是 `ai_cli` 模块支持的 `provider`。
2. `aiCliConfigPath` 必须指向已存在的 `ai_cli` 配置文件。
3. `databasePath` 必须指向可写入的 SQLite 数据库文件路径。
4. `knowledgeOutputDirectory` 必须指向知识库目录下的 `分析爆款` 目录。
5. `executionMode` 必须符合 `ai_cli` 模块支持的执行模式。
6. `timeoutSeconds` 必须是大于 0 的整数。

## SQLite 数据库规范

### 数据库文件

模块使用 SQLite 数据库记录分析任务和分析结果之间的关系。默认数据库文件为：

```text
app/module/hot_item_analysis/hot_item_analysis.sqlite3
```

### 表结构

```sql
CREATE TABLE hot_item_analysis_task (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  task_id TEXT NOT NULL UNIQUE,
  source_relation_id TEXT NOT NULL,
  local_hot_video_path TEXT NOT NULL,

  status TEXT NOT NULL CHECK (
    status IN ('pending', 'running', 'succeeded', 'failed')
  ),

  ai_cli_provider TEXT NOT NULL,

  output_markdown_path TEXT NOT NULL DEFAULT '',
  duration_ms INTEGER NOT NULL DEFAULT 0,
  error_message TEXT NOT NULL DEFAULT '',

  created_at TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT '',
  finished_at TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_hot_item_analysis_task_source_relation_id
ON hot_item_analysis_task(source_relation_id);

CREATE INDEX idx_hot_item_analysis_task_status
ON hot_item_analysis_task(status);

CREATE INDEX idx_hot_item_analysis_task_created_at
ON hot_item_analysis_task(created_at);

CREATE INDEX idx_hot_item_analysis_task_source_status_created
ON hot_item_analysis_task(source_relation_id, status, created_at);
```

### 字段说明

| 字段 | 说明 |
| --- | --- |
| `id` | 数据库自增主键，仅用于本地表记录。 |
| `task_id` | 分析任务 ID，必须由 `app/tools/id_generator` 生成。 |
| `source_relation_id` | 来源关联 ID，用于关联上游采集结果或来源数据，不允许设置唯一约束。 |
| `local_hot_video_path` | 本地爆款视频文件路径。 |
| `status` | 任务状态。 |
| `ai_cli_provider` | 本次分析调用的 AI CLI。 |
| `output_markdown_path` | 分析成功后生成的 Markdown 文件路径。 |
| `duration_ms` | 解析耗时，单位毫秒。 |
| `error_message` | 失败原因；未失败时为空字符串。 |
| `created_at` | 任务创建时间。 |
| `started_at` | 任务开始时间。 |
| `finished_at` | 任务结束时间。 |
| `updated_at` | 最近更新时间。 |

### 数据库约束

1. `task_id` 必须唯一。
2. `source_relation_id` 不允许设置唯一约束，同一个来源关联 ID 可以对应多次分析任务。
3. `ai_cli_provider` 只记录调用的 CLI 名称，不记录模型、执行模式或底层命令参数。
4. `duration_ms` 必须记录从任务开始解析到任务结束解析的耗时。
5. `status` 为 `succeeded` 时，`output_markdown_path` 必须记录已生成的 Markdown 文件路径。
6. `status` 为 `failed` 时，`error_message` 必须记录失败原因。

## AI CLI 调用约束

本模块调用大模型时，必须构造符合 `app/module/ai_cli/standard.md` 的请求。

### AI CLI 请求字段映射

| `ai_cli` 字段 | 取值来源 | 说明 |
| --- | --- | --- |
| `provider` | `config.analysisCliProvider` | 使用模块配置选择具体 CLI。 |
| `prompt` | 模块内固定分析提示词 | 提示词不得包含视频文件路径或视频文件内容。 |
| `files` | `[localHotVideoPath]` | 通过关联文件传递视频。 |
| `workingDirectory` | 项目根目录或 `ai_cli` 配置 | 不在本模块中硬编码非必要目录。 |
| `configPath` | `config.aiCliConfigPath` | 使用既有 `ai_cli` 配置。 |
| `executionMode` | `config.executionMode` | 默认使用 `headless`。 |
| `timeoutSeconds` | `config.timeoutSeconds` | 使用模块配置中的超时时间。 |

## Markdown 写入规范

### 写入目录

分析成功后，Markdown 文件必须写入以下目录：

```text
/Users/lexiyue/software/bunnyai-base/knowledge/分析爆款
```

### 文件命名

- 文件名必须使用英文小写、数字和连字符。
- 文件名建议使用 `hot-video-{normalizedSourceRelationId}.md`。
- `normalizedSourceRelationId` 应由 `sourceRelationId` 规范化得到。
- 规范化时应把不符合文件名要求的字符替换为连字符。

### 文档结构

生成的 Markdown 文档必须遵守 `app/standard/knowledge-md-format-standard.md`。

推荐结构如下：

```md
# 爆款视频分析报告

本文档记录一个爆款视频的分析结果。

## 基础信息

| 字段 | 内容 |
| --- | --- |
| 来源关联 ID | video-001 |
| 本地爆款视频路径 | 已通过任务输入提供 |
| 分析时间 | 2026-05-27 15:30:00 |
| AI CLI | codex |

## 分析结论

这里写视频分析的核心结论。

## 内容结构

- 待填写

## 爆款原因

- 待填写

## 可复用要点

- 待填写

## 风险与待确认

- 待填写
```

### 写入校验规则

1. Markdown 正文必须使用简体中文。
2. 一个 Markdown 文档只记录一个爆款视频的分析结果。
3. 标题、段落、列表、代码块、引用和表格之间必须使用一个空行分隔。
4. 表格必须包含表头行和分隔行。
5. 列表项内容应保持为单行文本。
6. 不得使用当前知识库 Markdown 规范未支持的复杂语法。
7. 无法确认的信息必须写为 `待确认`，不得编造。
