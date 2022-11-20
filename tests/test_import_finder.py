import ast
import sys
from py3arch.import_finder import walk_ast


def test_ast_walk():
    data = """
import datetime
import datetime.datetime
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
    imports = walk_ast(tree, package="pkgA.subpkg1.subpkg1a", package_path=sys.path + ["tests/data"])
    for imp in imports:
        print(imp)
