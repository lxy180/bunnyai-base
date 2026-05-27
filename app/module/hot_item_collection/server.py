#!/usr/bin/env python3
"""爆款采集模块 Web 服务。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from .config_store import group_config, load_app_config, save_app_config
from .project_assets import csv_output_dir, project_relative, video_output_dir


ROOT = Path(__file__).resolve().parents[3]
INDEX_HTML = Path(__file__).with_name("index.html")
CATEGORY_CONFIG_JSON = Path(__file__).with_name("fastmoss_category_config.json")
DEFAULT_PORT = 8081


@dataclass(frozen=True)
class Action:
    """Web 控制台允许执行的固定动作。"""

    id: str
    title: str
    description: str
    module: str
    output_hint: str


ACTIONS: tuple[Action, ...] = (
    Action(
        "login_fastmoss",
        "刷新 FastMoss 登录态",
        "打开浏览器完成登录，并保存 FastMoss 登录状态。",
        "app.module.hot_item_collection.login_fastmoss_assisted",
        "runtime_state/fastmoss-state.json",
    ),
    Action(
        "inspect_top_products",
        "检查前三商品",
        "按当前国家、类目和关键词打开 FastMoss，打印前三个商品链接。",
        "app.module.hot_item_collection.inspect_fastmoss_top_products",
        "控制台日志",
    ),
    Action(
        "scrape_category_tree",
        "抓取 FastMoss 类目树",
        "读取 FastMoss 商品搜索页类目菜单，并写入本地类目树 JSON。",
        "app.module.hot_item_collection.scrape_fastmoss_category_tree",
        "app/result/hot_item_collection/fastmoss_category_tree.json",
    ),
    Action(
        "collect_fastmoss_product_videos",
        "采集商品与关联视频",
        "按当前配置采集 FastMoss 商品、关联视频指标和 TikTok URL。",
        "app.module.hot_item_collection.collect_fastmoss_product_videos",
        "csv_output_dir/*.csv",
    ),
    Action(
        "download_tiktok_videos",
        "下载 TikTok 视频",
        "读取最新采集 CSV，并通过 Kolsprite 下载无水印视频。",
        "app.module.hot_item_collection.download_tiktok_videos_kolsprite",
        "video_output_dir/*/source/*.mp4",
    ),
    Action(
        "run_collection_pipeline",
        "一键采集流水线",
        "先采集 FastMoss 商品与视频 URL，再下载 TikTok 视频。",
        "app.module.hot_item_collection.run_collection_pipeline",
        "csv_output_dir + video_output_dir",
    ),
)

ACTION_BY_ID = {action.id: action for action in ACTIONS}
CommandRunner = Callable[[list[str], Path, Callable[[str], None]], int]


class TaskStore:
    """线程内任务状态存储；只保存当前服务生命周期内的任务。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: dict[str, dict[str, Any]] = {}

    def create(self, action: Action, command: list[str]) -> dict[str, Any]:
        task_id = uuid.uuid4().hex[:12]
        task = {
            "taskId": task_id,
            "actionId": action.id,
            "actionTitle": action.title,
            "command": command,
            "status": "running",
            "logs": [],
            "createdAt": _now(),
            "startedAt": _now(),
            "finishedAt": None,
            "exitCode": None,
            "error": None,
        }
        with self._lock:
            self._tasks[task_id] = task
        return task

    def append_log(self, task_id: str, line: str) -> None:
        with self._lock:
            self._tasks[task_id]["logs"].append(line)

    def finish(self, task_id: str, status: str, exit_code: int | None = None, error: str | None = None) -> None:
        with self._lock:
            task = self._tasks[task_id]
            task["status"] = status
            task["exitCode"] = exit_code
            task["error"] = error
            task["finishedAt"] = _now()

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return _copy_task(task) if task else None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [_copy_task(task) for task in sorted(self._tasks.values(), key=lambda item: item["createdAt"], reverse=True)]


TASKS = TaskStore()


def list_actions() -> list[dict[str, str]]:
    return [
        {
            "id": action.id,
            "title": action.title,
            "description": action.description,
            "module": action.module,
            "outputHint": action.output_hint,
        }
        for action in ACTIONS
    ]


def load_grouped_config() -> dict[str, Any]:
    return group_config(load_app_config())


def load_category_config() -> list[dict[str, Any]]:
    if not CATEGORY_CONFIG_JSON.exists():
        return []
    data = json.loads(CATEGORY_CONFIG_JSON.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def save_config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_config_payload(payload)
    return save_app_config(payload)


def _normalize_config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    normalized = dict(payload)
    hot_collection = normalized.get("hot_collection")
    if isinstance(hot_collection, dict) and "category_path" in hot_collection:
        normalized_hot_collection = dict(hot_collection)
        category_path = normalized_hot_collection.get("category_path")
        if isinstance(category_path, list):
            normalized_hot_collection["category_path"] = [str(item).strip() for item in category_path if str(item).strip()][:3]
        else:
            normalized_hot_collection["category_path"] = []
        normalized["hot_collection"] = normalized_hot_collection
    return normalized


def start_action_task(
    action_id: str,
    config_payload: dict[str, Any] | None,
    *,
    command_runner: CommandRunner | None = None,
    run_async: bool = True,
) -> dict[str, Any]:
    action = ACTION_BY_ID.get(action_id)
    if not action:
        raise ValueError(f"未知操作：{action_id}")
    if config_payload:
        save_config_payload(config_payload)

    command = [_python_executable(), "-m", action.module]
    task = TASKS.create(action, command)
    runner = command_runner or _run_subprocess

    def run() -> None:
        try:
            exit_code = runner(command, ROOT, lambda line: TASKS.append_log(task["taskId"], line))
            status = "completed" if exit_code == 0 else "failed"
            TASKS.finish(task["taskId"], status, exit_code=exit_code)
        except Exception as exc:
            TASKS.append_log(task["taskId"], f"任务异常：{exc}")
            TASKS.finish(task["taskId"], "failed", error=str(exc))

    if run_async:
        threading.Thread(target=run, daemon=True).start()
        return TASKS.get(task["taskId"]) or task

    run()
    return TASKS.get(task["taskId"]) or task


def list_artifacts(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_app_config()
    roots = _artifact_roots(config)
    files: list[dict[str, Any]] = []
    for label, root in roots:
        if root.exists():
            for path in sorted(item for item in root.rglob("*") if item.is_file()):
                files.append(
                    {
                        "path": f"{label}/{path.relative_to(root).as_posix()}",
                        "outputPath": project_relative(path),
                        "size": path.stat().st_size,
                        "modifiedAt": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "kind": _artifact_kind(path),
                        "readable": _is_text_artifact(path),
                    }
                )
    return {"outputRoots": [{"name": label, "path": project_relative(root)} for label, root in roots], "files": files[:500]}


def read_text_artifact(project_root: Path, relative_path: str) -> str:
    root = project_root.resolve()
    target = (root / relative_path).resolve()
    if root != target and root not in target.parents:
        raise ValueError("文件路径超出当前输出目录")
    if not target.is_file():
        raise FileNotFoundError(relative_path)
    if target.stat().st_size > 1024 * 1024:
        raise ValueError("文件超过 1MB，暂不支持在线预览")
    return target.read_text(encoding="utf-8", errors="replace")


def _artifact_roots(config: dict[str, Any]) -> list[tuple[str, Path]]:
    return [
        ("csv", csv_output_dir(config)),
        ("video", video_output_dir(config)),
    ]


def read_artifact_by_display_path(config: dict[str, Any], display_path: str) -> str:
    label, separator, relative_path = display_path.partition("/")
    if not separator:
        raise ValueError("文件路径缺少输出目录前缀")
    for root_label, root in _artifact_roots(config):
        if root_label == label:
            return read_text_artifact(root, relative_path)
    raise ValueError(f"未知输出目录：{label}")


class HotItemCollectionHandler(SimpleHTTPRequestHandler):
    """爆款采集 Web 控制台 HTTP Handler。"""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_index()
        elif parsed.path == "/api/actions":
            _json_response(self, {"actions": list_actions()})
        elif parsed.path == "/api/config":
            _json_response(self, load_grouped_config())
        elif parsed.path == "/api/category-config":
            _json_response(self, {"categories": load_category_config()})
        elif parsed.path == "/api/tasks":
            _json_response(self, {"tasks": TASKS.list()})
        elif parsed.path.startswith("/api/tasks/"):
            self._serve_task(parsed.path.rsplit("/", 1)[-1])
        elif parsed.path == "/api/artifacts":
            _json_response(self, list_artifacts())
        elif parsed.path == "/api/artifacts/read":
            self._serve_artifact_text(parsed.query)
        elif parsed.path == "/api/artifacts/video":
            self._serve_artifact_video(parsed.query)
        else:
            _json_response(self, {"error": "未找到"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            payload = _read_json_body(self)
            _json_response(self, save_config_payload(payload))
            return
        match = parsed.path.removeprefix("/api/actions/").removesuffix("/run")
        if parsed.path.startswith("/api/actions/") and parsed.path.endswith("/run"):
            payload = _read_json_body(self)
            try:
                task = start_action_task(match, payload.get("config") if isinstance(payload, dict) else None)
                _json_response(self, task, 202)
            except ValueError as exc:
                _json_response(self, {"error": str(exc)}, 404)
            return
        _json_response(self, {"error": "未找到"}, 404)

    def _serve_index(self) -> None:
        content = INDEX_HTML.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_task(self, task_id: str) -> None:
        task = TASKS.get(task_id)
        if not task:
            _json_response(self, {"error": f"任务 {task_id} 不存在"}, 404)
            return
        _json_response(self, task)

    def _serve_artifact_text(self, query: str) -> None:
        params = parse_qs(query)
        relative_path = params.get("path", [""])[0]
        try:
            text = read_artifact_by_display_path(load_app_config(), relative_path)
            _json_response(self, {"path": relative_path, "content": text})
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 400)

    def _serve_artifact_video(self, query: str) -> None:
        params = parse_qs(query)
        display_path = params.get("path", [""])[0]
        try:
            label, relative_path = display_path.split("/", 1)
            config = load_app_config()
            for root_label, root in _artifact_roots(config):
                if root_label == label:
                    target = (root / relative_path).resolve()
                    root_resolved = root.resolve()
                    if root_resolved != target and root_resolved not in target.parents:
                        raise ValueError("路径越界")
                    if not target.is_file():
                        raise FileNotFoundError(relative_path)
                    content = target.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", _video_mime(target))
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    self.wfile.write(content)
                    return
            raise ValueError(f"未知输出目录：{label}")
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 400)


def make_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), HotItemCollectionHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="启动爆款采集 Web 控制台")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = make_server(args.port)
    print(f"[hot_item_collection] 服务已启动：http://localhost:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[hot_item_collection] 服务已停止", flush=True)


def _run_subprocess(command: list[str], cwd: Path, on_output: Callable[[str], None]) -> int:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        on_output(line.rstrip("\n"))
    return process.wait()


def _python_executable() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _read_json_body(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _json_response(handler: SimpleHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _artifact_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".mp4", ".mov", ".webm"}:
        return "video"
    if suffix in {".json", ".txt", ".md", ".log"}:
        return "text"
    return "file"


def _is_text_artifact(path: Path) -> bool:
    return _artifact_kind(path) in {"csv", "text"} and path.stat().st_size <= 1024 * 1024


def _video_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".mp4":
        return "video/mp4"
    if suffix == ".webm":
        return "video/webm"
    if suffix == ".mov":
        return "video/quicktime"
    return "application/octet-stream"


def _copy_task(task: dict[str, Any]) -> dict[str, Any]:
    copied = dict(task)
    copied["logs"] = list(task.get("logs", []))
    return copied


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    main()
