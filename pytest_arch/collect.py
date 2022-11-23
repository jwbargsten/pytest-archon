import ast
import importlib.util
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Iterable

from pytest_arch.core_modules import list_core_modules

# https://docs.djangoproject.com/en/4.1/_modules/django/utils/module_loading/
# https://stackoverflow.com/questions/54325116/can-i-handle-imports-in-an-abstract-syntax-tree
# https://bugs.python.org/issue38721
# https://github.com/0cjs/sedoc/blob/master/lang/python/importers.md


def collect_imports_from_path(path, package):
    for py_file in Path(path).glob("**/*.py"):
        module_name = path_to_module(py_file, path, package)
        tree = ast.parse(py_file.read_bytes())
        import_it = extract_imports_ast(tree, module_name)
        yield module_name, set(import_it)


def collect_imports(package):
    if isinstance(package, ModuleType):
        if not hasattr(package, "__path__"):
            raise AttributeError("module {name} does not have __path__".format(name=package.__name__))
        package = package.__name__

    all_imports = {}
    spec = importlib.util.find_spec(package)
    if not spec:
        raise ModuleNotFoundError(f"could not find the module {package!r}", name=package)

    pkg_dir = os.path.dirname(spec.origin)

    for name, imports in collect_imports_from_path(pkg_dir, package):
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


def extract_imports_ast(tree, package: str, resolve=True) -> Iterable[str]:
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
    for imports in data.values():
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


def resolve_module_or_object(fqname):
    if fqname in list_core_modules():
        return fqname

    parent_name = fqname.rpartition(".")[0]

    # shortcut to deal with e.g. from __future__ import annotations
    if parent_name in list_core_modules():
        return parent_name

    spec = None
    try:
        spec = importlib.util.find_spec(fqname)
    except ModuleNotFoundError as ex:
        parent_spec = importlib.util.find_spec(parent_name)
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
