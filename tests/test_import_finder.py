import sys
import ast
from py3arch.import_finder import explode_import, resolve_module_or_object, resolve_import_from


def walk_ast(tree, package=None, path=None):
    modules = []
    if path is None:
        path = sys.path
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend([a.name for a in node.names])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                fqname = resolve_import_from(alias.name, node.module, package=package, level=node.level)
                fqname = resolve_module_or_object(fqname, path=path)
                modules.append(fqname)
    return modules


def test_namespace_pkgs(create_testset):
    path = create_testset(
        ("package/__init__.py", ""),
        ("package/initless/module.py", "A=3"),
    )
    res = resolve_module_or_object("package.initless.module.A", path=[str(path)])
    assert res == "package.initless.module"


def test_ast_walk(create_testset):
    path = create_testset(
        ("pkgA/subpkg2/moduleZ.py", ""),
        ("pkgA/subpkg2/__init__.py", ""),
        ("pkgA/subpkg2/subpkg2a/moduleM.py", ""),
        ("pkgA/subpkg2/subpkg2a/__init__.py", ""),
        ("pkgA/__init__.py", ""),
        ("pkgA/moduleA.py", ""),
        ("pkgA/subpkg1/__init__.py", ""),
        ("pkgA/subpkg1/moduleY.py", ""),
        ("pkgA/subpkg1/subpkg1a/moduleL.py", ""),
        ("pkgA/subpkg1/subpkg1a/__init__.py", ""),
        ("pkgA/subpkg1/subpkg1a/moduleK.py", ""),
        ("pkgA/subpkg1/moduleX.py", ""),
    )
    data = """
import datetime
import pkgA
import pkgA.subpkg1
import pkgA.subpkg1.subpkg1a
from pkgA import subpkg1
from . import moduleK, moduleL
from os import *
from .. import *
from .. import moduleX, moduleY
from ..subpkg2.subpkg2a import moduleM
from ..subpkg2.moduleZ import CONSTANT_A
"""
    tree = ast.parse(data)
    imports = walk_ast(tree, package="pkgA.subpkg1.subpkg1a", path=[str(path)] + sys.path)
    for imp in imports:
        print(imp)


def test_explode_import():
    assert explode_import("a.b.c") == ["a", "a.b", "a.b.c"]
    assert explode_import("a") == ["a"]


def test_resolve_module_or_object():
    res = resolve_module_or_object("fnmatch.fnmatch")
    assert res == "fnmatch"
