import os
import sys
from importlib.machinery import PathFinder

# https://stackoverflow.com/questions/54325116/can-i-handle-imports-in-an-abstract-syntax-tree
# https://bugs.python.org/issue38721
# https://github.com/0cjs/sedoc/blob/master/lang/python/importers.md


def resolve_module_or_object(fqname, path=None):
    if path is None:
        path = sys.path
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

    PathFinder.invalidate_caches()

    if "." not in fqname:
        return fqname

    parts = fqname.split(".")
    head = parts[0]

    spec = PathFinder.find_spec(head, path)
    if not hasattr(spec, "submodule_search_locations") or spec.submodule_search_locations is None:
        # we imported an object, return "parent"
        return ".".join(parts[:-1])

    for base_path in spec.submodule_search_locations:
        init = os.path.join(base_path, *(parts[1:] + ["__init__.py"]))
        direct = os.path.join(base_path, *parts[1:]) + ".py"
        if os.path.exists(init) or os.path.exists(direct):
            # we have a module
            return fqname
    # we imported an object, return "parent"
    return ".".join(parts[:-1])


def resolve_import_from(name, module=None, package=None, level=None):
    if not level:
        # absolute import
        return name if module is None else f"{module}.{name}"

    # taken from importlib._bootstrap._resolve_name
    bits = package.rsplit(".", level)
    if len(bits) < level:
        raise ImportError("attempted relative import beyond top-level package")
    base = bits[0]

    # relative import
    if module is None:
        # from . import moduleX
        return f"{base}.{name}"
    else:
        # from .moduleZ import moduleX
        return f"{base}.{module}.{name}"


def explode_import(fqname):
    parts = fqname.split(".")
    if len(parts) <= 1:
        return [fqname]

    acc = [parts[0]]
    for p in parts[1:]:
        acc.append(".".join([acc[-1], p]))
    return acc
