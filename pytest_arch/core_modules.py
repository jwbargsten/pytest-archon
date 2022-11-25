import sys
from functools import lru_cache
from pathlib import Path
from typing import FrozenSet

import pkg_resources


@lru_cache()
def core_modules(version=None) -> FrozenSet[str]:
    if version is None:
        version = sys.version_info
    if version >= (3, 10):
        modules = sys.stdlib_module_names | set(sys.builtin_module_names)
    else:
        modules_file = Path(
            pkg_resources.resource_filename(
                "pytest_arch", str(Path("assets", "core-module-lists", f"{version[0]}.{version[1]}.txt"))
            )
        )
        if not modules_file.exists():
            raise FileNotFoundError(
                f"{modules_file} does not exist, perhaps your python version is not supported"
            )
        modules = frozenset(modules_file.read_text().splitlines())
    return modules
