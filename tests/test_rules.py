from py3arch.collect import module_map
from py3arch.config import read_rules
from py3arch.rule import rule


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


def test_module_imports_other_module(create_testset):

    path = create_testset(
        (
            "pyproject.toml",
            """\
            [tool.py3arch.rules]
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


def test_only_rules():
    assert not rule({"module": "only othermodule"}, "module", "othermodule")
    assert rule({"module": "only othermodule"}, "module", "thirdparty")
    assert not rule({"module": "only othermodule,extra"}, "module", "othermodule")
    assert not rule({"module": "only extra,othermodule"}, "module", "othermodule")


def test_wildcard_rule():
    assert not rule({"mo*": "only other*"}, "module", "othermodule")
    assert rule({"mo*": "only other*"}, "module", "thirdparty")
