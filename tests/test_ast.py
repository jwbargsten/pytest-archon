import ast
from textwrap import dedent
from typing import Iterable


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


def find_imports(root, current_module) -> Iterable[str]:
    for node in ast.walk(root):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                assert node.module
                yield from (f"{node.module}.{alias.name}" for alias in node.names)
            else:
                yield from (
                    f"{relative(current_module, node.module, node.level)}.{alias.name}"
                    for alias in node.names
                )


def relative(current_module, module, level):
    parent = current_module.rsplit(".", level)[0]
    return f"{parent}.{module}" if module else parent
