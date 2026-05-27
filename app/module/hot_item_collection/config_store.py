#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent
CONFIG_PATH = CONFIG_DIR / "config.json"
LEGACY_CONFIG_PATH = CONFIG_DIR / "fastmoss_config.json"
CONFIG_SCHEMA_VERSION = 2


CONFIG_SECTIONS: list[tuple[str, str, list[str]]] = [
    (
        "hot_collection",
        "爆款采集配置。包含采集账号、搜索条件、筛选条件、采集数量和浏览器显示方式。",
        [
            "phone",
            "password",
            "keyword",
            "country",
            "category_path",
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
            "show_browser",
            "csv_output_dir",
            "video_output_dir",
        ],
    ),
]


SECTION_NAMES = {section_name for section_name, _comment, _fields in CONFIG_SECTIONS}
GROUPED_SECTION_NAMES = SECTION_NAMES | {"other"}
KNOWN_FIELDS = {field for _section_name, _comment, fields in CONFIG_SECTIONS for field in fields}
COMMENT_KEYS = {"_说明", "_字段说明", "_comment", "_comments", "_note", "_notes"}


def _read_raw_config() -> dict[str, Any]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else LEGACY_CONFIG_PATH
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def flatten_config(data: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    flat: dict[str, Any] = {}

    for section_name, section in data.items():
        if section_name not in GROUPED_SECTION_NAMES:
            continue
        if not isinstance(section, dict):
            continue
        for key, value in section.items():
            if key in COMMENT_KEYS or key.startswith("_"):
                continue
            flat[key] = value

    for key, value in data.items():
        if key in GROUPED_SECTION_NAMES or key in COMMENT_KEYS or key.startswith("_"):
            continue
        if key in {"config_schema_version", "schema_version", "filter—condition", "filter-condition"}:
            continue
        if key == "fastmoss_username":
            flat["phone"] = value
            continue
        if key == "fastmoss_password":
            flat["password"] = value
            continue
        flat[key] = value

    for legacy_filter_key in ("filter—condition", "filter-condition"):
        legacy_filter = data.get(legacy_filter_key)
        if isinstance(legacy_filter, dict):
            for key, value in legacy_filter.items():
                if key not in COMMENT_KEYS and not key.startswith("_"):
                    flat[key] = value

    return flat


def group_config(config: dict[str, Any] | None) -> dict[str, Any]:
    flat = flatten_config(config or {})
    grouped: dict[str, Any] = {
        "config_schema_version": CONFIG_SCHEMA_VERSION,
    }
    consumed: set[str] = set()

    for section_name, comment, fields in CONFIG_SECTIONS:
        section_payload: dict[str, Any] = {}
        for field in fields:
            if field in flat:
                section_payload[field] = flat[field]
                consumed.add(field)
        if section_payload:
            grouped[section_name] = section_payload

    extra = {key: value for key, value in flat.items() if key not in consumed}
    if extra:
        grouped["other"] = extra

    return grouped


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
