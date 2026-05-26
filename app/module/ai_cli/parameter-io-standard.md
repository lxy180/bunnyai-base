# AI CLI 模块参数输入输出规范

## 适用范围

本文档用于定义 `app/module/ai_cli` 模块统一调用本地 AI CLI 的参数输入与输出格式。

## 基本约定

- 输入使用 JSON object 作为根节点。
- 字段名使用英文驼峰命名，并与本规范保持一致。
- 说明性文本必须使用简体中文。
- `provider` 当前支持 `codex`、`claude`、`gemini`。
- 关联本地文件必须通过各 CLI 自身的工作区或附件参数传递，不允许把文件路径或文件内容拼接到 `prompt`。
- 关联文件不存在时必须直接拒绝调用。
- 可选数组字段没有数据时使用空数组 `[]`，不使用 `null`。
- 可选字符串字段没有数据时使用空字符串 `""`，不使用 `null`。

## 输入规范

### 输入根对象

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `provider` | `str` | 是 | 无 | 要调用的本地 AI CLI，支持 `codex`、`claude`、`gemini`。 |
| `prompt` | `str` | 是 | 无 | 发送给 AI CLI 的提示词，不得包含关联文件路径或文件内容。 |
| `files` | `list[str]` | 否 | `[]` | 需要关联的本地文件路径列表。 |
| `workingDirectory` | `str` | 否 | 配置值或当前进程目录 | AI CLI 的工作目录；请求中为空时读取配置。 |
| `configPath` | `str` | 否 | 模块内 `config.json` | AI CLI 模块配置文件路径。 |
| `executionMode` | `str` | 否 | `interactive` | 执行模式，支持 `interactive`、`headless`。 |
| `model` | `str` | 否 | `""` | 指定 CLI 模型参数；为空时使用 CLI 默认配置。 |
| `outputFormat` | `str` | 否 | `""` | 输出格式，支持 `text`、`json`、`stream-json`。 |
| `extraArgs` | `list[str]` | 否 | `[]` | 透传给底层 CLI 的额外参数。 |
| `timeoutSeconds` | `int` | 否 | 无 | 调用超时时间，单位为秒。 |

### 输入校验规则

1. 根对象必须是 JSON object，不允许使用数组作为根节点。
2. `provider` 必须是受支持的本地 CLI 名称。
3. `prompt` 必须是非空字符串。
4. `prompt` 不允许包含 `files` 中任一文件的完整路径。
5. `files` 中的每一项必须是已存在的本地文件，不允许传入目录。
6. `workingDirectory` 必须是已存在的本地目录。
7. 请求中未传 `workingDirectory` 时，优先读取 `config.json` 中当前 provider 的 `workingDirectory`，其次读取顶层 `workingDirectory`。
8. 配置中也未设置 `workingDirectory` 时，使用当前进程目录。
9. `executionMode` 必须是 `interactive` 或 `headless`。
10. `outputFormat` 为空时使用 CLI 默认输出格式；不为空时必须是 `text`、`json` 或 `stream-json`。

### 输入示例

```json
{
  "provider": "codex",
  "prompt": "请根据已关联资料输出一份实现建议。",
  "files": ["/Users/lexiyue/Documents/example/需求.md"],
  "workingDirectory": "/Users/lexiyue/Documents/example",
  "configPath": "",
  "executionMode": "headless",
  "model": "",
  "outputFormat": "json",
  "extraArgs": [],
  "timeoutSeconds": 300
}
```

## 输出规范

### 命令构造输出

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `provider` | `str` | 是 | 无 | 实际调用的 CLI 名称。 |
| `args` | `list[str]` | 是 | 无 | 已构造的命令参数数组，可直接传给 `subprocess.run`。 |
| `prompt` | `str` | 是 | 无 | 校验后的提示词。 |
| `cwd` | `str` | 是 | 无 | 实际执行目录。 |
| `associatedFiles` | `list[str]` | 是 | 无 | 已校验的关联文件列表。 |
| `associatedDirectories` | `list[str]` | 是 | 无 | 传给 CLI 的关联目录列表。 |

### 调用执行输出

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `spec` | `CommandSpec` | 是 | 无 | 命令构造结果。 |
| `returncode` | `int` | 是 | 无 | CLI 进程退出码。 |
| `stdout` | `str` | 是 | 无 | CLI 标准输出。 |
| `stderr` | `str` | 是 | 无 | CLI 标准错误输出。 |

### 输出校验规则

1. `args` 中允许出现关联文件路径或关联目录路径，但 `prompt` 中不允许出现。
2. 调用失败时保留 `returncode`、`stdout` 和 `stderr`，由调用方决定是否重试。
3. `check=true` 执行失败时会抛出异常，异常信息必须使用简体中文。
