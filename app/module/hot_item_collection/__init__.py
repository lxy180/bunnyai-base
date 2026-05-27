"""爆款采集模块。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_items(module_dir: Path | str) -> list[dict[str, Any]]:
    """读取爆款采集目录下的非空 Markdown 条目。"""
    collection_dir = Path(module_dir)
    items: list[dict[str, Any]] = []

    for markdown_file in sorted(collection_dir.glob("*.md")):
        if markdown_file.name.startswith("_"):
            continue

        content = markdown_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        items.append(
            {
                "title": markdown_file.stem,
                "sourceFile": markdown_file.name,
                "content": content,
            }
        )

    return items
