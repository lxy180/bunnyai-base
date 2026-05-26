import json
import re
import tempfile
import unittest
from pathlib import Path

from app.tools.json_to_md import (
    convert_file,
    parse_markdown,
    render_markdown,
    run_conversion,
    sync_json_to_markdown,
    sync_markdown_to_json,
)


def read_log_lines(log_path):
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class JsonToMarkdownTest(unittest.TestCase):
    def test_render_heading_paragraph_and_code_block(self):
        document = {
            "blocks": [
                {"id": "title", "type": "heading", "level": 1, "text": "产品说明"},
                {"id": "intro", "type": "paragraph", "text": "这是产品的基础介绍。"},
                {"id": "install", "type": "code", "language": "bash", "content": "npm install"},
            ]
        }

        markdown = render_markdown(document)

        self.assertEqual(
            markdown,
                "# 产品说明\n\n这是产品的基础介绍。\n\n```bash\nnpm install\n```\n",
        )

    def test_render_table_nested_mixed_list_and_link_reference(self):
        document = {
            "blocks": [
                {
                    "type": "table",
                    "headers": ["字段", "说明"],
                    "rows": [["type", "块类型"], ["text", "文本内容"]],
                },
                {
                    "type": "list",
                    "items": [
                        {
                            "text": "准备环境",
                            "children": {
                                "type": "list",
                                "ordered": True,
                                "items": ["安装依赖", "运行测试"],
                            },
                        },
                        "完成转换",
                    ],
                },
                {
                    "type": "link_reference",
                    "label": "转换工具",
                    "url": "app/tools/json_to_md/README.md",
                    "title": "工具说明",
                },
            ]
        }

        markdown = render_markdown(document)

        self.assertEqual(
            markdown,
            "| 字段 | 说明 |\n"
            "| --- | --- |\n"
            "| type | 块类型 |\n"
            "| text | 文本内容 |\n\n"
            "- 准备环境\n"
            "  1. 安装依赖\n"
            "  2. 运行测试\n"
            "- 完成转换\n\n"
            '[转换工具]: app/tools/json_to_md/README.md "工具说明"\n',
        )

    def test_render_frontmatter_task_list_footnote_html_and_group_marker(self):
        document = {
            "blocks": [
                {
                    "type": "frontmatter",
                    "content": "title: 产品说明\ntags:\n  - 工具",
                },
                {
                    "id": "overview",
                    "type": "group",
                    "blocks": [
                        {"type": "heading", "level": 2, "text": "概述"},
                        {"type": "paragraph", "text": "这是概述内容。"},
                    ],
                },
                {
                    "type": "task_list",
                    "items": [
                        {"text": "完成转换", "checked": True},
                        {"text": "补充文档", "checked": False},
                    ],
                },
                {"type": "footnote", "label": "note1", "text": "这是脚注内容。"},
                {"type": "html", "content": '<div class="note">\n  <p>提示</p>\n</div>'},
            ]
        }

        markdown = render_markdown(document)

        self.assertEqual(
            markdown,
            "---\n"
            "title: 产品说明\n"
            "tags:\n"
            "  - 工具\n"
            "---\n\n"
            "<!-- block:overview -->\n"
            "## 概述\n\n"
            "这是概述内容。\n"
            "<!-- /block:overview -->\n\n"
            "- [x] 完成转换\n"
            "- [ ] 补充文档\n\n"
            "[^note1]: 这是脚注内容。\n\n"
            '<div class="note">\n'
            "  <p>提示</p>\n"
            "</div>\n",
        )

    def test_render_with_block_markers(self):
        document = {
            "blocks": [
                {"id": "intro", "type": "paragraph", "text": "这是产品的基础介绍。"},
            ]
        }

        markdown = render_markdown(document, with_markers=True)

        self.assertEqual(
            markdown,
            "<!-- block:intro -->\n这是产品的基础介绍。\n<!-- /block:intro -->\n",
        )

    def test_sync_json_file_to_markdown_file(self):
        document = {
            "blocks": [
                {"id": "title", "type": "heading", "level": 2, "text": "安装"},
                {"id": "steps", "type": "list", "items": ["安装依赖", "运行脚本"]},
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "content.json"
            output_path = Path(temp_dir) / "content.md"
            input_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            sync_json_to_markdown(input_path, output_path)

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "## 安装\n\n- 安装依赖\n- 运行脚本\n",
            )

    def test_parse_markdown_to_blocks(self):
        markdown = (
            "# 产品说明\n\n"
            "这是产品的基础介绍。\n\n"
            "```bash\nnpm install\n```\n\n"
            "- 安装依赖\n- 运行脚本\n\n"
            "> 这是一段引用。\n"
        )

        document = parse_markdown(markdown)

        self.assertEqual(
            document,
            {
                "blocks": [
                    {"type": "heading", "level": 1, "text": "产品说明"},
                    {"type": "paragraph", "text": "这是产品的基础介绍。"},
                    {"type": "code", "language": "bash", "content": "npm install"},
                    {"type": "list", "items": ["安装依赖", "运行脚本"]},
                    {"type": "quote", "text": "这是一段引用。"},
                ]
            },
        )

    def test_parse_table_nested_mixed_list_and_link_reference(self):
        markdown = (
            "| 字段 | 说明 |\n"
            "| --- | --- |\n"
            "| type | 块类型 |\n"
            "| text | 文本内容 |\n\n"
            "- 准备环境\n"
            "  1. 安装依赖\n"
            "  2. 运行测试\n"
            "- 完成转换\n\n"
            '[转换工具]: app/tools/json_to_md/README.md "工具说明"\n'
        )

        document = parse_markdown(markdown)

        self.assertEqual(
            document,
            {
                "blocks": [
                    {
                        "type": "table",
                        "headers": ["字段", "说明"],
                        "rows": [["type", "块类型"], ["text", "文本内容"]],
                    },
                    {
                        "type": "list",
                        "items": [
                            {
                                "text": "准备环境",
                                "children": {
                                    "type": "list",
                                    "ordered": True,
                                    "items": ["安装依赖", "运行测试"],
                                },
                            },
                            "完成转换",
                        ],
                    },
                    {
                        "type": "link_reference",
                        "label": "转换工具",
                        "url": "app/tools/json_to_md/README.md",
                        "title": "工具说明",
                    },
                ]
            },
        )

    def test_parse_frontmatter_task_list_footnote_html_and_group_marker(self):
        markdown = (
            "---\n"
            "title: 产品说明\n"
            "tags:\n"
            "  - 工具\n"
            "---\n\n"
            "<!-- block:overview -->\n"
            "## 概述\n\n"
            "这是概述内容。\n"
            "<!-- /block:overview -->\n\n"
            "- [x] 完成转换\n"
            "- [ ] 补充文档\n\n"
            "[^note1]: 这是脚注内容。\n\n"
            '<div class="note">\n'
            "  <p>提示</p>\n"
            "</div>\n"
        )

        document = parse_markdown(markdown)

        self.assertEqual(
            document,
            {
                "blocks": [
                    {
                        "type": "frontmatter",
                        "content": "title: 产品说明\ntags:\n  - 工具",
                    },
                    {
                        "id": "overview",
                        "type": "group",
                        "blocks": [
                            {"type": "heading", "level": 2, "text": "概述"},
                            {"type": "paragraph", "text": "这是概述内容。"},
                        ],
                    },
                    {
                        "type": "task_list",
                        "items": [
                            {"text": "完成转换", "checked": True},
                            {"text": "补充文档", "checked": False},
                        ],
                    },
                    {"type": "footnote", "label": "note1", "text": "这是脚注内容。"},
                    {
                        "type": "html",
                        "content": '<div class="note">\n  <p>提示</p>\n</div>',
                    },
                ]
            },
        )

    def test_parse_markdown_preserves_block_markers(self):
        markdown = (
            "<!-- block:intro -->\n"
            "这是产品的基础介绍。\n"
            "<!-- /block:intro -->\n"
        )

        document = parse_markdown(markdown)

        self.assertEqual(
            document,
            {
                "blocks": [
                    {"id": "intro", "type": "paragraph", "text": "这是产品的基础介绍。"},
                ]
            },
        )

    def test_sync_markdown_file_to_json_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "content.md"
            output_path = Path(temp_dir) / "content.json"
            input_path.write_text("## 安装\n\n1. 安装依赖\n2. 运行脚本\n", encoding="utf-8")

            sync_markdown_to_json(input_path, output_path)

            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {
                    "blocks": [
                        {"type": "heading", "level": 2, "text": "安装"},
                        {"type": "list", "ordered": True, "items": ["安装依赖", "运行脚本"]},
                    ]
                },
            )

    def test_convert_file_infers_direction_from_input_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            json_output = Path(temp_dir) / "content.json"
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            convert_file(md_input, json_output)

            self.assertEqual(
                json.loads(json_output.read_text(encoding="utf-8")),
                {"blocks": [{"type": "heading", "level": 1, "text": "产品说明"}]},
            )

    def test_convert_file_writes_to_custom_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            output_dir = Path(temp_dir) / "dist"
            output_dir.mkdir()
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            output_path = convert_file(md_input, output_dir)

            self.assertEqual(output_path, output_dir / "content.json")
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {"blocks": [{"type": "heading", "level": 1, "text": "产品说明"}]},
            )

    def test_convert_file_uses_default_output_path_when_omitted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            output_path = convert_file(md_input)

            self.assertEqual(output_path, Path(temp_dir) / "content.json")
            self.assertTrue(output_path.exists())

    def test_convert_file_keeps_input_filename_when_output_file_name_differs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            custom_output = Path(temp_dir) / "dist" / "custom-name.json"
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            output_path = convert_file(md_input, custom_output)

            self.assertEqual(output_path, Path(temp_dir) / "dist" / "content.json")
            self.assertTrue(output_path.exists())
            self.assertFalse(custom_output.exists())

    def test_run_conversion_records_success_log(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            output_dir = Path(temp_dir) / "dist"
            log_path = Path(temp_dir) / "call-log.log"
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            output_path = run_conversion(md_input, output_dir, log_path=log_path)

            logs = read_log_lines(log_path)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["status"], "success")
            self.assertEqual(logs[0]["input"], str(md_input))
            self.assertEqual(logs[0]["output"], str(output_path))
            self.assertIsNone(logs[0]["error"])
            self.assertRegex(logs[0]["timestamp"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_run_conversion_records_failure_log(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_input = Path(temp_dir) / "missing.md"
            log_path = Path(temp_dir) / "call-log.log"

            with self.assertRaises(FileNotFoundError):
                run_conversion(missing_input, log_path=log_path)

            logs = read_log_lines(log_path)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["status"], "failure")
            self.assertEqual(logs[0]["input"], str(missing_input))
            self.assertIsNone(logs[0]["output"])
            self.assertIn("No such file", logs[0]["error"])

    def test_run_conversion_keeps_latest_50_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_input = Path(temp_dir) / "content.md"
            log_path = Path(temp_dir) / "call-log.log"
            md_input.write_text("# 产品说明\n", encoding="utf-8")

            for index in range(55):
                output_dir = Path(temp_dir) / f"dist-{index}"
                run_conversion(md_input, output_dir, log_path=log_path)

            logs = read_log_lines(log_path)
            self.assertEqual(len(logs), 50)
            self.assertEqual(logs[0]["output"], str(Path(temp_dir) / "dist-5" / "content.json"))
            self.assertEqual(logs[-1]["output"], str(Path(temp_dir) / "dist-54" / "content.json"))


if __name__ == "__main__":
    unittest.main()
