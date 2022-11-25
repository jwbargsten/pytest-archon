# pytest-arch

[![build_and_test](https://github.com/jwbargsten/pytest-arch/actions/workflows/tests.yml/badge.svg)](https://github.com/jwbargsten/pytest-arch/actions/workflows/tests.yml)

`pytest-arch` is a little tool that helps you structure (large) Python projects.
This tool allows you to define architectural boundries in your code, also
known as _forbidden dependencies_.

Explicitly defined architectural boundaries helps you keep your code in shape.
It avoids the creation of circular dependencies. New people on the project
are made aware of the structure through a simple set of rules, instead of lore.

## Installation

The simple way:

```sh
pip install git+https://github.com/jwbargsten/pytest-arch.git
```

## Usage

`pytest-arch` can be used to define architectural boundaries from (unit) tests.
Because they're unit tests, they can be closely tied to the actual application. 

You can use `pytest-arch` in tests by simply importing the `archrule` function.
Using this function you can construct import tests:

```python
from pytest_arch import archrule


def test_rule_basic():
    (
        archrule("name", comment="some comment")
        .match("pytest_arch.col*")
        .exclude("pytest_arch.colgate")
        .should_not_import("pytest_arch.import_finder")
        .should_import("pytest_arch.core*")
        .check("pytest_arch")
    )
```

- To match the modules and constraints,
  [fnmatch](https://docs.python.org/3/library/fnmatch.html) syntax is used.
- `.exclude()` is optional
- `.should_import()` and `.should_not_import()` can be combined and can occur multiple
  times.
- `.check()` needs either a module object or a string


## Examples

```python
def test_module_boundaries():
    # you can do:
    # from packageX.moduleA import functionX
    # you cannot do
    # from packageX.moduleA.internal.functionY
    # so packageX/moduleA/__init__.py contains the exposed API functions,
    # and only they can be used
    modules = [
        "moduleA",
        "moduleB",
    ]
    for m in modules:
        (
            archrule(
                "respect module boundaries",
                comment="respect the module boundary and only import from the (sub-)module API",
            )
            .match("*")
            .exclude(f"packageX.{m}.*")
            .exclude(f"packageX.{m}")
            .should_not_import(f"packageX.{m}.*")
            .check("packageX", only_direct_imports=True)
        )


def test_domain():
    # test if the domain model does not import other submodules
    # (the domain model should be standing on its own and be used by other modules)
    (
        archrule("domain", comment="domain does not import any other submodules")
        .match("packageX.domain.*")
        .match("packageX.domain")
        .should_not_import("packageX*")
        .may_import("packageX.domain.*")
        .check("packageX")
    )
```


## Similar projects

* [Archunit](https://www.archunit.org/) (Java)
* [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) (Javascript)
* [import-linter](https://github.com/seddonym/import-linter) (Python)
