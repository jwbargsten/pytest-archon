from py3arch.__main__ import main
import re


def test_module_imports_other_module(create_testset, capsys):

    path = create_testset(
        (
            "pyproject.toml",
            """\
            [tool.py3arch.rules]
            "abcz.othermodule" = [ "abcz.module" ]
            """,
        ),
        ("abcz/module.py", ""),
        ("abcz/othermodule.py", "import abcz.module"),
    )

    exitcode = main(["-d", str(path), "abcz"])
    captured = capsys.readouterr()

    assert exitcode == 0
    assert captured.out == ""


def test_module_fails_imports_other_module(create_testset, capsys):

    path = create_testset(
        (
            "pyproject.toml",
            """\
            [tool.py3arch.options]
            package = "abcz"
            [tool.py3arch.rules]
            foobar = [ "sys" ]
            "abcz.othermodule" = [ "not abcz.module" ]
            """,
        ),
        ("abcz/module.py", ""),
        ("abcz/othermodule.py", "import abcz.module"),
    )

    exitcode = main(["-d", str(path)])
    captured = capsys.readouterr()

    assert exitcode == 1
    assert re.search(r"abcz.module.* forbidden .*abcz.othermodule", captured.out)
