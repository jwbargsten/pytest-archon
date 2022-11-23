import sys
from functools import lru_cache
from pathlib import Path
from typing import List

import pkg_resources


@lru_cache()
def list_core_modules(version=None) -> List[str]:
    if version is None:
        version = sys.version_info
    if version >= (3, 10):
        modules = list(set(list(sys.stdlib_module_names) + list(sys.builtin_module_names)))
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
        modules = modules_file.read_text().splitlines()
    return modules
