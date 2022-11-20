import pytest

from py3arch.collect import module_map
from py3arch.config import read_rules
from py3arch.rule import ALLOWED, DENIED, UNDECIDED, lhs_matches, rhs_matches, rule


def test_module_imports_other_module(create_testset):

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

    rules = read_rules(path / "pyproject.toml")
    mapping = module_map(path)
    voilations = [voilation for module, imported in mapping if (voilation := rule(rules, module, imported))]

    assert rules
    assert mapping
    assert not voilations


def test_module_fails_imports_other_module(create_testset):

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

    rules = read_rules(path / "pyproject.toml")
    mapping = module_map(path)
    voilations = [voilation for module, imported in mapping if (voilation := rule(rules, module, imported))]

    assert rules
    assert mapping
    assert voilations


def test_allow_rules():
    assert not rule({"module": "othermodule"}, "module", "othermodule")
    assert not rule({"module": "othermodule"}, "module", "thirdparty")


def test_deny_rules():
    assert rule({"module": "not othermodule"}, "module", "othermodule")
    assert not rule({"module": "not othermodule"}, "module", "thirdparty")
    assert not rule({"not othermodule": "not othermodule"}, "module", "thirdparty")


def test_only_rules():
    assert not rule({"module": "only othermodule"}, "module", "othermodule")
    assert rule({"module": "only othermodule"}, "module", "thirdparty")
    assert not rule({"module": "only othermodule,extra"}, "module", "othermodule")
    assert not rule({"module": "only extra,othermodule"}, "module", "othermodule")


def test_wildcard_rule():
    assert not rule({"mo*": "only other*"}, "module", "othermodule")
    assert rule({"mo*": "only other*"}, "module", "thirdparty")


def test_lhs_matches():
    assert not lhs_matches("os.path", "mismatch")
    assert lhs_matches("os.path", "os.path")
    assert lhs_matches("os.path", "os")
    assert not lhs_matches("os.path", "not os.path")
    assert not lhs_matches("os.path", "not os")
    with pytest.raises(ValueError):
        lhs_matches("os.path", "foo bar")


def test_rhs_matches():
    assert rhs_matches("os.path", "mismatch") is UNDECIDED
    assert rhs_matches("os.path", "os.path") is ALLOWED
    assert rhs_matches("os.path", "os") is ALLOWED
    assert rhs_matches("os.path", "not os.path") is DENIED
    assert rhs_matches("os.path", "not os") is DENIED
    assert rhs_matches("os.path", "only os") is ALLOWED
    assert rhs_matches("os.path", "only os.path") is ALLOWED
    assert rhs_matches("os.path", "only sys") is DENIED

    with pytest.raises(ValueError):
        rhs_matches("os.path", "foo bar")
