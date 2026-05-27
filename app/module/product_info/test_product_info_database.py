import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.module.product_info.database import (
    initialize_database,
    record_product_info_document,
    record_product_report_document,
)


class ProductInfoDatabaseTest(unittest.TestCase):
    def test_initialize_database_creates_product_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"

            initialize_database(db_path)

            with sqlite3.connect(db_path) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertIn("product_info_document", table_names)
        self.assertIn("product_report_document", table_names)

    def test_record_product_info_document_upserts_by_product_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)

            first_id = record_product_info_document(
                db_path,
                product_code="SHG-001",
                product_name_zh="智能桌面种植机",
                info_file_name="智能桌面种植机.md",
                info_file_path="knowledge/产品信息/智能桌面种植机.md",
                product_created_at="2026-05-23 13:52:00",
            )
            second_id = record_product_info_document(
                db_path,
                product_code="SHG-001",
                product_name_zh="智能桌面种植机 Pro",
                info_file_name="智能桌面种植机 Pro.md",
                info_file_path="knowledge/产品信息/智能桌面种植机 Pro.md",
                product_created_at="2026-05-23 13:52:00",
            )

            with sqlite3.connect(db_path) as connection:
                rows = list(
                    connection.execute(
                        "SELECT product_code, product_name_zh, info_file_name FROM product_info_document"
                    )
                )

        self.assertEqual(first_id, second_id)
        self.assertEqual(rows, [("SHG-001", "智能桌面种植机 Pro", "智能桌面种植机 Pro.md")])

    def test_record_product_report_document_allocates_incremental_report_no(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)
            record_product_info_document(
                db_path,
                product_code="SHG-001",
                product_name_zh="智能桌面种植机",
                info_file_name="智能桌面种植机.md",
                info_file_path="knowledge/产品信息/智能桌面种植机.md",
                product_created_at="2026-05-23 13:52:00",
            )

            first_report_no = record_product_report_document(
                db_path,
                product_code="SHG-001",
                report_file_path="knowledge/产品信息/产品报告/智能桌面种植机-信息报告-1.md",
            )
            second_report_no = record_product_report_document(
                db_path,
                product_code="SHG-001",
                report_file_path="knowledge/产品信息/产品报告/智能桌面种植机-信息报告-2.md",
            )

            with sqlite3.connect(db_path) as connection:
                rows = list(
                    connection.execute(
                        """
                        SELECT product_code, report_no, product_name_zh_snapshot, report_file_name
                        FROM product_report_document
                        ORDER BY report_no
                        """
                    )
                )

        self.assertEqual(first_report_no, 1)
        self.assertEqual(second_report_no, 2)
        self.assertEqual(
            rows,
            [
                ("SHG-001", 1, "智能桌面种植机", "智能桌面种植机-信息报告-1.md"),
                ("SHG-001", 2, "智能桌面种植机", "智能桌面种植机-信息报告-2.md"),
            ],
        )

    def test_record_product_report_document_requires_existing_product(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)

            with self.assertRaisesRegex(ValueError, "产品信息不存在"):
                record_product_report_document(
                    db_path,
                    product_code="MISSING-001",
                    report_file_path="knowledge/产品信息/产品报告/缺失产品-信息报告-1.md",
                )

    def test_record_product_info_document_trims_product_code_before_querying_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)

            product_info_id = record_product_info_document(
                db_path,
                product_code=" SHG-001 ",
                product_name_zh="智能桌面种植机",
                info_file_name="智能桌面种植机.md",
                info_file_path="knowledge/产品信息/智能桌面种植机.md",
                product_created_at="2026-05-23 13:52:00",
            )

            with sqlite3.connect(db_path) as connection:
                row = connection.execute(
                    "SELECT id, product_code FROM product_info_document"
                ).fetchone()

        self.assertEqual(product_info_id, row[0])
        self.assertEqual(row[1], "SHG-001")


if __name__ == "__main__":
    unittest.main()
