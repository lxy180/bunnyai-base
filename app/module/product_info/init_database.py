#!/usr/bin/env python3
from pathlib import Path
import sys


try:
    from .database import initialize_database
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from app.module.product_info.database import initialize_database


def main():
    database_path = initialize_database()
    print(f"产品信息数据库已初始化：{database_path}")


if __name__ == "__main__":
    main()
