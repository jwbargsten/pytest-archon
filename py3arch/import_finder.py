import os
import sys
from importlib.machinery import PathFinder
import importlib

# https://stackoverflow.com/questions/54325116/can-i-handle-imports-in-an-abstract-syntax-tree
# https://bugs.python.org/issue38721
# https://github.com/0cjs/sedoc/blob/master/lang/python/importers.md


def find_spec(fqname, path=None, with_sys_modules=True):
    # taken from importlib.util.find_spec
    if with_sys_modules and fqname in sys.modules:
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
            return spec

    PathFinder.invalidate_caches()

    if "." not in fqname:
        return PathFinder.find_spec(fqname, path)

    parts = fqname.split(".")
    while parts:
        head = parts[0]
        parts = parts[1:]
        spec = PathFinder.find_spec(head, path)
        if spec is None:
            # if we cannot find the last part the "c" of "a.b.c"
            # then we might try to import an object
            # but if we already cannot find the spec for "a.b", then
            # something is off
            if len(parts) > 1:
                raise ImportError("No module named {name!r}".format(name=head), name=head)
            else:
                return None
        if parts and (
            not hasattr(spec, "submodule_search_locations") or spec.submodule_search_locations is None
        ):
            # we imported an object, return "parent"
            return None
        path = spec.submodule_search_locations
    return spec


def resolve_module_or_object(fqname, path=None):
    if path is None:
        path = sys.path
    spec = find_spec(fqname, path)
    return fqname if spec else fqname.rpartition(".")[0]


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


def explode_import(fqname):
    parts = fqname.split(".")
    if len(parts) <= 1:
        return [fqname]

    acc = [parts[0]]
    for p in parts[1:]:
        acc.append(".".join([acc[-1], p]))
    return acc
