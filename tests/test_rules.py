from py3arch.collect import collect_modules
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


def module_map(base_path):
    for name, path, modules in collect_modules(base_path):
        for m in modules:
            yield (".".join(name), m.__name__)
