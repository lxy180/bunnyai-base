# AI CLI 统一调用入口

`app/module/ai_cli` 用于统一调用本机已安装的 Agent CLI，例如 Codex CLI、Claude Code CLI 和 Gemini CLI。

## 当前能力

- 根据统一请求构造本地 CLI 命令。
- 支持 `codex`、`claude`、`gemini` 三种 provider。
- 支持 `interactive` 和 `headless` 两种执行模式。
- 支持关联本地文件，并把文件转换为各 CLI 自带的工作区或附件参数。
- 支持在 `config.json` 中配置默认 `workingDirectory`。
- 支持可选执行命令并返回 `stdout`、`stderr`、`returncode`。

## 文件关联规则

调用要求：如果需要关联文件，必须使用 CLI 自带的关联文件能力，不允许将文件路径或 Markdown 文档内容直接放到提示词。

当前映射如下：

| CLI | 本地文件关联方式 | 说明 |
| --- | --- | --- |
| Codex CLI | `--add-dir`、`--image` | 文件父目录通过 `--add-dir` 关联；图片文件额外使用 `--image`。 |
| Claude Code CLI | `--add-dir` | 文件父目录通过 `--add-dir` 关联。 |
| Gemini CLI | `--include-directories` | 文件父目录通过 `--include-directories` 关联。 |

## Python 调用示例

```python
from app.module.ai_cli import AiCliRequest, build_command, run_ai_cli

request = AiCliRequest(
    provider="codex",
    prompt="请根据已关联资料输出实现建议。",
    files=["/Users/lexiyue/Documents/example/需求.md"],
    workingDirectory="/Users/lexiyue/Documents/example",
    executionMode="headless",
)

spec = build_command(request)
print(spec.args)

result = run_ai_cli(request)
print(result.stdout)
```

## 工作目录配置

请求中传入 `workingDirectory` 时优先使用请求值；未传时读取 `config.json`。可以设置顶层默认值，也可以给某个 CLI 单独设置：

```json
{
  "workingDirectory": "/Users/lexiyue/Documents/example",
  "providers": {
    "codex": {
      "workingDirectory": "/Users/lexiyue/Documents/codex-workspace"
    }
  }
}
```

provider 级配置优先于顶层配置；两者都为空时使用当前进程目录。

## 命令行调用示例

```bash
python3 -m app.module.ai_cli codex "请根据已关联资料输出实现建议。" \
  --file /Users/lexiyue/Documents/example/需求.md \
  --cwd /Users/lexiyue/Documents/example \
  --mode headless \
  --dry-run
```

`--dry-run` 只输出即将执行的命令，便于调用方检查参数。

## 相关文件

- `ai_cli.py`：核心实现。
- `config.json`：当前支持的 CLI 与文件关联参数映射。
- `standard.md`：模块功能参数输入与响应规范。
- `test_ai_cli.py`：命令构造与文件关联规则测试。
