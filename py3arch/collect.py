from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable

from py3arch.core_modules import list_core_modules
from py3arch.import_finder import resolve_import_from, resolve_module_or_object, explode_import


def collect_modules(base_path: Path, package: str = ".") -> Iterable[tuple[str, str]]:
    for py_file in base_path.glob(f"{package}/**/*.py"):
        module_name = path_to_module(py_file, base_path)
        tree = ast.parse(py_file.read_bytes())
        imported_iter = find_imports(tree, module_name, sys.path + [str(base_path)])
        yield module_name, set(imported_iter)


def path_to_module(module_path: Path, base_path: Path) -> str:
    rel_path = module_path.relative_to(base_path)
    return ".".join((rel_path.parent / rel_path.stem).parts).removesuffix(".__init__")


def find_imports(
    tree, package: str, path: Iterable[str] = None, resolve=True, explode=False
) -> Iterable[str]:
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
                    for i in explode_import(fqname):
                        yield i
                else:
                    yield fqname


def collect_from_pkg(module):
    core_modules = list_core_modules()
    if not hasattr(module, "__path__"):
        raise AttributeError("module {name} does not have __path__".format(name=module.__name__))
    all_imports = {}
    for path in [Path(p) for p in module.__path__]:
        for name, imports in collect_modules(path.parent, path.name):
            direct_imports = {i for i in imports if i != name and i not in core_modules}
            if name in all_imports:
                raise KeyError("WTF? duplicate module {}".format(name))
            all_imports[name] = {"direct": direct_imports}
    _update_with_transitive_imports(all_imports)
    return all_imports


def _update_with_transitive_imports(data):
    for name, imports in data.items():
        transitive = []
        is_circular = False
        seen = {}
        for imp in imports["direct"]:
            node = data.get(imp, None)
            if node is None:
                continue
            stack = [(imp, n) for n in node["direct"]]
            while stack:
                head = stack[0]
                stack = stack[1:]

                transitive.append(head[1])
                if head in seen:
                    is_circular = True
                    continue
                seen[head] = True
                child = data.get(head[1], None)
                if child is None:
                    continue
                stack.extend([(head[1], n) for n in child["direct"]])

        imports["transitive"] = set(transitive) - imports["direct"]
        imports["is_circular"] = is_circular
