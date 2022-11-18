from glob import iglob
from modulefinder import ModuleFinder

from textwrap import dedent

import pytest

from py3arch.collect import collect_modules


@pytest.fixture
def create_testset(tmp_path):
    def _create_testset(*module_contents):
        for module, contents in module_contents:
            mod_path = (tmp_path / module)
            mod_path.parent.mkdir(parents=True, exist_ok=True)
            mod_path.write_text(dedent(contents))
        return tmp_path

    return _create_testset


def xtest_collect_modules(create_testset):

    path = create_testset(("mymodule.py", ""))

    collected = list(collect_modules(path))

    assert "mymodule.py" in collected


def test_module_imports_other_module(create_testset):

    path = create_testset(
        ("module.py", "import othermodule"),
        ("othermodule.py", "import module")
    )

    module_names = [m.__name__ for name, path, modules in collect_modules(path) for m in modules]

    assert "module" in module_names
    assert "othermodule" in module_names

