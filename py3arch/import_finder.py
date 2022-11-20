import ast
import sys
import importlib
import os


def find_module(name, path=None):
    importlib.machinery.PathFinder.invalidate_caches()
    spec = importlib.machinery.PathFinder.find_spec(name, path)

    if spec is None:
        raise ImportError("No module named {name!r}".format(name=name), name=name)

    return spec


def resolve_module_or_object(fqname, path=None):
    if not fqname.count("."):
        return fqname
    bits = fqname.split(".")
    parent_name = bits[0]

    spec = find_module(parent_name, path)
    file_path = spec.origin

    base_path = os.path.dirname(file_path)
    init = os.path.join(base_path, *(bits[1:] + ["__init__.py"]))
    direct = os.path.join(base_path, *bits[1:]) + ".py"
    if os.path.exists(init) or os.path.exists(direct):
        # we have a module
        return fqname
    else:
        # we imported an object, return "parent"
        return ".".join(bits[:-1])


def resolve_import_from(name, module=None, package=None, level=None):
    if not level:
        # absolute import
        return name if module is None else "{}.{}".format(module, name)

    # taken from importlib._bootstrap._resolve_name
    bits = package.rsplit(".", level - 1)
    if len(bits) < level:
        raise ImportError("attempted relative import beyond top-level package")
    base = bits[0]

    # relative import
    if module is None:
        # from . import moduleX
        return "{}.{}".format(base, name)
    else:
        # from .moduleZ import moduleX
        return "{}.{}.{}".format(base, module, name)


def walk_ast(tree, package=None, package_path=None):
    modules = []
    if package_path is None:
        package_path = sys.path
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend([a.name for a in node.names])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                fqname = resolve_import_from(alias.name, node.module, package=package, level=node.level)
                # TODO(jwbargsten): check for builtins
                fqname = resolve_module_or_object(fqname, path=package_path)
                modules.append(fqname)
    return modules
