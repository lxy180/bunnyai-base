#!/usr/bin/env python3
import hashlib
import re
from pathlib import Path

from .config_store import load_app_config


ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = MODULE_DIR / "projects"
BROWSER_PROFILE_DIR = MODULE_DIR / "browser-profile"
OUTPUTS_DIR = ROOT / "app" / "result" / "hot_item_collection"
RUNTIME_STATE_DIR = MODULE_DIR / "runtime_state"
DIAGNOSTICS_DIR = MODULE_DIR / "diagnostics"
PRODUCT_IDENTITY_FIELDS = ("product_name", "english_name")


def load_config():
    return load_app_config()


def safe_name(value, default="untitled", max_length=120):
    text = str(value or "").strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in text)
    text = re.sub(r"_+", "_", text).strip(" ._")
    return (text[:max_length].strip(" ._") or default)


def config_value(config, key, default=""):
    config = config or load_config()
    return config.get(key) or default


def safe_profile_part(value):
    return re.sub(r"[^0-9A-Za-z_-]+", "_", str(value or "").strip()).strip("_") or "default"


def fastmoss_profile_dir(config=None):
    config = config or load_config()
    phone = config_value(config, "phone")
    return BROWSER_PROFILE_DIR / "fastmoss" / safe_profile_part(phone)


def fastmoss_account_signature(config=None):
    config = config or load_config()
    phone = str(config_value(config, "phone") or "").strip()
    password = str(config_value(config, "password") or "")
    password_sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest() if password else ""
    return {"phone": phone, "password_sha256": password_sha256}


def resolve_config_path_value(value, default_path):
    raw_value = str(value or "").strip()
    path = Path(raw_value).expanduser() if raw_value else Path(default_path)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def csv_output_dir(config=None):
    return resolve_config_path_value(config_value(config, "csv_output_dir"), OUTPUTS_DIR / "csv")


def video_output_dir(config=None):
    return resolve_config_path_value(config_value(config, "video_output_dir"), OUTPUTS_DIR / "videos")


def product_project_slug(config=None):
    return "outputs"


def product_project_root(config=None):
    return OUTPUTS_DIR


def has_product_identity(config=None):
    config = config or load_config()
    profile = config.get("product_profile", {}) or {}
    return any(str(profile.get(field, "") or "").strip() for field in PRODUCT_IDENTITY_FIELDS)


def product_project_ready(config=None):
    config = config or load_config()
    configured = str(config.get("product_project_slug", "") or "").strip()
    if configured == "current_product":
        return False
    if configured:
        return has_product_identity(config) or product_profile_path(config).exists()
    return has_product_identity(config)


def require_product_project(config=None, action="继续操作"):
    if not product_project_ready(config):
        raise SystemExit(f"请先在「产品信息」页面创建并保存产品项目，再{action}")
    return config or load_config()


def ensure_project_dirs(config=None):
    for path in [
        OUTPUTS_DIR,
        csv_output_dir(config),
        video_output_dir(config),
        RUNTIME_STATE_DIR,
        DIAGNOSTICS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def project_relative(path):
    path = Path(path)
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_project_path(value, default_path=None):
    raw_value = str(value or "").strip()
    if not raw_value and default_path:
        return Path(default_path).expanduser().resolve()
    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def product_profile_path(config=None):
    return product_project_root(config) / "product_profile" / "current_product_profile.md"


def runtime_state_path(name, config=None):
    return RUNTIME_STATE_DIR / name


def diagnostics_dir(config=None):
    return DIAGNOSTICS_DIR


def collection_run_dir(run_stem, config=None):
    return csv_output_dir(config)


def collection_csv_path(run_stem, config=None):
    run_dir = collection_run_dir(run_stem, config)
    return run_dir / f"{safe_name(run_stem, 'collection_run')}.csv"


def latest_collection_csv(config=None):
    output_dir = csv_output_dir(config)
    candidates = [path for path in output_dir.rglob("*.csv") if path.is_file()] if output_dir.exists() else []
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0] if candidates else None


def infer_source_id(value, default="unknown_source"):
    text = str(value or "").strip()
    if not text:
        return default

    path = Path(text)
    parts = list(path.parts)
    if "hot_sources" in parts:
        index = parts.index("hot_sources")
        if index + 1 < len(parts):
            return safe_name(parts[index + 1], default, 120)

    for pattern in [
        r"/video/(\d{10,24})",
        r"(?:video_id|作品ID|Video ID)[^\d]{0,12}(\d{10,24})",
        r"(\d{16,24})",
        r"(\d{10,15})",
    ]:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    if path.name:
        return safe_name(path.stem, default, 120)
    return default


def source_dir(source_id, config=None):
    return video_output_dir(config) / safe_name(source_id, "unknown_source", 120)


def source_stage_dir(source_id, stage, config=None):
    path = source_dir(source_id, config) / stage
    path.mkdir(parents=True, exist_ok=True)
    return path


def source_stage_path(source_id, stage, filename, config=None):
    return source_stage_dir(source_id, stage, config) / filename


def product_report_dir(stage, config=None):
    path = product_project_root(config) / "product_level_reports" / stage
    path.mkdir(parents=True, exist_ok=True)
    return path


def raw_data_dir(kind, config=None):
    path = product_project_root(config) / "raw_data" / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def source_id_from_row(row):
    for key in [
        "tiktok_video_url",
        "fastmoss_video_url",
        "video_id",
        "视频ID",
        "作品ID",
        "Video ID",
        "vidoe id",
    ]:
        value = row.get(key) if isinstance(row, dict) else ""
        if value:
            source_id = infer_source_id(value, "")
            if source_id:
                return source_id
    return "unknown_source"


def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for index in range(2, 1000):
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to find unique path for {path}")
