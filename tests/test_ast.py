import ast
from textwrap import dedent

from pytest_archon.collect import extract_imports_ast, walk, walk_runtime, walk_toplevel


def test_parse_imports():
    code = dedent(
        """\
        import sys
        if True:
            from datetime import datetime
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(extract_imports_ast(walk(root), ""))

    assert "sys" in imports
    assert "datetime" in imports


def test_parse_toplevel_imports():
    code = dedent(
        """\
        import sys
        if 0:
            from datetime import datetime
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(
        extract_imports_ast(
            walk_toplevel(root),
            "",
        )
    )

    assert "sys" in imports
    assert "datetime" not in imports


def test_skip_type_checking_marker():
    code = dedent(
        """\
        import sys
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from datetime import datetime
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(extract_imports_ast(walk_runtime(root), ""))

    # Should this be os.path?
    assert "datetime" not in imports
    assert "sys" in imports


def test_skip_typing_dot_type_checking_marker():
    code = dedent(
        """\
        import sys
        import typing
        if typing.TYPE_CHECKING:
            from datetime import datetime
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(extract_imports_ast(walk_runtime(root), ""))

    # Should this be os.path?
    assert "datetime" not in imports
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
    imports = set(extract_imports_ast(walk(root), "pkgA.subpkg1.subpkg1a"))

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
