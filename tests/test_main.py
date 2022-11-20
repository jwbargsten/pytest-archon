from py3arch.__main__ import main


def test_module_imports_other_module(create_testset, capsys):

    path = create_testset(
        (
            "pyproject.toml",
            """\
            [tool.py3arch.rules]
            othermodule = [ "module" ]
            """,
        ),
        ("module.py", ""),
        ("othermodule.py", "import module"),
    )

    exitcode = main(["-d", str(path)])
    captured = capsys.readouterr()

    assert exitcode == 0
    assert captured.out == ""


def test_module_fails_imports_other_module(create_testset, capsys):

    path = create_testset(
        (
            "pyproject.toml",
            """\
            [tool.py3arch.rules]
            foobar = [ "sys" ]
            othermodule = [ "not module" ]
            """,
        ),
        ("module.py", ""),
        ("othermodule.py", "import module"),
    )

    exitcode = main(["-d", str(path)])
    captured = capsys.readouterr()

    assert exitcode == 1
    assert (
        captured.out == "Import 'module' is not allows in 'othermodule' (rule: 'othermodule => not module')\n"
    )
