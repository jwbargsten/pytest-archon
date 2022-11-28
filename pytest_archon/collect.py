from __future__ import annotations

import ast
import os
import re
import sys
from collections import deque
from importlib.util import find_spec
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, Iterator, TypedDict, Tuple

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


class ImportCollector:
    _cache: Dict[str, set[str]] = {}
    _transitive_cache: Dict[str, Tuple[set[str], bool]] = {}
    _use_cache = True

    @classmethod
    def disable_cache(cls):
        cls._use_cache = False

    @classmethod
    def enable_cache(cls):
        cls._use_cache = True

    @classmethod
    def invalidate_caches(cls):
        cls._cache = {}
        cls._transitive_cache = {}

    @classmethod
    def collect_imports(cls, package: str | ModuleType, walker: Walker) -> ImportMap:
        if isinstance(package, ModuleType):
            if not hasattr(package, "__path__"):
                raise AttributeError(f"module {package.__name__} does not have __path__")
            package = package.__name__

        all_imports: ImportMap = {}
        for name, imports in cls.collect_imports_from_path(package_dir(package), package, walker):
            direct_imports = {imp for imp in imports if imp != name}
            if name in all_imports:
                raise KeyError(f"WTF? duplicate module {name}")
            all_imports[name] = {"direct": direct_imports}
        ImportCollector.update_with_transitive_imports(all_imports)
        return all_imports

    @classmethod
    def collect_imports_from_path(
        cls, path: Path, package: str, walker: Walker = walk
    ) -> Iterator[tuple[str, set[str]]]:  # type: ignore[type-arg]
        for py_file in Path(path).glob("**/*.py"):
            module_name = path_to_module(py_file, path, package)
            if cls._use_cache and module_name in cls._cache:
                yield module_name, cls._cache[module_name]
                continue
            tree = ast.parse(py_file.read_bytes())
            imports = set(extract_imports_ast(walker(tree), module_name))
            cls._cache[module_name] = imports
            yield module_name, imports

    # https://algowiki-project.org/en/Transitive_closure_of_a_directed_graph#Algorithms_for_solving_the_problem
    @classmethod
    def update_entry_with_transitive_imports(cls, initial_name, data):
        initial_imports = data[initial_name].get("direct", set())
        seen = {}

        # we start with the module "initial_name". Our goal is to get its transitive imports. So we take
        # the direct imports and do a depth-first-search (DFS) till we collected all transitive imports.
        #
        # Along the way we also visit other modules. While visiting them we can collect their
        # transitive dependencies, too. The "collected transitive dependencies so-far" are in
        # "trans_of_modules_visited".

        # For DFS we use a stack (only push and pop are allowed with the "head" at the end). How can we
        # figure out when we collected all transitive dependencies of a visited module?
        # Here we use a marker entry in the stack. An example stack looks like this:
        #
        # (None, m1) <- marker entry. If we reach this entry, we know that all dependencies of
        #               m1 are processed and we can set the transitive entries for m1
        # (m1, m2)   <- normal entry. The left (m1 in this case) is the
        #               originating module, the right is the dependency
        # (m1, m3)
        # ...

        # init stack and transitive collection for
        # the starting module (the stack already starts on lvl deeper)
        stack = [(None, initial_name)]
        stack.extend([(initial_name, imp) for imp in initial_imports])
        trans_of_modules_visited = {initial_name: [set(), False]}

        while stack:
            head = stack[-1]
            name, imp = head
            stack = stack[:-1]
            if name is None:
                # we reached a "end" marker
                transitive, is_circular = trans_of_modules_visited.pop(imp, [set(), False])
                if cls._use_cache:
                    cls._transitive_cache[imp] = (transitive, is_circular)
                if imp in data:
                    data[imp]["transitive"] = transitive - data[imp]["direct"]
                    data[imp]["is_circular"] = is_circular
                continue

            stack.append((None, imp))
            for v in trans_of_modules_visited.values():
                v[0].add(imp)

            if head in seen:
                for v in trans_of_modules_visited.values():
                    v[1] = True
                continue
            seen[head] = True

            if imp not in trans_of_modules_visited:
                trans_of_modules_visited[imp] = [set(), False]

            # check the cache of the class
            # prehaps we find some transitive imports
            if cls._use_cache and imp in cls._transitive_cache:
                (transitive, is_circular) = cls._transitive_cache[imp]
                for v in trans_of_modules_visited.values():
                    v[0] |= transitive
                    v[1] = v[1] or is_circular
                continue
            # or perhaps the existing entries?
            elif imp in data and "transitive" in data[imp]:
                for v in trans_of_modules_visited.values():
                    v[0] |= data[imp]["transitive"]
                    v[0] |= data[imp]["direct"]
                    v[1] = v[1] or data[imp]["is_circular"]
                continue

            # ok, nothing found, dig deeper
            child = data.get(imp, None)
            if child is None:
                continue

            stack.extend([(imp, imp_child) for imp_child in child.get("direct", set())])

        for name, entry in data.items():
            if "transitive" not in entry:
                entry["transitive"] = set()
                entry["is_circular"] = False

    @classmethod
    def update_with_transitive_imports(cls, data: ImportMap) -> None:
        for name in data.keys():
            cls.update_entry_with_transitive_imports(name, data)


def walk_toplevel(node: ast.Module) -> Iterator[ast.AST]:
    yield from node.body


def package_dir(package: str) -> Path:
    spec = find_spec(package)
    if not spec:
        raise ModuleNotFoundError(f"could not find the module {package!r}", name=package)

    assert spec.origin
    return Path(spec.origin).parent


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
