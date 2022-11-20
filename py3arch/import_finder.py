import ast
import sys
import importlib
import os


# from mdulefinder
def find_module(name, path=None):
    """An importlib reimplementation of imp.find_module (for our purposes)."""

    # It's necessary to clear the caches for our Finder first, in case any
    # modules are being added/deleted/modified at runtime. In particular,
    # test_modulefinder.py changes file tree contents in a cache-breaking way:

    importlib.machinery.PathFinder.invalidate_caches()

    # parent_name = name.rpartition('.')[0]
    # if parent_name:
    #     spec = find_module(parent_name, path)
    #     if spec is None:
    #         raise ImportError("No module named {name!r}".format(name=name), name=name)
    #     if not spec.submodule_search_locations:
    #         raise ImportError("No submodule search locations for {name!r}".format(name=name), name=name)
    #     print(spec)
    # else:
    spec = importlib.machinery.PathFinder.find_spec(name, path)

    if spec is None:
        raise ImportError("No module named {name!r}".format(name=name), name=name)

    return spec


# importlib._bootstrap._resolve_name
def _resolve_name(name, package, level):
    """Resolve a relative module name to an absolute one."""
    bits = package.rsplit('.', level - 1)
    if len(bits) < level:
        raise ImportError('attempted relative import beyond top-level package')
    base = bits[0]
    return '{}.{}'.format(base, name) if name else base


class FileProcessor:
    # importlib.import_module()
    pass


def build_ast(data):
    return ast.parse(data)


def resolve_import_from(name, module=None, package=None, level=None, path=None):
    fqname = resolve_import_from1(name, module, package, level, path)

    if not fqname.count("."):
        return fqname
    bits = fqname.split('.')
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

    #     finder = importlib.machinery.FileFinder(path=base_path)
    #     spec = finder.find_spec(fqname)
    #     if spec is None:
    #         newname = fqname.rpartition('.')[0]
    #         spec = finder.find_spec(newname)
    #         if spec is None:
    #             raise ImportError("No module named {name!r}".format(name=fqname), name=fqname)
    #         return newname
    # return fqname


def resolve_import_from1(name, module=None, package=None, level=None, path=None):
    if path is None:
        path = sys.path
    if not level:
        # absolute import
        return name if module is None else "{}.{}".format(module, name)

    # taken from importlib._bootstrap._resolve_name
    bits = package.rsplit('.', level - 1)
    if len(bits) < level:
        raise ImportError('attempted relative import beyond top-level package')
    base = bits[0]

    # relative import
    if module is None:
        # from . import moduleX
        return "{}.{}".format(base, name)
    else:
        # from .moduleZ import moduleX
        return "{}.{}.{}".format(base, module, name)


# from . import moduleX
# if module is None:

# import .moduleX
# if module is not None:


# if module is None:
# relative import
# raise ModuleNotFoundError("no module name supplied, cannot resolve relative imports")
# if not level:
#     return ".".join([module_name, name])

def walk_ast(tree, package=None):
    importsx = []
    path = "/Users/jwb/entwicklung/py3arch/tests/data"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            importsx.extend([a.name for a in node.names])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = resolve_import_from(alias.name, node.module, package=package, level=node.level,
                    path=sys.path + [path])
                importsx.append(name)
    return importsx
