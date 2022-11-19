from textwrap import dedent

from py3arch.config import read_rules


def test_read_rules(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(dedent("""\
        [tool.py3arch.rules]
        package = [ "package.submodule", "not package.forbidden" ]
        """))

    raw_rules = read_rules(pyproject)

    assert "package" in raw_rules
    assert raw_rules["package"] == [ "package.submodule", "not package.forbidden" ]
    