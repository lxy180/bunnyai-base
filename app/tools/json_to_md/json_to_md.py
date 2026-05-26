from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


Block = dict[str, Any]
Document = dict[str, Any]
CALL_LOG_PATH = Path(__file__).with_name("call-log.log")
MAX_CALL_LOG_RECORDS = 50


def render_markdown(document: Document, with_markers: bool = False) -> str:
    blocks = document.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("JSON 根对象必须包含 blocks 数组。")

    rendered_blocks = [_render_block(block, with_markers) for block in blocks]
    return "\n\n".join(rendered_blocks).rstrip() + "\n"


def sync_json_to_markdown(
    input_path: str | Path,
    output_path: str | Path,
    with_markers: bool = False,
) -> None:
    input_file = Path(input_path)
    output_file = Path(output_path)

    document = json.loads(input_file.read_text(encoding="utf-8"))
    markdown = render_markdown(document, with_markers=with_markers)
    output_file.write_text(markdown, encoding="utf-8")


def parse_markdown(markdown: str) -> Document:
    blocks = []
    lines = markdown.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        if index == 0 and line.strip() == "---":
            block, index = _parse_frontmatter(lines, index)
            blocks.append(block)
            continue

        marker_match = re.fullmatch(r"\s*<!-- block:([^>]+) -->\s*", line)
        if marker_match:
            block_id = marker_match.group(1)
            inner_lines = []
            index += 1
            while index < len(lines) and not re.fullmatch(
                rf"\s*<!-- /block:{re.escape(block_id)} -->\s*",
                lines[index],
            ):
                inner_lines.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError(f"未找到 block 结束标记：{block_id}")
            inner_document = parse_markdown("\n".join(inner_lines))
            if len(inner_document["blocks"]) == 1:
                block = inner_document["blocks"][0]
                block["id"] = block_id
                blocks.append(block)
            else:
                blocks.append(
                    {
                        "id": block_id,
                        "type": "group",
                        "blocks": inner_document["blocks"],
                    }
                )
            index += 1
            continue

        heading_match = re.fullmatch(r"(#{1,6})\s+(.+)", line)
        if heading_match:
            blocks.append(
                {
                    "type": "heading",
                    "level": len(heading_match.group(1)),
                    "text": heading_match.group(2),
                }
            )
            index += 1
            continue

        code_match = re.fullmatch(r"```(\w*)", line)
        if code_match:
            code_lines = []
            index += 1
            while index < len(lines) and lines[index] != "```":
                code_lines.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError("代码块缺少结束围栏。")
            block = {
                "type": "code",
                "language": code_match.group(1),
                "content": "\n".join(code_lines),
            }
            if not block["language"]:
                block.pop("language")
            blocks.append(block)
            index += 1
            continue

        footnote_match = _match_footnote(line)
        if footnote_match:
            block, index = _parse_footnote(lines, index)
            blocks.append(block)
            continue

        if _is_html_start(line):
            block, index = _parse_html(lines, index)
            blocks.append(block)
            continue

        link_reference_match = _match_link_reference(line)
        if link_reference_match:
            block = {
                "type": "link_reference",
                "label": link_reference_match.group("label"),
                "url": link_reference_match.group("url"),
            }
            title = link_reference_match.group("title")
            if title:
                block["title"] = title
            blocks.append(block)
            index += 1
            continue

        if _is_table_start(lines, index):
            block, index = _parse_table(lines, index)
            blocks.append(block)
            continue

        if _is_task_list_item(line):
            block, index = _parse_task_list(lines, index)
            blocks.append(block)
            continue

        if _is_unordered_list_item(line) or _is_ordered_list_item(line):
            block, index = _parse_list(lines, index)
            blocks.append(block)
            continue

        if line.startswith("> "):
            quote_lines = []
            while index < len(lines) and lines[index].startswith("> "):
                quote_lines.append(lines[index][2:])
                index += 1
            blocks.append({"type": "quote", "text": "\n".join(quote_lines)})
            continue

        paragraph_lines = []
        while index < len(lines) and _is_paragraph_line(lines[index]):
            paragraph_lines.append(lines[index])
            index += 1
        blocks.append({"type": "paragraph", "text": "\n".join(paragraph_lines)})

    return {"blocks": blocks}


def sync_markdown_to_json(input_path: str | Path, output_path: str | Path) -> None:
    input_file = Path(input_path)
    output_file = Path(output_path)

    document = parse_markdown(input_file.read_text(encoding="utf-8"))
    output_file.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def convert_file(
    input_path: str | Path,
    output_path: str | Path | None = None,
    direction: str | None = None,
    with_markers: bool = False,
) -> Path:
    input_file = Path(input_path)
    actual_direction = direction or _infer_direction(input_file)
    actual_output_path = _resolve_output_path(input_file, output_path, actual_direction)
    actual_output_path.parent.mkdir(parents=True, exist_ok=True)

    if actual_direction == "json-to-md":
        sync_json_to_markdown(input_file, actual_output_path, with_markers=with_markers)
        return actual_output_path
    if actual_direction == "md-to-json":
        sync_markdown_to_json(input_file, actual_output_path)
        return actual_output_path

    raise ValueError(f"不支持的转换方向：{actual_direction}")


def run_conversion(
    input_path: str | Path,
    output_path: str | Path | None = None,
    direction: str | None = None,
    with_markers: bool = False,
    log_path: str | Path = CALL_LOG_PATH,
) -> Path:
    try:
        actual_output_path = convert_file(
            input_path,
            output_path,
            direction=direction,
            with_markers=with_markers,
        )
    except Exception as error:
        _append_call_log(
            {
                "timestamp": _current_timestamp(),
                "status": "failure",
                "input": str(input_path),
                "output_argument": _stringify_optional_path(output_path),
                "output": None,
                "direction": direction,
                "with_markers": with_markers,
                "error": str(error),
            },
            log_path,
        )
        raise

    _append_call_log(
        {
            "timestamp": _current_timestamp(),
            "status": "success",
            "input": str(input_path),
            "output_argument": _stringify_optional_path(output_path),
            "output": str(actual_output_path),
            "direction": direction,
            "with_markers": with_markers,
            "error": None,
        },
        log_path,
    )
    return actual_output_path


def _render_block(block: Block, with_markers: bool) -> str:
    if not isinstance(block, dict):
        raise ValueError("blocks 中的每一项都必须是对象。")

    block_type = block.get("type")
    if block_type == "heading":
        markdown = _render_heading(block)
    elif block_type == "paragraph":
        markdown = _require_text(block)
    elif block_type == "code":
        markdown = _render_code(block)
    elif block_type == "list":
        markdown = _render_list(block)
    elif block_type == "quote":
        markdown = _render_quote(block)
    elif block_type == "table":
        markdown = _render_table(block)
    elif block_type == "link_reference":
        markdown = _render_link_reference(block)
    elif block_type == "frontmatter":
        markdown = _render_frontmatter(block)
    elif block_type == "group":
        markdown = _render_group(block, with_markers)
    elif block_type == "task_list":
        markdown = _render_task_list(block)
    elif block_type == "footnote":
        markdown = _render_footnote(block)
    elif block_type == "html":
        markdown = _render_html(block)
    else:
        raise ValueError(f"不支持的块类型：{block_type}")

    if block_type == "group":
        return markdown

    if not with_markers:
        return markdown

    block_id = block.get("id")
    if not block_id:
        raise ValueError("开启块标记时，每个 block 都必须提供 id。")

    return f"<!-- block:{block_id} -->\n{markdown}\n<!-- /block:{block_id} -->"


def _render_heading(block: Block) -> str:
    level = int(block.get("level", 1))
    if level < 1 or level > 6:
        raise ValueError("heading.level 必须在 1 到 6 之间。")

    return f"{'#' * level} {_require_text(block)}"


def _render_code(block: Block) -> str:
    language = block.get("language", "")
    content = str(block.get("content", ""))
    return f"```{language}\n{content.rstrip()}\n```"


def _render_list(block: Block, indent: int = 0) -> str:
    items = block.get("items")
    if not isinstance(items, list):
        raise ValueError("list.items 必须是数组。")

    ordered = bool(block.get("ordered", False))
    lines = []
    for index, item in enumerate(items, start=1):
        prefix = f"{index}. " if ordered else "- "
        line_prefix = " " * indent + prefix
        if isinstance(item, dict):
            text = item.get("text")
            if text is None:
                raise ValueError("嵌套列表项必须提供 text。")
            lines.append(f"{line_prefix}{text}")
            children = item.get("children")
            if children is not None:
                lines.append(_render_list(children, indent=indent + 2))
        else:
            lines.append(f"{line_prefix}{item}")

    return "\n".join(lines)


def _render_quote(block: Block) -> str:
    text = _require_text(block)
    return "\n".join(f"> {line}" for line in text.splitlines())


def _render_table(block: Block) -> str:
    headers = block.get("headers")
    rows = block.get("rows")
    if not isinstance(headers, list) or not headers:
        raise ValueError("table.headers 必须是非空数组。")
    if not isinstance(rows, list):
        raise ValueError("table.rows 必须是数组。")

    lines = [
        _render_table_row(headers),
        _render_table_row(["---" for _ in headers]),
    ]
    for row in rows:
        if not isinstance(row, list):
            raise ValueError("table.rows 中的每一行都必须是数组。")
        lines.append(_render_table_row(row))

    return "\n".join(lines)


def _render_table_row(cells: list[Any]) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def _render_link_reference(block: Block) -> str:
    label = block.get("label")
    url = block.get("url")
    if not label or not url:
        raise ValueError("link_reference 块必须提供 label 和 url。")

    markdown = f"[{label}]: {url}"
    title = block.get("title")
    if title:
        escaped_title = str(title).replace('"', '\\"')
        markdown += f' "{escaped_title}"'
    return markdown


def _render_frontmatter(block: Block) -> str:
    content = str(block.get("content", "")).strip()
    return f"---\n{content}\n---"


def _render_group(block: Block, with_markers: bool) -> str:
    block_id = block.get("id")
    if not block_id:
        raise ValueError("group 块必须提供 id。")
    inner_blocks = block.get("blocks")
    if not isinstance(inner_blocks, list):
        raise ValueError("group.blocks 必须是数组。")
    inner_markdown = render_markdown({"blocks": inner_blocks}).rstrip()
    return f"<!-- block:{block_id} -->\n{inner_markdown}\n<!-- /block:{block_id} -->"


def _render_task_list(block: Block) -> str:
    items = block.get("items")
    if not isinstance(items, list):
        raise ValueError("task_list.items 必须是数组。")
    lines = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("task_list.items 中的每一项都必须是对象。")
        text = item.get("text")
        if text is None:
            raise ValueError("任务列表项必须提供 text。")
        marker = "x" if bool(item.get("checked", False)) else " "
        lines.append(f"- [{marker}] {text}")
    return "\n".join(lines)


def _render_footnote(block: Block) -> str:
    label = block.get("label")
    text = block.get("text")
    if not label or text is None:
        raise ValueError("footnote 块必须提供 label 和 text。")
    lines = str(text).splitlines()
    first_line = lines[0] if lines else ""
    rendered = f"[^{label}]: {first_line}"
    if len(lines) > 1:
        rendered += "\n" + "\n".join(f"    {line}" for line in lines[1:])
    return rendered


def _render_html(block: Block) -> str:
    content = block.get("content")
    if content is None:
        raise ValueError("html 块必须提供 content。")
    return str(content).rstrip()


def _require_text(block: Block) -> str:
    text = block.get("text")
    if text is None:
        raise ValueError(f"{block.get('type')} 块必须提供 text。")
    return str(text)


def _is_paragraph_line(line: str) -> bool:
    return bool(line.strip()) and not (
        re.fullmatch(r"\s*<!-- block:([^>]+) -->\s*", line)
        or re.fullmatch(r"(#{1,6})\s+(.+)", line)
        or re.fullmatch(r"```\w*", line)
        or _match_footnote(line)
        or _is_html_start(line)
        or _match_link_reference(line)
        or _is_task_list_item(line)
        or _is_unordered_list_item(line)
        or _is_ordered_list_item(line)
        or line.startswith("> ")
    )


def _is_unordered_list_item(line: str) -> bool:
    return bool(re.fullmatch(r"\s*[-*]\s+.+", line))


def _is_ordered_list_item(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\d+\.\s+.+", line))


def _is_same_list_type(line: str, ordered: bool) -> bool:
    if ordered:
        return _is_ordered_list_item(line)
    return _is_unordered_list_item(line)


def _parse_list_item(line: str, ordered: bool) -> str:
    pattern = r"\s*\d+\.\s+(.+)" if ordered else r"\s*[-*]\s+(.+)"
    match = re.fullmatch(pattern, line)
    if not match:
        raise ValueError(f"无效的列表项：{line}")
    return match.group(1)


def _parse_list(lines: list[str], start_index: int) -> tuple[Block, int]:
    entries = []
    index = start_index
    while index < len(lines):
        match = _match_list_item(lines[index])
        if not match:
            break
        entries.append(
            {
                "indent": len(match.group("indent").replace("\t", "  ")),
                "ordered": match.group("marker").endswith("."),
                "text": match.group("text"),
            }
        )
        index += 1

    block, entry_index = _build_list(entries, 0, entries[0]["indent"])
    if entry_index != len(entries):
        raise ValueError("列表缩进结构无法解析。")
    return block, index


def _build_list(entries: list[dict[str, Any]], index: int, indent: int) -> tuple[Block, int]:
    ordered = bool(entries[index]["ordered"])
    items = []

    while index < len(entries):
        entry = entries[index]
        if entry["indent"] < indent:
            break
        if entry["indent"] > indent:
            raise ValueError("列表子项必须挂在上一个列表项下面。")

        text = entry["text"]
        index += 1
        item: str | dict[str, Any] = text
        if index < len(entries) and entries[index]["indent"] > indent:
            children, index = _build_list(entries, index, entries[index]["indent"])
            item = {"text": text, "children": children}
        items.append(item)

    block: Block = {"type": "list", "items": items}
    if ordered:
        block["ordered"] = True
    return block, index


def _match_list_item(line: str) -> re.Match[str] | None:
    return re.fullmatch(r"(?P<indent>\s*)(?P<marker>[-*]|\d+\.)\s+(?P<text>.+)", line)


def _match_link_reference(line: str) -> re.Match[str] | None:
    return re.fullmatch(
        r'\s*\[(?P<label>[^\]]+)\]:\s+(?P<url>\S+)(?:\s+"(?P<title>[^"]+)")?\s*',
        line,
    )


def _parse_frontmatter(lines: list[str], start_index: int) -> tuple[Block, int]:
    content_lines = []
    index = start_index + 1
    while index < len(lines) and lines[index].strip() != "---":
        content_lines.append(lines[index])
        index += 1
    if index == len(lines):
        raise ValueError("Frontmatter 缺少结束分隔符。")
    return {"type": "frontmatter", "content": "\n".join(content_lines)}, index + 1


def _is_task_list_item(line: str) -> bool:
    return bool(re.fullmatch(r"\s*[-*]\s+\[[ xX]\]\s+.+", line))


def _parse_task_list(lines: list[str], start_index: int) -> tuple[Block, int]:
    items = []
    index = start_index
    while index < len(lines):
        match = re.fullmatch(r"\s*[-*]\s+\[(?P<checked>[ xX])\]\s+(?P<text>.+)", lines[index])
        if not match:
            break
        items.append(
            {
                "text": match.group("text"),
                "checked": match.group("checked").lower() == "x",
            }
        )
        index += 1
    return {"type": "task_list", "items": items}, index


def _match_footnote(line: str) -> re.Match[str] | None:
    return re.fullmatch(r"\[\^(?P<label>[^\]]+)\]:\s*(?P<text>.*)", line)


def _parse_footnote(lines: list[str], start_index: int) -> tuple[Block, int]:
    match = _match_footnote(lines[start_index])
    if not match:
        raise ValueError(f"无效的脚注定义：{lines[start_index]}")
    text_lines = [match.group("text")]
    index = start_index + 1
    while index < len(lines) and re.fullmatch(r"\s{4,}.+", lines[index]):
        text_lines.append(lines[index].strip())
        index += 1
    return {
        "type": "footnote",
        "label": match.group("label"),
        "text": "\n".join(text_lines),
    }, index


def _is_html_start(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("<")
        and not stripped.startswith("<!--")
        and bool(re.match(r"</?[A-Za-z][^>]*>", stripped))
    )


def _parse_html(lines: list[str], start_index: int) -> tuple[Block, int]:
    html_lines = []
    index = start_index
    while index < len(lines) and lines[index].strip():
        html_lines.append(lines[index])
        index += 1
    return {"type": "html", "content": "\n".join(html_lines)}, index


def _is_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and _looks_like_table_row(lines[index])
        and _is_table_separator(lines[index + 1])
    )


def _parse_table(lines: list[str], start_index: int) -> tuple[Block, int]:
    headers = _split_table_row(lines[start_index])
    rows = []
    index = start_index + 2

    while index < len(lines) and _looks_like_table_row(lines[index]):
        rows.append(_split_table_row(lines[index]))
        index += 1

    return {"type": "table", "headers": headers, "rows": rows}, index


def _looks_like_table_row(line: str) -> bool:
    return "|" in line and bool(line.strip())


def _is_table_separator(line: str) -> bool:
    cells = _split_table_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _append_call_log(entry: dict[str, Any], log_path: str | Path) -> None:
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if log_file.exists():
        logs = [
            json.loads(line)
            for line in log_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        logs = []

    logs.append(entry)
    logs = logs[-MAX_CALL_LOG_RECORDS:]
    log_file.write_text(
        "\n".join(json.dumps(log, ensure_ascii=False) for log in logs) + "\n",
        encoding="utf-8",
    )


def _current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _stringify_optional_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def _infer_direction(input_file: Path) -> str:
    suffix = input_file.suffix.lower()
    if suffix == ".json":
        return "json-to-md"
    if suffix in {".md", ".markdown"}:
        return "md-to-json"
    raise ValueError("无法根据输入文件后缀判断转换方向，请使用 --direction 指定。")


def _resolve_output_path(
    input_file: Path,
    output_path: str | Path | None,
    direction: str,
) -> Path:
    target_suffix = ".md" if direction == "json-to-md" else ".json"
    if output_path is None:
        return input_file.with_suffix(target_suffix)

    output_file = Path(output_path)
    if output_file.exists() and output_file.is_dir():
        return output_file / f"{input_file.stem}{target_suffix}"
    if output_file.suffix:
        return output_file.parent / f"{input_file.stem}{target_suffix}"

    return output_file / f"{input_file.stem}{target_suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="在块级 JSON 与 Markdown 之间相互转换。")
    parser.add_argument("input", help="输入文件路径，支持 .json、.md、.markdown。")
    parser.add_argument("output", nargs="?", help="输出文件或目录路径。")
    parser.add_argument("-o", "--output", dest="output_option", help="自定义输出文件或目录路径。")
    parser.add_argument(
        "--direction",
        choices=["json-to-md", "md-to-json"],
        help="转换方向；不指定时根据输入文件后缀自动判断。",
    )
    parser.add_argument(
        "--markers",
        action="store_true",
        help="JSON 转 Markdown 时输出 block id 标记，便于后续按块定位。",
    )
    args = parser.parse_args()
    if args.output and args.output_option:
        parser.error("位置参数 output 与 --output 只能选择一种。")

    run_conversion(
        args.input,
        args.output_option or args.output,
        direction=args.direction,
        with_markers=args.markers,
    )


if __name__ == "__main__":
    main()
