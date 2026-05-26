from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")
SUPPORTED_PROVIDERS = {"codex", "claude", "gemini"}
HEADLESS_MODE = "headless"
INTERACTIVE_MODE = "interactive"
SUPPORTED_EXECUTION_MODES = {HEADLESS_MODE, INTERACTIVE_MODE}
SUPPORTED_OUTPUT_FORMATS = {"text", "json", "stream-json"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
TEXT_CONTENT_CHECK_LIMIT_BYTES = 256 * 1024


@dataclass(frozen=True)
class AiCliRequest:
    provider: str
    prompt: str
    files: Sequence[str | Path] = ()
    workingDirectory: str | Path | None = None
    configPath: str | Path | None = None
    executionMode: str = INTERACTIVE_MODE
    model: str = ""
    outputFormat: str = ""
    extraArgs: Sequence[str] = ()
    env: Mapping[str, str] = field(default_factory=dict)
    timeoutSeconds: int | None = None


@dataclass(frozen=True)
class CommandSpec:
    provider: str
    args: list[str]
    prompt: str
    cwd: Path
    associatedFiles: list[Path]
    associatedDirectories: list[Path]


@dataclass(frozen=True)
class AiCliResult:
    spec: CommandSpec
    returncode: int
    stdout: str
    stderr: str


def build_command(request: AiCliRequest) -> CommandSpec:
    provider = _normalize_provider(request.provider)
    execution_mode = _normalize_execution_mode(request.executionMode)
    output_format = _normalize_output_format(request.outputFormat)
    config = _load_config(request.configPath)
    cwd = _resolve_working_directory(request.workingDirectory, config, provider)
    prompt = _normalize_prompt(request.prompt)
    files = _resolve_associated_files(request.files)
    _validate_prompt_does_not_embed_files(prompt, files)
    directories = _resolve_associated_directories(files)

    if provider == "codex":
        args = _build_codex_args(request, prompt, cwd, directories, files, execution_mode, output_format)
    elif provider == "claude":
        args = _build_claude_args(request, prompt, directories, execution_mode, output_format)
    else:
        args = _build_gemini_args(request, prompt, directories, execution_mode, output_format)

    return CommandSpec(
        provider=provider,
        args=args,
        prompt=prompt,
        cwd=cwd,
        associatedFiles=files,
        associatedDirectories=directories,
    )


def run_ai_cli(request: AiCliRequest, check: bool = False) -> AiCliResult:
    spec = build_command(request)
    env = os.environ.copy()
    env.update(request.env)
    completed = subprocess.run(
        spec.args,
        cwd=spec.cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=request.timeoutSeconds,
        check=False,
    )
    result = AiCliResult(
        spec=spec,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{spec.provider} CLI 调用失败，退出码：{result.returncode}\n{result.stderr}")
    return result


def to_shell_command(spec: CommandSpec) -> str:
    return " ".join(shlex.quote(arg) for arg in spec.args)


def _build_codex_args(
    request: AiCliRequest,
    prompt: str,
    cwd: Path,
    directories: Sequence[Path],
    files: Sequence[Path],
    execution_mode: str,
    output_format: str,
) -> list[str]:
    args = ["codex", "exec"] if execution_mode == HEADLESS_MODE else ["codex"]
    args.extend(["--cd", str(cwd)])
    if request.model:
        args.extend(["--model", request.model])
    for directory in directories:
        args.extend(["--add-dir", str(directory)])
    for file_path in files:
        if file_path.suffix.lower() in IMAGE_SUFFIXES:
            args.extend(["--image", str(file_path)])
    if output_format in {"json", "stream-json"}:
        args.append("--json")
    args.extend(request.extraArgs)
    args.append(prompt)
    return args


def _build_claude_args(
    request: AiCliRequest,
    prompt: str,
    directories: Sequence[Path],
    execution_mode: str,
    output_format: str,
) -> list[str]:
    args = ["claude"]
    if directories:
        args.append("--add-dir")
        args.extend(str(directory) for directory in directories)
    if execution_mode == HEADLESS_MODE:
        args.append("--print")
    if request.model:
        args.extend(["--model", request.model])
    if output_format:
        args.extend(["--output-format", output_format])
    args.extend(request.extraArgs)
    args.append(prompt)
    return args


def _build_gemini_args(
    request: AiCliRequest,
    prompt: str,
    directories: Sequence[Path],
    execution_mode: str,
    output_format: str,
) -> list[str]:
    args = ["gemini"]
    if request.model:
        args.extend(["--model", request.model])
    for directory in directories:
        args.extend(["--include-directories", str(directory)])
    if output_format:
        args.extend(["--output-format", output_format])
    args.extend(request.extraArgs)
    prompt_flag = "--prompt" if execution_mode == HEADLESS_MODE else "--prompt-interactive"
    args.extend([prompt_flag, prompt])
    return args


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError(f"不支持的 AI CLI：{provider}")
    return normalized


def _normalize_execution_mode(execution_mode: str) -> str:
    normalized = execution_mode.strip().lower()
    if normalized not in SUPPORTED_EXECUTION_MODES:
        raise ValueError(f"不支持的执行模式：{execution_mode}")
    return normalized


def _normalize_output_format(output_format: str) -> str:
    normalized = output_format.strip().lower()
    if normalized and normalized not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"不支持的输出格式：{output_format}")
    return normalized


def _normalize_prompt(prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt 必须是非空字符串。")
    return prompt.strip()


def _load_config(config_path: str | Path | None) -> Mapping[str, Any]:
    actual_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not actual_path.exists():
        return {}
    return json.loads(actual_path.read_text(encoding="utf-8"))


def _resolve_working_directory(
    working_directory: str | Path | None,
    config: Mapping[str, Any],
    provider: str,
) -> Path:
    cwd_value = working_directory or _get_configured_working_directory(config, provider) or Path.cwd()
    cwd = Path(cwd_value)
    resolved = cwd.expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"工作目录不存在或不是目录：{resolved}")
    return resolved


def _get_configured_working_directory(config: Mapping[str, Any], provider: str) -> str:
    providers = config.get("providers")
    if isinstance(providers, Mapping):
        provider_config = providers.get(provider)
        if isinstance(provider_config, Mapping):
            provider_cwd = provider_config.get("workingDirectory")
            if isinstance(provider_cwd, str) and provider_cwd.strip():
                return provider_cwd

    configured_cwd = config.get("workingDirectory")
    if isinstance(configured_cwd, str) and configured_cwd.strip():
        return configured_cwd
    return ""


def _resolve_associated_files(files: Sequence[str | Path]) -> list[Path]:
    resolved_files = []
    for file_path in files:
        resolved = Path(file_path).expanduser().resolve()
        if not resolved.exists():
            raise ValueError(f"关联文件不存在：{resolved}")
        if not resolved.is_file():
            raise ValueError(f"关联目标必须是文件：{resolved}")
        resolved_files.append(resolved)
    return _dedupe_paths(resolved_files)


def _resolve_associated_directories(files: Sequence[Path]) -> list[Path]:
    return _dedupe_paths(file_path.parent for file_path in files)


def _validate_prompt_does_not_embed_files(prompt: str, files: Sequence[Path]) -> None:
    for file_path in files:
        if str(file_path) in prompt:
            raise ValueError(f"prompt 中不能直接包含关联文件路径：{file_path}")
        file_content = _read_small_text_file(file_path)
        if file_content and file_content in prompt:
            raise ValueError(f"prompt 中不能直接包含关联文件内容：{file_path}")


def _read_small_text_file(file_path: Path) -> str:
    if file_path.stat().st_size > TEXT_CONTENT_CHECK_LIMIT_BYTES:
        return ""
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return ""


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen = set()
    deduped = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI CLI 统一调用入口。")
    parser.add_argument("provider", choices=sorted(SUPPORTED_PROVIDERS), help="要调用的本地 AI CLI。")
    parser.add_argument("prompt", help="发送给 AI CLI 的提示词，不应包含本地文件路径或文件内容。")
    parser.add_argument("--file", action="append", default=[], help="需要关联的本地文件，可重复传入。")
    parser.add_argument("--cwd", default=None, help="AI CLI 的工作目录，默认使用当前目录。")
    parser.add_argument("--config", default=None, help="AI CLI 模块配置文件路径。")
    parser.add_argument("--mode", choices=sorted(SUPPORTED_EXECUTION_MODES), default=INTERACTIVE_MODE)
    parser.add_argument("--model", default="")
    parser.add_argument("--output-format", choices=sorted(SUPPORTED_OUTPUT_FORMATS), default="")
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="只输出将要执行的命令，不真正调用 CLI。")
    args, extra_args = parser.parse_known_args(argv)

    request = AiCliRequest(
        provider=args.provider,
        prompt=args.prompt,
        files=args.file,
        workingDirectory=args.cwd,
        configPath=args.config,
        executionMode=args.mode,
        model=args.model,
        outputFormat=args.output_format,
        extraArgs=extra_args,
        timeoutSeconds=args.timeout,
    )
    spec = build_command(request)
    if args.dry_run:
        print(to_shell_command(spec))
        return 0

    result = run_ai_cli(request)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
