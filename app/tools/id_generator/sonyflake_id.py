from pathlib import Path
import sys
from typing import Iterator, Optional


TOOL_DIR = Path(__file__).resolve().parent
SONYFLAKE_DIR = TOOL_DIR / "sonyflake-py"
sys.path.insert(0, str(SONYFLAKE_DIR))

from sonyflake import SonyFlake  # noqa: E402


def create_generator(machine_id: Optional[int] = None) -> SonyFlake:
    return SonyFlake(machine_id=machine_id)


def generate_id(machine_id: Optional[int] = None) -> int:
    return create_generator(machine_id).next_id()


def generate_ids(count: int, machine_id: Optional[int] = None) -> Iterator[int]:
    if count < 1:
        raise ValueError("count 必须大于等于 1")

    sf = create_generator(machine_id)
    for _ in range(count):
        yield sf.next_id()
