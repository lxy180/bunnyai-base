import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

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

            with closing(sqlite3.connect(db_path)) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertIn("product_info_document", table_names)
        self.assertIn("product_report_document", table_names)

    def test_initialize_database_does_not_create_autoincrement_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"

            initialize_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                table_sql = {
                    row[0]: row[1]
                    for row in connection.execute(
                        "SELECT name, sql FROM sqlite_master WHERE type = 'table'"
                    )
                }

        self.assertNotIn("AUTOINCREMENT", table_sql["product_info_document"].upper())
        self.assertNotIn("AUTOINCREMENT", table_sql["product_report_document"].upper())

    def test_initialize_database_migrates_existing_autoincrement_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            with closing(sqlite3.connect(db_path)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE product_info_document (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_code TEXT NOT NULL UNIQUE,
                        product_name_zh TEXT NOT NULL,
                        info_file_name TEXT NOT NULL,
                        info_file_path TEXT NOT NULL UNIQUE,
                        product_created_at TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE product_report_document (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_info_id INTEGER NOT NULL,
                        product_code TEXT NOT NULL,
                        report_no INTEGER NOT NULL CHECK (report_no > 0),
                        product_name_zh_snapshot TEXT NOT NULL,
                        report_file_name TEXT NOT NULL,
                        report_file_path TEXT NOT NULL UNIQUE,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (product_info_id)
                            REFERENCES product_info_document(id)
                            ON DELETE CASCADE,
                        UNIQUE (product_info_id, report_no)
                    );
                    INSERT INTO product_info_document (
                        product_code,
                        product_name_zh,
                        info_file_name,
                        info_file_path,
                        product_created_at,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        'SHG-001',
                        '智能桌面种植机',
                        '智能桌面种植机.md',
                        'knowledge/产品信息/智能桌面种植机.md',
                        '2026-05-23 13:52:00',
                        '2026-05-23 13:52:00',
                        '2026-05-23 13:52:00'
                    );
                    INSERT INTO product_report_document (
                        product_info_id,
                        product_code,
                        report_no,
                        product_name_zh_snapshot,
                        report_file_name,
                        report_file_path,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        1,
                        'SHG-001',
                        1,
                        '智能桌面种植机',
                        '智能桌面种植机-信息报告-1.md',
                        'knowledge/产品信息/产品报告/智能桌面种植机-信息报告-1.md',
                        '2026-05-23 13:52:00',
                        '2026-05-23 13:52:00'
                    );
                    """
                )
                connection.commit()

            with patch("app.module.product_info.database.generate_id", side_effect=[9001, 9101]):
                initialize_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                table_sql = {
                    row[0]: row[1]
                    for row in connection.execute(
                        "SELECT name, sql FROM sqlite_master WHERE type = 'table'"
                    )
                }
                product_row = connection.execute(
                    "SELECT id, product_code FROM product_info_document"
                ).fetchone()
                report_row = connection.execute(
                    "SELECT id, product_info_id, product_code FROM product_report_document"
                ).fetchone()

        self.assertNotIn("AUTOINCREMENT", table_sql["product_info_document"].upper())
        self.assertNotIn("AUTOINCREMENT", table_sql["product_report_document"].upper())
        self.assertEqual(product_row, (9001, "SHG-001"))
        self.assertEqual(report_row, (9101, 9001, "SHG-001"))

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

            with closing(sqlite3.connect(db_path)) as connection:
                rows = list(
                    connection.execute(
                        "SELECT product_code, product_name_zh, info_file_name FROM product_info_document"
                    )
                )

        self.assertEqual(first_id, second_id)
        self.assertEqual(rows, [("SHG-001", "智能桌面种植机 Pro", "智能桌面种植机 Pro.md")])

    def test_record_product_info_document_uses_generated_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)

            with patch("app.module.product_info.database.generate_id", return_value=9001):
                product_info_id = record_product_info_document(
                    db_path,
                    product_code="SHG-001",
                    product_name_zh="智能桌面种植机",
                    info_file_name="智能桌面种植机.md",
                    info_file_path="knowledge/产品信息/智能桌面种植机.md",
                    product_created_at="2026-05-23 13:52:00",
                )

            with closing(sqlite3.connect(db_path)) as connection:
                stored_id = connection.execute(
                    "SELECT id FROM product_info_document WHERE product_code = 'SHG-001'"
                ).fetchone()[0]

        self.assertEqual(product_info_id, 9001)
        self.assertEqual(stored_id, 9001)

    def test_record_product_report_document_uses_generated_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "product_info.sqlite3"
            initialize_database(db_path)
            with patch("app.module.product_info.database.generate_id", return_value=9001):
                record_product_info_document(
                    db_path,
                    product_code="SHG-001",
                    product_name_zh="智能桌面种植机",
                    info_file_name="智能桌面种植机.md",
                    info_file_path="knowledge/产品信息/智能桌面种植机.md",
                    product_created_at="2026-05-23 13:52:00",
                )

            with patch("app.module.product_info.database.generate_id", return_value=9101):
                record_product_report_document(
                    db_path,
                    product_code="SHG-001",
                    report_file_path="knowledge/产品信息/产品报告/智能桌面种植机-信息报告-1.md",
                )

            with closing(sqlite3.connect(db_path)) as connection:
                stored_id = connection.execute(
                    "SELECT id FROM product_report_document WHERE product_code = 'SHG-001'"
                ).fetchone()[0]

        self.assertEqual(stored_id, 9101)

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

            with closing(sqlite3.connect(db_path)) as connection:
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

            with closing(sqlite3.connect(db_path)) as connection:
                row = connection.execute(
                    "SELECT id, product_code FROM product_info_document"
                ).fetchone()

        self.assertEqual(product_info_id, row[0])
        self.assertEqual(row[1], "SHG-001")


if __name__ == "__main__":
    unittest.main()
