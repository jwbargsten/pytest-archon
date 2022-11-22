import ast
from textwrap import dedent

from py3arch.collect import extract_imports_ast


def test_parse():
    code = dedent(
        """\
        import sys
        from os import path
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(extract_imports_ast(root, ""))

    # Should this be os.path?
    assert "os.path" in imports
    assert "sys" in imports


def test_parse_relative_imports(create_testset, monkeypatch):
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

    code = dedent(
        """\
        import datetime
        import pkgA
        import pkgA.subpkg1
        import pkgA.subpkg1.subpkg1a
        from pkgA import subpkg2
        from . import variableA, variableB
        from .. import moduleA
        from . import moduleX, moduleY
        from ..subpkg2.subpkg2a import moduleM
        from ..subpkg2.moduleZ import CONSTANT_A
        """
    )

    monkeypatch.syspath_prepend(path)
    root = ast.parse(code)
    imports = set(extract_imports_ast(root, "pkgA.subpkg1.subpkg1a"))

    assert imports == {
        "datetime",
        "pkgA",
        "pkgA.subpkg1",
        "pkgA.subpkg1.subpkg1a",
        "pkgA.subpkg2",
        "pkgA.moduleA",
        "pkgA.subpkg1.moduleX",
        "pkgA.subpkg1.moduleY",
        "pkgA.subpkg2.subpkg2a.moduleM",
        "pkgA.subpkg2.moduleZ",
    }
