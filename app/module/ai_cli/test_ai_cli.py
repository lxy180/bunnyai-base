import json
import tempfile
import unittest
from pathlib import Path

from app.module.ai_cli import (
    AiCliRequest,
    build_command,
)


class AiCliCommandTest(unittest.TestCase):
    def test_codex_command_uses_workspace_arguments_for_local_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            doc_path = root / "docs" / "需求.md"
            image_path = root / "images" / "截图.png"
            doc_content = "不能进入 prompt 的内容"
            doc_path.parent.mkdir()
            image_path.parent.mkdir()
            doc_path.write_text(doc_content, encoding="utf-8")
            image_path.write_bytes(b"fake image")

            spec = build_command(
                AiCliRequest(
                    provider="codex",
                    prompt="请分析已关联文件。",
                    files=[doc_path, image_path],
                    workingDirectory=root,
                    executionMode="headless",
                )
            )

        self.assertEqual(spec.args[0:2], ["codex", "exec"])
        self.assertIn("--cd", spec.args)
        self.assertIn("--add-dir", spec.args)
        self.assertIn("--image", spec.args)
        self.assertEqual(spec.prompt, "请分析已关联文件。")
        self.assertNotIn(str(doc_path), spec.prompt)
        self.assertNotIn(doc_content, spec.prompt)

    def test_claude_command_uses_add_dir_for_local_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "input" / "brief.md"
            file_path.parent.mkdir()
            file_path.write_text("本地文件内容", encoding="utf-8")

            spec = build_command(
                AiCliRequest(
                    provider="claude",
                    prompt="请根据已关联资料输出方案。",
                    files=[file_path],
                    workingDirectory=root,
                    executionMode="headless",
                    outputFormat="json",
                )
            )

        self.assertEqual(spec.args[0], "claude")
        self.assertIn("--print", spec.args)
        self.assertIn("--add-dir", spec.args)
        self.assertIn("--output-format", spec.args)
        self.assertEqual(spec.prompt, "请根据已关联资料输出方案。")
        self.assertNotIn(str(file_path), spec.prompt)

    def test_gemini_command_uses_include_directories_for_local_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "data" / "sample.md"
            file_path.parent.mkdir()
            file_path.write_text("样例内容", encoding="utf-8")

            spec = build_command(
                AiCliRequest(
                    provider="gemini",
                    prompt="请总结已关联资料。",
                    files=[file_path],
                    workingDirectory=root,
                    executionMode="headless",
                )
            )

        self.assertEqual(spec.args[0], "gemini")
        self.assertIn("--prompt", spec.args)
        self.assertIn("--include-directories", spec.args)
        self.assertEqual(spec.prompt, "请总结已关联资料。")
        self.assertNotIn(str(file_path), spec.prompt)

    def test_rejects_missing_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "关联文件不存在"):
                build_command(
                    AiCliRequest(
                        provider="codex",
                        prompt="请分析已关联文件。",
                        files=[root / "missing.md"],
                        workingDirectory=root,
                    )
                )

    def test_rejects_prompt_containing_markdown_file_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "brief.md"
            file_path.write_text("这是一段不允许直接塞进 prompt 的 Markdown 文档内容。", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "prompt 中不能直接包含关联文件内容"):
                build_command(
                    AiCliRequest(
                        provider="gemini",
                        prompt="请分析：这是一段不允许直接塞进 prompt 的 Markdown 文档内容。",
                        files=[file_path],
                        workingDirectory=root,
                    )
                )

    def test_uses_working_directory_from_config_when_request_omits_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_cwd = root / "workspace"
            configured_cwd.mkdir()
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps({"workingDirectory": str(configured_cwd)}, ensure_ascii=False),
                encoding="utf-8",
            )

            spec = build_command(
                AiCliRequest(
                    provider="codex",
                    prompt="请执行任务。",
                    configPath=config_path,
                    executionMode="headless",
                )
            )

        self.assertEqual(spec.cwd, configured_cwd.resolve())
        self.assertIn(str(configured_cwd.resolve()), spec.args)


if __name__ == "__main__":
    unittest.main()
