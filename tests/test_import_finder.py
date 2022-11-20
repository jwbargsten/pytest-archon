import ast
import sys
from py3arch.import_finder import walk_ast, explode_import


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
