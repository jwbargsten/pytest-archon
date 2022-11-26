from __future__ import annotations

import ast
import os
import re
import sys
from collections import deque
from importlib.util import find_spec
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, Iterator, TypedDict

from pytest_archon.core_modules import core_modules

# https://docs.djangoproject.com/en/4.1/_modules/django/utils/module_loading/
# https://stackoverflow.com/questions/54325116/can-i-handle-imports-in-an-abstract-syntax-tree
# https://bugs.python.org/issue38721
# https://github.com/0cjs/sedoc/blob/master/lang/python/importers.md


Walker = Callable[[ast.Module], Iterator[ast.AST]]


class Imports(TypedDict, total=False):
    direct: set[str]
    transitive: set[str]
    is_circular: bool


ImportMap = Dict[
    str,
    Imports,
]


def collect_imports(package: str | ModuleType, walker: Walker) -> ImportMap:
    if isinstance(package, ModuleType):
        if not hasattr(package, "__path__"):
            raise AttributeError(f"module {package.__name__} does not have __path__")
        package = package.__name__

    all_imports: ImportMap = {}
    for name, imports in collect_imports_from_path(package_dir(package), package, walker):
        direct_imports = {imp for imp in imports if imp != name}
        if name in all_imports:
            raise KeyError(f"WTF? duplicate module {name}")
        all_imports[name] = {"direct": direct_imports}
    update_with_transitive_imports(all_imports)
    return all_imports


# from ast:
def walk(node: ast.AST, skip_type_checking=False) -> Iterator[ast.AST]:
    todo = deque([node])
    while todo:
        node = todo.popleft()
        # Skip TYPE_CHECKING markers. The check if pretty rudimentary:
        # it checks for if statements with either TYPE_CHECKING or <somemod>.TYPECHECKING in the expression.
        # TODO: should we make this configurable?
        if not (skip_type_checking and type_checking_clause(node)):
            todo.extend(ast.iter_child_nodes(node))
            yield node


def walk_toplevel(node: ast.Module) -> Iterator[ast.AST]:
    yield from node.body


def package_dir(package: str) -> Path:
    spec = find_spec(package)
    if not spec:
        raise ModuleNotFoundError(f"could not find the module {package!r}", name=package)

    assert spec.origin
    return Path(spec.origin).parent


def collect_imports_from_path(
    path: Path, package: str, walker: Walker = walk
) -> Iterator[tuple[str, set[str]]]:  # type: ignore[type-arg]
    for py_file in Path(path).glob("**/*.py"):
        module_name = path_to_module(py_file, path, package)
        tree = ast.parse(py_file.read_bytes())
        imports = extract_imports_ast(walker(tree), module_name)
        yield module_name, set(imports)


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


def extract_imports_ast(nodes: Iterator[ast.AST], package: str, resolve=True) -> Iterator[str]:
    for node in nodes:
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


def type_checking_clause(node: ast.AST) -> bool:
    return isinstance(node, ast.If) and (
        (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING")
        or (isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING")
    )


def update_with_transitive_imports(data: ImportMap) -> None:
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
def resolve_import_from(
    name: str, module: str | None = None, package: str | None = None, level: int = 0
) -> str:
    if not level:
        # absolute import
        if name == "*":
            assert module
            return module
        return name if module is None else f"{module}.{name}"

    # taken from importlib._bootstrap._resolve_name
    assert package
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
def resolve_module_or_object_by_spec(fqname: str) -> str:
    if fqname in core_modules():
        return fqname

    parent_name = fqname.rpartition(".")[0]

    # shortcut to deal with e.g. from __future__ import annotations
    if parent_name in core_modules():
        return parent_name

    spec = None
    try:
        spec = find_spec(fqname)
    except ModuleNotFoundError as ex:
        parent_spec = find_spec(parent_name)
        # if we cannot find the parent, then something is off
        if not parent_spec:
            raise ex

    return fqname if spec else fqname.rpartition(".")[0]


def resolve_module_or_object_by_path(fqname: str) -> str:
    if "." not in fqname:
        return fqname

    if fqname in core_modules():
        return fqname

    parts = fqname.split(".")
    head = parts[0]
    parent_name = ".".join(parts[:-1])

    # shortcut to deal with e.g. from __future__ import annotations
    if parent_name in core_modules():
        return parent_name

    # taken from importlib.util.find_spec
    if fqname in sys.modules:
        module = sys.modules[fqname]
        if module is None:
            return None
        try:
            spec = module.__spec__
        except AttributeError:
            raise ValueError(f"{fqname}.__spec__ is not set") from None
        else:
            if spec is None:
                raise ValueError(f"{fqname}.__spec__ is None")
            return fqname

    spec = find_spec(head)
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

    assert spec.submodule_search_locations
    for base_path in spec.submodule_search_locations:
        init = os.path.join(base_path, *(parts[1:] + ["__init__.py"]))
        dir = os.path.join(base_path, *parts[1:])
        direct = os.path.join(base_path, *parts[1:]) + ".py"
        if os.path.exists(init) or os.path.exists(direct) or os.path.isdir(dir):
            # we have a module
            return fqname
    # we imported an object, return "parent"
    return parent_name
