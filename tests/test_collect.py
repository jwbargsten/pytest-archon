import pytest

from py3arch.collect import collect_modules


def test_collect_modules(create_testset):

    path = create_testset(("mymodule.py", ""))

    collected = list(path.name for name, path, mod in collect_modules(path))

    assert "mymodule.py" in collected


def test_collect_with_system_modules(create_testset):

    path = create_testset(("mymodule.py", "import sys, os"))

    name, path, modules = next(collect_modules(path))
    modules = [m.__name__ for m in modules]

    assert name == ("mymodule",)
    assert "sys" in modules
    assert "os" in modules


def test_module_imports_other_module(create_testset):

    path = create_testset(("module.py", ""), ("othermodule.py", "import module"))

    module_names = {m.__name__ for name, path, modules in collect_modules(path) for m in modules}

    assert "module" in module_names
    assert "othermodule" not in module_names


def test_module_import_from(create_testset):

    path = create_testset(("module.py", "val = 1"), ("othermodule.py", "from module import val"))

    module_names = {m.__name__ for name, path, modules in collect_modules(path) for m in modules}

    assert "module" in module_names
    assert "othermodule" not in module_names


def test_module_import_nested_modules(create_testset):

    path = create_testset(
        ("package/__init__.py", ""), ("package/module.py", ""), ("othermodule.py", "import package.module")
    )

    module_names = {m.__name__ for name, path, modules in collect_modules(path) for m in modules}

    assert "package.module" in module_names
    assert "othermodule" not in module_names


@pytest.mark.xfail
def test_relative_imports(create_testset):

    path = create_testset(
        ("package/__init__.py", ""),
        ("package/module.py", "from .importme import val"),
        ("package/importme.py", "val = 1"),
        ("package/sub/__init__.py", ""),
        ("package/sub/deep.py", "from ..importme import val"),
    )

    print(list(collect_modules(path)))
    module_names = {m.__name__ for name, path, modules in collect_modules(path) for m in modules}

    assert "package.importme" in module_names
