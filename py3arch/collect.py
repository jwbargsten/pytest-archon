import os
import sys
import importlib
import importlib.util

from py3arch import list_core_modules
from py3arch.core_modules import list_core_modules
import ast
from importlib.util import find_spec

import ast
from pathlib import Path
from typing import Iterable
import re

CORE_MODULES = list_core_modules()

def collect_imports_per_file(path, package):
    for py_file in Path(path).glob(f"**/*.py"):
        module_name = path_to_module(py_file, path, package)
        tree = ast.parse(py_file.read_bytes())
        import_it = extract_imports_ast(tree, module_name)
        yield module_name, set(import_it)

def collect_imports(package):
    all_imports = {}
    spec = find_spec(package)
    if not spec:
        raise ModuleNotFoundError("FIXME")

    pkg_dir = os.path.dirname(spec.origin)

    for name, imports in collect_imports_per_file(pkg_dir, package):
        direct_imports = {imp for imp in imports if imp != name}
        if name in all_imports:
            raise KeyError("WTF? duplicate module {}".format(name))
        all_imports[name] = {"direct": direct_imports}
    update_with_transitive_imports(all_imports)
    return all_imports



def path_to_module(module_path: Path, base_path: Path, package=None) -> str:
    rel_path = module_path.relative_to(base_path)

    if package:
        parts = [package]
    else:
        parts = []
    parts.extend(rel_path.parent.parts)

    if rel_path.stem != "__init__":
        parts.append(rel_path.stem)
    module = ".".join(parts)
    # some very basic sanitation
    return re.sub(r"\.+", ".", module)


def extract_imports_ast(
    tree, package: str, resolve=True
) -> Iterable[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                fqname = resolve_import_from(alias.name, node.module, package=package, level=node.level)
                if resolve:
                    yield resolve_module_or_object(fqname)
                else:
                    yield fqname



def update_with_transitive_imports(data):
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


# https://stackoverflow.com/questions/54325116/can-i-handle-imports-in-an-abstract-syntax-tree
# https://bugs.python.org/issue38721
# https://github.com/0cjs/sedoc/blob/master/lang/python/importers.md


def resolve_module_or_object(fqname, path=None):
    if path is None:
        path = sys.path

    if fqname in CORE_MODULES:
        return fqname

    parent_name = fqname.rpartition('.')[0]

    # shortcut to deal with e.g. from __future__ import annotations
    if parent_name in CORE_MODULES:
        return parent_name

    spec = None
    try:
        spec = importlib.util.find_spec(fqname, path)
    except ModuleNotFoundError as ex:
        parent_spec = importlib.util.find_spec(parent_name, path)
        # if we cannot find the parent, then something is off
        if not parent_spec:
            raise ex

    return fqname if spec else fqname.rpartition(".")[0]


# TODO replace with importlib.util.resolve_name ?
def resolve_import_from(name, module=None, package=None, level=None):
    if not level:
        # absolute import
        if name == "*":
            return module
        return name if module is None else f"{module}.{name}"

    # taken from importlib._bootstrap._resolve_name
    bits = package.rsplit(".", level)
    if len(bits) < level:
        raise ImportError("attempted relative import beyond top-level package")
    base = bits[0]

    # relative import
    if module is None:
        # from . import moduleX
        prefix = base
    else:
        # from .moduleZ import moduleX
        prefix = f"{base}.{module}"
    if name == "*":
        return prefix
    return f"{prefix}.{name}"
