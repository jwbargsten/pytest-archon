import ast
import importlib.util
import os
import re
import sys
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
                    yield resolve_module_or_object_by_path(fqname)
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


# I'm not sure what to do with this function.
# importlib.util.find_spec is flaky and sometimes doesn't work
# for now we use resolve_module_or_object_by_path till I figure
# out what the issue is
def resolve_module_or_object_by_spec(fqname):
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


def resolve_module_or_object_by_path(fqname, path=None):
    if "." not in fqname:
        return fqname

    if fqname in list_core_modules():
        return fqname

    parts = fqname.split(".")
    head = parts[0]
    parent_name = ".".join(parts[:-1])

    # shortcut to deal with e.g. from __future__ import annotations
    if parent_name in list_core_modules():
        return parent_name

    # taken from importlib.util.find_spec
    if fqname in sys.modules:
        module = sys.modules[fqname]
        if module is None:
            return None
        try:
            spec = module.__spec__
        except AttributeError:
            raise ValueError("{}.__spec__ is not set".format(fqname)) from None
        else:
            if spec is None:
                raise ValueError("{}.__spec__ is None".format(fqname))
            return fqname

    spec = importlib.util.find_spec(head)
    if not spec:
        raise ModuleNotFoundError(f"could not find the module {head} to resolve {fqname}", name=head)

    has_no_submodules = (
        not hasattr(spec, "submodule_search_locations") or spec.submodule_search_locations is None
    )
    if len(parts) == 2 and has_no_submodules:
        # we have from a import b with a being a.py, is that possible:
        # a package without directories, just one file? I assume yes for now
        return head

    if has_no_submodules:
        raise ModuleNotFoundError(f"could not find the module {head} to resolve {fqname}", name=head)

    for base_path in spec.submodule_search_locations:
        init = os.path.join(base_path, *(parts[1:] + ["__init__.py"]))
        dir = os.path.join(base_path, *parts[1:])
        direct = os.path.join(base_path, *parts[1:]) + ".py"
        if os.path.exists(init) or os.path.exists(direct) or os.path.isdir(dir):
            # we have a module
            return fqname
    # we imported an object, return "parent"
    return parent_name
