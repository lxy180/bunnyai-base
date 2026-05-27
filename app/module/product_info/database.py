#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"
DEFAULT_DATABASE_PATH = MODULE_DIR / "product_info.sqlite3"


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS product_info_document (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT NOT NULL UNIQUE,
        product_name_zh TEXT NOT NULL,
        info_file_name TEXT NOT NULL,
        info_file_path TEXT NOT NULL UNIQUE,
        product_created_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_report_document (
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
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_product_report_product_code
        ON product_report_document(product_code)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_product_report_product_info_id
        ON product_report_document(product_info_id)
    """,
]


def load_config(config_path=CONFIG_PATH):
    path = Path(config_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_database_path(db_path=None, config_path=CONFIG_PATH):
    raw_path = db_path
    if raw_path is None:
        raw_path = load_config(config_path).get("sqlite_database_path", "")
    if not str(raw_path or "").strip():
        return DEFAULT_DATABASE_PATH

    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def initialize_database(db_path=None):
    database_path = resolve_database_path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

    return database_path


def record_product_info_document(
    db_path=None,
    *,
    product_code,
    product_name_zh,
    info_file_name,
    info_file_path,
    product_created_at,
):
    database_path = initialize_database(db_path)
    product_code = _require_text(product_code, "productCode")
    product_name_zh = _require_text(product_name_zh, "productNameZh")
    info_file_name = _require_text(info_file_name, "infoFileName")
    info_file_path = _require_text(info_file_path, "infoFilePath")
    product_created_at = _require_text(product_created_at, "createdAt")
    now_text = _now_text()

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            INSERT INTO product_info_document (
                product_code,
                product_name_zh,
                info_file_name,
                info_file_path,
                product_created_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_code) DO UPDATE SET
                product_name_zh = excluded.product_name_zh,
                info_file_name = excluded.info_file_name,
                info_file_path = excluded.info_file_path,
                product_created_at = excluded.product_created_at,
                updated_at = excluded.updated_at
            """,
            (
                product_code,
                product_name_zh,
                info_file_name,
                info_file_path,
                product_created_at,
                now_text,
                now_text,
            ),
        )
        row = connection.execute(
            "SELECT id FROM product_info_document WHERE product_code = ?",
            (product_code,),
        ).fetchone()

    return row[0]


def record_product_report_document(
    db_path=None,
    *,
    product_code,
    report_file_path,
):
    database_path = initialize_database(db_path)
    product_code = _require_text(product_code, "productCode")
    report_file_path = _require_text(report_file_path, "reportFilePath")
    report_file_name = Path(report_file_path).name
    now_text = _now_text()

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        product_row = connection.execute(
            """
            SELECT id, product_name_zh
            FROM product_info_document
            WHERE product_code = ?
            """,
            (product_code,),
        ).fetchone()
        if product_row is None:
            raise ValueError(f"产品信息不存在，无法记录产品报告：{product_code}")

        product_info_id, product_name_zh = product_row
        report_no = (
            connection.execute(
                """
                SELECT COALESCE(MAX(report_no), 0) + 1
                FROM product_report_document
                WHERE product_info_id = ?
                """,
                (product_info_id,),
            ).fetchone()[0]
        )
        connection.execute(
            """
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_info_id,
                product_code,
                report_no,
                product_name_zh,
                report_file_name,
                report_file_path,
                now_text,
                now_text,
            ),
        )

    return report_no


def _now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _require_text(value, field_name):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} 不能为空")
    return text
