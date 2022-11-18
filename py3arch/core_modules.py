import pkg_resources
import sys
from pathlib import Path


def list_core_modules(version=None) -> list[str]:
    if version is None:
        version = [sys.version_info.major, sys.version_info.minor]
    if version[0] == 3 and version[1] > 9:
        modules = list(set(list(sys.stdlib_module_names) + list(sys.builtin_module_names)))
    else:
        modules_file = Path(
            pkg_resources.resource_filename(
                "py3arch", str(Path("assets", "core-module-lists", f"{version[0]}.{version[1]}.txt"))
            )
        )
        if not modules_file.exists():
            raise FileNotFoundError(
                f"{modules_file} does not exist, perhaps your python version is not supported"
            )
        modules = modules_file.read_text().splitlines()
    return modules
