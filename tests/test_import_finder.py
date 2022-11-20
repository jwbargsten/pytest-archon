import ast
import importlib
import sys
from py3arch.import_finder import walk_ast, find_module
from importlib.util import find_spec

# def find_module(self, name, path, parent=None):
#     if parent is not None:
#         # assert path is not None
#         fullname = parent.__name__ + "." + name
#     else:
#         fullname = name
#     if fullname in self.excludes:
#         self.msgout(3, "find_module -> Excluded", fullname)
#         raise ImportError(name)
#
#     if path is None:
#         if name in sys.builtin_module_names:
#             return (None, None, ("", "", _C_BUILTIN))
#
#         path = self.path
#
#     return _find_module(name, path)



def test_find():
    pass



def test_ast_walk():
    # subpkg1/subpkg1a/__init__.py
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
    imports = walk_ast(tree, package="pkgA.subpkg1.subpkg1a")
    for imp in imports:
        print(imp)
    # print(find_module(imp, ["/Users/jwb/entwicklung/py3arch/tests/data"] + sys.path))

# from .module import h
# from .moduleY import spam
# from .moduleY import spam as ham
# from . import moduleY
# from ..subpackage1 import moduleY
# from ..subpackage2.moduleZ import eggs
# from ..moduleA import foo
