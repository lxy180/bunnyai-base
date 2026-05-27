import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.module.hot_item_collection import server
from app.module.hot_item_collection.config_store import flatten_config, group_config
from app.module.hot_item_collection.project_assets import fastmoss_account_signature, resolve_config_path_value


class HotItemCollectionTest(unittest.TestCase):
    def test_action_modules_use_current_package_path(self):
        modules = [action["module"] for action in server.list_actions()]

        self.assertTrue(modules)
        for module in modules:
            self.assertTrue(module.startswith("app.module.hot_item_collection."))
            self.assertNotIn("bunny_ai.hot_item_collection", module)

    def test_category_config_defaults_to_shared_tools_file(self):
        expected_path = server.ROOT / "app" / "tools" / "fastmoss_category_config.json"

        self.assertEqual(server.category_config_path({}), expected_path)
        self.assertTrue(server.load_category_config())

    def test_web_config_exposes_default_category_config_path(self):
        grouped = server.load_grouped_config()

        self.assertEqual(
            grouped["category_config_path"],
            "app/tools/fastmoss_category_config.json",
        )

    def test_category_config_path_can_be_configured(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_category.json"
            custom_path.write_text('[{"c_name": "自定义类目"}]', encoding="utf-8")

            categories = server.load_category_config({"category_config_path": str(custom_path)})

        self.assertEqual(categories, [{"c_name": "自定义类目"}])

    def test_fastmoss_account_signature_uses_module_config(self):
        with patch.dict("os.environ", {"FASTMOSS_PHONE": "19900000000", "FASTMOSS_PASSWORD": "env-secret"}):
            signature = fastmoss_account_signature({"phone": "13800000000", "password": "secret"})

        self.assertEqual(signature["phone"], "13800000000")
        self.assertTrue(signature["password_sha256"])

    def test_grouped_config_round_trip_keeps_requested_config_shape(self):
        flat = {
            "phone": "13800000000",
            "password": "secret",
            "keyword": "口红",
            "country": "马来西亚",
            "category_path": ["美妆个护", "美妆", "口红与唇彩"],
            "category_config_path": "app/tools/fastmoss_category_config.json",
            "show_browser": False,
            "product_limit": 2,
            "csv_output_dir": "",
            "video_output_dir": "",
        }

        grouped = group_config(flat)
        restored = flatten_config(grouped)

        self.assertEqual(set(grouped), {"show_browser", "category_config_path", "login_params", "filter_condition", "result_path"})
        self.assertEqual(grouped["login_params"]["phone"], "13800000000")
        self.assertEqual(grouped["login_params"]["password"], "secret")
        self.assertEqual(grouped["category_config_path"], "app/tools/fastmoss_category_config.json")
        self.assertEqual(grouped["filter_condition"]["keyword"], "口红")
        self.assertEqual(grouped["result_path"]["csv_output_dir"], "")
        self.assertEqual(restored["category_path"], ["美妆个护", "美妆", "口红与唇彩"])

    def test_flatten_config_reads_requested_config_shape(self):
        config = {
            "show_browser": False,
            "category_config_path": "app/tools/fastmoss_category_config.json",
            "login_params": {
                "phone": "13800000000",
                "password": "secret",
            },
            "filter_condition": {
                "category_path": ["美妆个护", "头部护理与造型", "染发用品"],
                "keyword": "",
                "country": "马来西亚",
                "product_limit": 1,
            },
            "result_path": {
                "csv_output_dir": "",
                "video_output_dir": "",
            },
        }

        flat = flatten_config(config)

        self.assertEqual(flat["phone"], "13800000000")
        self.assertEqual(flat["password"], "secret")
        self.assertEqual(flat["country"], "马来西亚")
        self.assertEqual(flat["category_path"], ["美妆个护", "头部护理与造型", "染发用品"])
        self.assertEqual(flat["category_config_path"], "app/tools/fastmoss_category_config.json")

    def test_flatten_config_ignores_legacy_config_shape(self):
        legacy = {
            "fastmoss_username": "13800000000",
            "fastmoss_password": "secret",
            "filter—condition": {
                "country": "马来西亚",
                "product_limit": 1,
                "show_browser": False,
            },
        }

        flat = flatten_config(legacy)

        self.assertNotIn("phone", flat)
        self.assertNotIn("password", flat)
        self.assertNotIn("country", flat)
        self.assertNotIn("product_limit", flat)
        self.assertNotIn("fastmoss_username", flat)
        self.assertNotIn("fastmoss_password", flat)

    def test_relative_output_path_resolves_from_repository_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            resolved = resolve_config_path_value("app/result/hot_item_collection/csv", root / "fallback")

        self.assertEqual(resolved, (server.ROOT / "app/result/hot_item_collection/csv").resolve())


if __name__ == "__main__":
    unittest.main()
