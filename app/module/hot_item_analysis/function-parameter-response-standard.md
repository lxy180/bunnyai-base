# 分析爆款模块功能参数输入与响应规范

## 适用范围

本文档用于定义 `app/module/hot_item_analysis` 模块统一的功能参数输入与响应格式。

本文档只描述数据结构、字段类型、必填规则和填写约束，不描述具体业务流程或代码实现。

## 功能范围

本模块当前只定义一个功能：分析已有的爆款视频。

调用方传入爆款视频 ID 和本地爆款视频路径后，模块返回分析任务状态。任务分析成功后，模块必须把分析结果写入 `knowledge/分析爆款` 目录下的 Markdown 文档。

## 基本约定

- 输入使用 JSON object 作为根节点。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。
- 时间字段统一使用 `yyyy-MM-dd HH:mm:ss` 格式。
- 本模块的大模型调用必须通过 `app/module/ai_cli` 模块完成。
- 本模块不得直接拼接或执行 `codex`、`claude`、`gemini` 等底层 AI CLI 命令。
- 关联视频文件必须通过 `ai_cli` 模块的 `files` 字段传递，不允许把视频路径或视频内容拼接到 `prompt`。

## 输入规范

### 输入根对象

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `hotVideoId` | `str` | 是 | 无 | 爆款视频 ID，对应用户示例中的“爆款视频 id”。 |
| `localHotVideoPath` | `str` | 是 | 无 | 本地爆款视频文件路径，对应用户示例中的“本地爆款视频路径”。 |

### 输入校验规则

1. 根对象必须是 JSON object，不允许使用数组作为根节点。
2. `hotVideoId` 必须是非空字符串。
3. `localHotVideoPath` 必须是非空字符串。
4. `localHotVideoPath` 必须指向已存在的本地视频文件，不允许传入目录。
5. 同一个 `hotVideoId` 对应的分析结果文件名必须稳定，不应在重复分析时生成多个无关文件名。
6. 字段名必须使用 `hotVideoId` 和 `localHotVideoPath`，不使用中文字段名作为正式协议字段。

### 输入示例

```json
{
  "hotVideoId": "video-001",
  "localHotVideoPath": "/Users/lexiyue/software/bunnyai-base/app/result/hot_item_collection/videos/video-001.mp4"
}
```

## 响应规范

### 任务状态响应

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `taskId` | `str` | 是 | 无 | 分析任务 ID。 |
| `hotVideoId` | `str` | 是 | 无 | 爆款视频 ID。 |
| `status` | `str` | 是 | 无 | 任务状态，支持 `pending`、`running`、`succeeded`、`failed`。 |
| `message` | `str` | 是 | `""` | 任务状态说明或失败原因。 |
| `outputMarkdownPath` | `str` | 是 | `""` | 分析成功后生成的 Markdown 文件路径；未成功时为空字符串。 |
| `createdAt` | `str` | 是 | 无 | 任务创建时间。 |
| `startedAt` | `str` | 否 | `""` | 任务开始时间。 |
| `finishedAt` | `str` | 否 | `""` | 任务结束时间。 |

### 响应示例

```json
{
  "taskId": "analysis-20260527153000-video-001",
  "hotVideoId": "video-001",
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
| `knowledgeOutputDirectory` | `str` | 是 | `knowledge/分析爆款` | 分析结果 Markdown 写入目录。 |
| `executionMode` | `str` | 是 | `headless` | 调用 AI CLI 时使用的执行模式。 |
| `timeoutSeconds` | `int` | 是 | `600` | 单次 AI CLI 调用超时时间，单位为秒。 |

### 配置示例

```json
{
  "analysisCliProvider": "codex",
  "aiCliConfigPath": "app/module/ai_cli/config.json",
  "knowledgeOutputDirectory": "knowledge/分析爆款",
  "executionMode": "headless",
  "timeoutSeconds": 600
}
```

### 配置校验规则

1. `analysisCliProvider` 必须是 `ai_cli` 模块支持的 `provider`。
2. `aiCliConfigPath` 必须指向已存在的 `ai_cli` 配置文件。
3. `knowledgeOutputDirectory` 必须指向知识库目录下的 `分析爆款` 目录。
4. `executionMode` 必须符合 `ai_cli` 模块支持的执行模式。
5. `timeoutSeconds` 必须是大于 0 的整数。

## AI CLI 调用约束

本模块调用大模型时，必须构造符合 `app/module/ai_cli/function-parameter-response-standard.md` 的请求。

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
- 文件名建议使用 `hot-video-{normalizedHotVideoId}.md`。
- `normalizedHotVideoId` 应由 `hotVideoId` 规范化得到。
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
| 爆款视频 ID | video-001 |
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
