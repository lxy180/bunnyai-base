# ID 生成工具使用说明

本目录提供基于 `sonyflake-py` 的分布式唯一 ID 生成能力，供外部 Python 程序直接调用，也保留命令行生成入口。

## 目录结构

```text
id_generator/
├── __init__.py
├── sonyflake_id.py
├── sonyflake-id
└── sonyflake-py/
```

## Python 调用方式

推荐外部模块按当前文件位置向上查找 `app` 目录，再把 `app/tools` 加入 `sys.path`，然后从 `id_generator` 导入。

```python
from pathlib import Path
import sys


def find_app_dir(start: Path) -> Path:
    for path in (start, *start.parents):
        if path.name == "app" and (path / "tools" / "id_generator").exists():
            return path
    raise RuntimeError("未找到 app/tools/id_generator，请确认调用文件位于项目 app 目录内")


APP_DIR = find_app_dir(Path(__file__).resolve())
sys.path.insert(0, str(APP_DIR / "tools"))

from id_generator import generate_id

new_id = generate_id()
print(new_id)
```

## 常用接口

### 生成单个 ID

```python
from id_generator import generate_id

new_id = generate_id()
```

### 批量生成 ID

```python
from id_generator import generate_ids

ids = list(generate_ids(10))
```

### 指定机器号

`machine_id` 用于区分不同机器或不同进程来源，取值范围是 `0x0000` 到 `0xffff`。

```python
from id_generator import generate_id, generate_ids

new_id = generate_id(machine_id=0x1234)
ids = list(generate_ids(10, machine_id=0x1234))
```

### 复用生成器

高频生成 ID 时，建议复用同一个生成器实例，避免每次调用都重新初始化。

```python
from id_generator import create_generator

sf = create_generator(machine_id=0x1234)

first_id = sf.next_id()
second_id = sf.next_id()
```

## 直接导入底层封装

如果外部程序只方便把 `id_generator` 目录加入 `sys.path`，也可以直接导入 `sonyflake_id`。

```python
from pathlib import Path
import sys


def find_app_dir(start: Path) -> Path:
    for path in (start, *start.parents):
        if path.name == "app" and (path / "tools" / "id_generator").exists():
            return path
    raise RuntimeError("未找到 app/tools/id_generator，请确认调用文件位于项目 app 目录内")


APP_DIR = find_app_dir(Path(__file__).resolve())
sys.path.insert(0, str(APP_DIR / "tools" / "id_generator"))

from sonyflake_id import generate_id

new_id = generate_id()
```

## 命令行调用

在 `app` 目录下执行：

```bash
./tools/id_generator/sonyflake-id
./tools/id_generator/sonyflake-id --count 5
./tools/id_generator/sonyflake-id --machine-id 0x1234
./tools/id_generator/sonyflake-id --count 5 --machine-id 0x1234
```

## 注意事项

- `generate_id()` 每次会创建一个新的生成器，适合低频调用。
- 高频生成时使用 `create_generator()` 复用实例。
- 多台机器或多个长期运行进程同时生成 ID 时，建议显式配置不同的 `machine_id`。
- `count` 必须大于等于 `1`。
