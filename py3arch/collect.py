from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable
from py3arch.import_finder import resolve_import_from, resolve_module_or_object,explode_import


def collect_modules(base_path: Path, package: str = ".") -> Iterable[tuple[str, str]]:
    for py_file in base_path.glob(f"{package}/**/*.py"):
        module_name = path_to_module_name(py_file, base_path)
        tree = ast.parse(py_file.read_bytes())
        imported_iter = find_imports(tree, module_name, sys.path + [str(base_path)])
        yield module_name, list(imported_iter)


def path_to_module_name(module_path: Path, base_path: Path) -> str:
    rel_path = module_path.relative_to(base_path)
    return ".".join(
        rel_path.parent.parts if rel_path.stem == "__init__" else rel_path.parent.parts + (rel_path.stem,)
    )


def find_imports(tree, package: str, path: Iterable[str] = None, resolve=True, explode=True) -> Iterable[str]:
    if path is None:
        path = sys.path
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                fqname = resolve_import_from(alias.name, node.module, package=package, level=node.level)
                if resolve:
                    fqname = resolve_module_or_object(fqname, path=path)
                if explode:
                    imports = explode_import(fqname)
                else:
                    imports = [fqname]
                for i in imports:
                    yield i
