from pathlib import Path

from pytest_archon.collect import (
    collect_imports_from_path,
    path_to_module,
    recurse_imports,
    resolve_module_or_object_by_path,
    resolve_module_or_object_by_spec,
)


def test_collect_modules(create_testset):
    path = create_testset(("mymodule.py", ""))
    collected = list(name for name, _ in collect_imports_from_path(path, "pkg"))
    assert "pkg.mymodule" in collected


def test_collect_with_system_modules(create_testset):
    path = create_testset(("mymodule.py", "import sys, os"))

    name, imports = next(iter(collect_imports_from_path(path, "pkg")))

    assert name == "pkg.mymodule"
    assert "sys" in imports
    assert "os" in imports


def test_path_to_module():
    assert path_to_module(Path("a/b/./c/d/../e"), Path("a/b/c")) == "d.e"


def test_module_imports_other_module(create_testset):
    path = create_testset(("module.py", ""), ("othermodule.py", "import module"))

    module_names = {i for name, imports in collect_imports_from_path(path, "pkg") for i in imports}

    assert "module" in module_names
    assert "othermodule" not in module_names


def test_module_import_from(create_testset):
    path = create_testset(("module.py", "val = 1"), ("othermodule.py", "from module import val"))

    module_names = {i for name, imports in collect_imports_from_path(path, "pkg") for i in imports}
    assert module_names == {"module"}


def test_module_import_nested_modules(create_testset):
    path = create_testset(
        ("package/__init__.py", ""),
        ("package/module.py", ""),
        ("package/othermodule.py", "import package.module"),
    )

    module_names = {i for name, imports in collect_imports_from_path(path, "package") for i in imports}

    assert "package.module" in module_names
    assert "package.othermodule" not in module_names
    assert "othermodule" not in module_names


def test_relative_imports(create_testset):
    path = create_testset(
        ("package/__init__.py", ""),
        ("package/module.py", "from .importme import val"),
        ("package/importme.py", "val = 1"),
        ("package/sub/__init__.py", ""),
        ("package/sub/deep.py", "from ..importme import val"),
    )

    module_names = {
        i for name, imports in collect_imports_from_path(path / "package", "package") for i in imports
    }

    assert "package.importme" in module_names


def test_namespace_pkgs(create_testset):
    create_testset(
        ("package/__init__.py", ""),
        ("package/initless/module.py", "A=3"),
    )

    res = resolve_module_or_object_by_path("package.initless.module.A")
    assert res == "package.initless.module"


def test_resolve_module_or_object_by_spec():
    res = resolve_module_or_object_by_spec("fnmatch.fnmatch")
    assert res == "fnmatch"


def test_resolve_module_or_object_by_path():
    res = resolve_module_or_object_by_path("fnmatch.fnmatch")
    assert res == "fnmatch"


def test_recurse_imports():
    all_imports = {"a": ["b", "c"], "b": ["c", "d"], "c": ["e"]}
    res = list(recurse_imports("a", all_imports))

    assert res == [("a", "b"), ("a", "b", "c"), ("a", "b", "c", "e"), ("a", "b", "d"), ("a", "c")]
