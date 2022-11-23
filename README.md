# pytest-arch

[![build_and_test](https://github.com/jwbargsten/pytest-arch/actions/workflows/tests.yml/badge.svg)](https://github.com/jwbargsten/pytest-arch/actions/workflows/tests.yml)

`pytest-arch` is a little tool that helps you structure (large) Python projects.
This tool allows you to define architectural boundries in your code, also
known as _forbidden dependencies_.

Explicitly defined architectural boundaries help you keep your code in shape.
It avoids the creation of circular dependencies. New people on the project
are made aware of the structure through a simple set of rules, instead of lore.

## Installation


The simple way:

```sh
pip install git+https://github.com/jwbargsten/pytest-arch.git
```

## Usage

`pytest-arch` can be used to define architectural boundaries from (unit) tests. Because they're unit tests,
they can be closely tied to the actual application. 

You can use `pytest-arch` in tests by simply importing the `rule` function. Using this
function you can construct import tests:

```
from pytest_arch.plugin import rule


def test_rule_basic():
    (
        rule("name", comment="some comment")
        .match("pytest_arch.col*")
        .exclude("pytest_arch.colgate")
        .should_not_import("pytest_arch.import_finder")
        .should_import("pytest_arch.core*")
        .check("pytest_arch", path=["/path/to/base/dir"])
    )
```

- To match the modules and constraints,
  [fnmatch](https://docs.python.org/3/library/fnmatch.html) syntax is used.
- `.exclude()` is optional
- `.should_import()` and `.should_not_import()` can be combined and can occur multiple
  times.
- `.check()` needs either a module object or a string; `path` can be skipped and will be
  derived from the module path.
- `comment=` is currently not used, but might be in the future



## Similar projects

* [Archunit](https://www.archunit.org/) (Java)
* [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) (Javascript)
* [import-linter](https://github.com/seddonym/import-linter) (Python)
