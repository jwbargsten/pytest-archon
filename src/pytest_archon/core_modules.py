import importlib.resources
import sys
from functools import lru_cache
from typing import FrozenSet


@lru_cache
def core_modules(version=None) -> FrozenSet[str]:
    if version is None:
        version = sys.version_info
    if version >= (3, 10):
        modules = sys.stdlib_module_names | set(sys.builtin_module_names)  # type: ignore[attr-defined]
    else:
        modules_file = _module_file_path(version)
        if not modules_file.exists():
            raise FileNotFoundError(
                f"{modules_file} does not exist, perhaps your python version is not supported"
            )
        modules = frozenset(modules_file.read_text().splitlines())
    return modules


def _module_file_path(version):
    if sys.version_info < (3, 9):
        with importlib.resources.path("pytest_archon", "assets") as p:
            return p / "core-module-lists" / f"{version[0]}.{version[1]}.txt"
    return (
        importlib.resources.files("pytest_archon")
        / "assets"
        / "core-module-lists"
        / f"{version[0]}.{version[1]}.txt"
    )
