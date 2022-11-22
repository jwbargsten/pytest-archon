from py3arch.collect import collect_modules, collect_from_pkg, path_to_module
import py3arch
from pathlib import Path


def test_collect_modules(create_testset):

    path = create_testset(("mymodule.py", ""))
    collected = list(name for name, _ in collect_modules(path))
    assert "mymodule" in collected


def test_collect_with_system_modules(create_testset):

    path = create_testset(("mymodule.py", "import sys, os"))

    name, imports = next(collect_modules(path))

    assert name == "mymodule"
    assert "sys" in imports
    assert "os" in imports


def test_path_to_module():
    assert path_to_module(Path("a/b/./c/d/../e"), Path("a/b/c")) == "d.e"


def test_module_imports_other_module(create_testset):

    path = create_testset(("module.py", ""), ("othermodule.py", "import module"))

    module_names = {i for name, imports in collect_modules(path) for i in imports}

    assert "module" in module_names
    assert "othermodule" not in module_names


def test_module_import_from(create_testset):

    path = create_testset(("module.py", "val = 1"), ("othermodule.py", "from module import val"))

    module_names = {i for name, imports in collect_modules(path) for i in imports}
    assert module_names == {"module"}


def test_module_import_nested_modules(create_testset):

    path = create_testset(
        ("package/__init__.py", ""), ("package/module.py", ""), ("othermodule.py", "import package.module")
    )

    module_names = {i for name, imports in collect_modules(path) for i in imports}

    assert "package.module" in module_names
    assert "othermodule" not in module_names


def test_relative_imports(create_testset):

    path = create_testset(
        ("package/__init__.py", ""),
        ("package/module.py", "from .importme import val"),
        ("package/importme.py", "val = 1"),
        ("package/sub/__init__.py", ""),
        ("package/sub/deep.py", "from ..importme import val"),
    )

    print(list(collect_modules(path)))
    module_names = {i for name, imports in collect_modules(path) for i in imports}

    assert "package.importme" in module_names


def test_collect_pkg():
    data = collect_from_pkg(py3arch)
    assert "py3arch.import_finder" in data["py3arch"]["transitive"]
