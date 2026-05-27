import tempfile
import unittest
from pathlib import Path

from app.module.hot_item_collection import server
from app.module.hot_item_collection.config_store import flatten_config, group_config
from app.module.hot_item_collection.project_assets import resolve_config_path_value


class HotItemCollectionTest(unittest.TestCase):
    def test_action_modules_use_current_package_path(self):
        modules = [action["module"] for action in server.list_actions()]

        self.assertTrue(modules)
        for module in modules:
            self.assertTrue(module.startswith("app.module.hot_item_collection."))
            self.assertNotIn("bunny_ai.hot_item_collection", module)

    def test_grouped_config_round_trip_keeps_hot_collection_fields(self):
        flat = {
            "phone": "13800000000",
            "keyword": "口红",
            "country": "马来西亚",
            "category_path": ["美妆个护", "美妆", "口红与唇彩"],
            "product_limit": 2,
            "custom_field": "保留扩展字段",
        }

        grouped = group_config(flat)
        restored = flatten_config(grouped)

        self.assertEqual(grouped["config_schema_version"], 2)
        self.assertEqual(grouped["hot_collection"]["phone"], "13800000000")
        self.assertEqual(restored["category_path"], ["美妆个护", "美妆", "口红与唇彩"])
        self.assertEqual(grouped["other"]["custom_field"], "保留扩展字段")

    def test_flatten_config_accepts_existing_legacy_config_shape(self):
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

        self.assertEqual(flat["phone"], "13800000000")
        self.assertEqual(flat["password"], "secret")
        self.assertEqual(flat["country"], "马来西亚")
        self.assertEqual(flat["product_limit"], 1)

    def test_relative_output_path_resolves_from_repository_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            resolved = resolve_config_path_value("app/result/hot_item_collection/csv", root / "fallback")

        self.assertEqual(resolved, (server.ROOT / "app/result/hot_item_collection/csv").resolve())


if __name__ == "__main__":
    unittest.main()
