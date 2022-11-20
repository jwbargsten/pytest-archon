from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable


def collect_modules(base_path: Path, package: str = ".") -> Iterable[tuple[str, str]]:
    for module_path in base_path.glob(f"{package}/**/*.py"):
        module_name = path_to_module_name(module_path, base_path)
        for imported in find_imports(ast.parse(module_path.read_bytes()), str(module_path)):
            yield module_name, imported


def path_to_module_name(module_path: Path, base_path: Path) -> str:
    rel_path = module_path.relative_to(base_path)
    return ".".join(
        rel_path.parent.parts if rel_path.stem == "__init__" else rel_path.parent.parts + (rel_path.stem,)
    )


def find_imports(root, current_module) -> Iterable[str]:
    for node in ast.walk(root):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                assert node.module
                yield from (f"{node.module}.{alias.name}" for alias in node.names)
            else:
                yield from (
                    f"{relative(current_module, node.module, node.level)}.{alias.name}"
                    for alias in node.names
                )


def relative(current_module, module, level):
    parent = current_module.rsplit(".", level)[0]
    return f"{parent}.{module}" if module else parent
