from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, IO
from collections.abc import Container
from modulefinder import ModuleFinder, Module


def collect_modules(base_path: Path, package: str = ".") -> Iterable[tuple[tuple[str], Path, Module]]:
    for module_path in base_path.glob(f"{package}/**/*.py"):
        finder = FlatModuleFinder(path=[str(base_path), *sys.path])
        finder.load_file(str(module_path))

        yield (
            path_to_module_name(module_path, base_path),
            module_path,
            [m for m in finder.modules.values() if not m.__file__ or Path(m.__file__) != module_path],
        )


def path_to_module_name(module_path: Path, base_path: Path):
    rel_path = module_path.relative_to(base_path)
    return rel_path.parent.parts if rel_path.stem == "__init__" else rel_path.parent.parts + (rel_path.stem,)


class FlatModuleFinder(ModuleFinder):
    def __init__(self, path: list[str] | None, excludes: Container[str] = []) -> None:
        super().__init__(path, excludes=excludes)
        self._depth = 0

    def load_module(self, fqname: str, fp: IO[str], pathname: str, file_info: tuple[str, str, str]) -> Module:
        if self._depth > 1:
            return None
        self._depth += 1
        try:
            return super().load_module(fqname, fp, pathname, file_info)
        finally:
            self._depth -= 1
