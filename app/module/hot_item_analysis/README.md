# 分析爆款模块

## 模块定位

`hot_item_analysis` 用于承载对“采集爆款”模块采集下来的视频进行分析的相关能力。

本模块当前只有一个功能：分析已有的爆款视频，并在分析成功后把结果写入知识库 Markdown 文档。

## 模块边界

- 本模块负责分析已有爆款视频。
- 本模块默认以上游 `hot_item_collection` 的采集结果作为分析对象。
- 本模块不负责爆款视频采集、登录态维护或视频下载。
- 本模块不直接调用大模型 CLI，所有大模型调用必须通过 `app/module/ai_cli` 模块完成。

## 模块文件

| 文件 | 说明 |
| --- | --- |
| `__init__.py` | 模块包入口，提供模块标识常量。 |
| `config.json` | 模块运行配置，用于选择分析时使用的 AI CLI。 |
| `standard.md` | 模块功能参数输入与响应规范。 |

## 功能说明

### 分析已有爆款视频

调用方提交来源关联 ID 和本地爆款视频路径后，模块创建分析任务并返回任务状态。

任务 ID 必须通过 `app/tools/id_generator` 的 ID 生成工具生成。分析任务执行时必须通过 `ai_cli` 模块调用配置中选择的本地 AI CLI。分析成功后，模块必须把分析结果写入以下目录：

```text
/Users/lexiyue/software/bunnyai-base/knowledge/分析爆款
```

写入的 Markdown 文档必须遵守以下规范：

- `app/standard/knowledge-md-format-standard.md`
- `app/standard/knowledge-json-source-standard.md`

## 输入示例

```json
{
  "sourceRelationId": "video-001",
  "localHotVideoPath": "/Users/lexiyue/software/bunnyai-base/app/result/hot_item_collection/videos/video-001.mp4"
}
```

## 配置说明

模块配置文件为 `config.json`。

| 字段 | 说明 |
| --- | --- |
| `analysisCliProvider` | 分析视频时使用的 AI CLI，取值必须符合 `ai_cli` 模块支持的 `provider`。 |
| `aiCliConfigPath` | `ai_cli` 模块配置文件路径。 |
| `databasePath` | SQLite 数据库文件路径，用于记录分析任务与结果文件的关系。 |
| `knowledgeOutputDirectory` | 分析结果 Markdown 写入目录。 |
| `executionMode` | 调用 AI CLI 时使用的执行模式。 |
| `timeoutSeconds` | 单次 AI CLI 调用超时时间，单位为秒。 |

## 任务记录

模块应使用 SQLite 数据库记录每次分析任务。任务记录至少包含来源关联 ID、任务 ID、任务状态、分析结果 Markdown 路径、使用的 AI CLI 和解析耗时。

同一个来源关联 ID 可以对应多次分析任务，数据库不得对 `source_relation_id` 设置唯一约束。

## 输出文档要求

- 输出目录固定为 `knowledge/分析爆款`。
- 输出文件必须是 Markdown 文件。
- 文件名必须使用英文小写、数字和连字符。
- 一个 Markdown 文档只记录一个爆款视频的分析结果。
- 文档正文必须使用简体中文。
- 文档中不得虚构视频内容、采集结果或分析过程中不存在的信息。
