import ast
from textwrap import dedent

from py3arch.collect import find_imports


def test_parse():
    code = dedent(
        """\
        import sys
        from os import path
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(find_imports(root, ""))

    # Should this be os.path?
    assert "os.path" in imports
    assert "sys" in imports


def test_parse_relative_imports():
    code = dedent(
        """\
        from . import sibling
        from .. import uncle
        from ..foo import nephew
        """
    )

    root = ast.parse(code, "test_parse.py")
    imports = list(find_imports(root, "family.tree.me"))

    print(ast.dump(root))

    assert "family.tree.sibling" in imports
    assert "family.uncle" in imports
    assert "family.foo.nephew" in imports
