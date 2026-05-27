#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent
CONFIG_PATH = CONFIG_DIR / "config.json"


LOGIN_FIELDS = ["phone", "password"]
FILTER_FIELDS = [
    "category_path",
    "keyword",
    "country",
    "shop_type",
    "product_types",
    "product_status",
    "creator_conversion_rate_filter",
    "total_sales_filter",
    "total_gmv_filter",
    "sales_7d_filter",
    "gmv_7d_filter",
    "creator_count_filter",
    "commission_rate_filter",
    "shipping_method_filter",
    "product_limit",
    "videos_per_product",
]
RESULT_PATH_FIELDS = ["csv_output_dir", "video_output_dir"]
TOP_LEVEL_FIELDS = ["show_browser", "category_config_path"]
GROUPED_SECTION_NAMES = {"login_params", "filter_condition", "result_path"}
COMMENT_KEYS = {"_说明", "_字段说明", "_comment", "_comments", "_note", "_notes"}
UNSUPPORTED_LEGACY_KEYS = {"fastmoss_username", "fastmoss_password", "filter—condition", "filter-condition"}


def _read_raw_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def flatten_config(data: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    flat: dict[str, Any] = {}

    for key in TOP_LEVEL_FIELDS:
        if key in data:
            flat[key] = data[key]

    for section_name in GROUPED_SECTION_NAMES:
        section = data.get(section_name)
        if isinstance(section, dict):
            for key, value in section.items():
                if key in COMMENT_KEYS or key.startswith("_"):
                    continue
                flat[key] = value

    for key, value in data.items():
        if key in GROUPED_SECTION_NAMES or key in COMMENT_KEYS or key.startswith("_"):
            continue
        if key in UNSUPPORTED_LEGACY_KEYS:
            continue
        flat[key] = value

    return flat


def group_config(config: dict[str, Any] | None) -> dict[str, Any]:
    flat = flatten_config(config or {})
    grouped: dict[str, Any] = {}
    consumed: set[str] = set()

    for field in TOP_LEVEL_FIELDS:
        if field in flat:
            grouped[field] = flat[field]
            consumed.add(field)

    login_params = _pick_fields(flat, LOGIN_FIELDS, consumed)
    if login_params:
        grouped["login_params"] = login_params

    filter_condition = _pick_fields(flat, FILTER_FIELDS, consumed)
    if filter_condition:
        grouped["filter_condition"] = filter_condition

    result_path = _pick_fields(flat, RESULT_PATH_FIELDS, consumed)
    if result_path:
        grouped["result_path"] = result_path

    extra = {key: value for key, value in flat.items() if key not in consumed}
    if extra:
        grouped["other"] = extra

    return grouped


def _pick_fields(config: dict[str, Any], fields: list[str], consumed: set[str]) -> dict[str, Any]:
    payload = {}
    for field in fields:
        if field in config:
            payload[field] = config[field]
            consumed.add(field)
    return payload


def load_app_config(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    loaded = flatten_config(_read_raw_config())
    if defaults:
        return {**defaults, **loaded}
    return loaded


def save_app_config(config: dict[str, Any]) -> dict[str, Any]:
    flat = flatten_config(config)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(group_config(flat), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return flat
