# pytest-archon

[![build_and_test](https://github.com/jwbargsten/pytest-archon/actions/workflows/tests.yml/badge.svg)](https://github.com/jwbargsten/pytest-archon/actions/workflows/tests.yml)

`pytest-archon` is a little tool that helps you structure (large) Python projects. This
tool allows you to define architectural boundaries in your code, also known as
_forbidden dependencies_.

Explicitly defined architectural boundaries helps you keep your code in shape. It avoids
the creation of circular dependencies. New people on the project are made aware of the
structure through a simple set of rules, instead of lore.

## Installation

The simple way:

```sh
pip install pytest-archon
```

## Usage

_pytest-archon_ can be used to define architectural boundaries from (unit) tests.
Because they're tests, they can be closely tied to the actual application.

You can use _pytest-archon_ in tests by simply importing the `archrule` function. Using
this function you can construct import tests:

```python
from pytest_archon import archrule


def test_rule_basic():
    (
        archrule("name", comment="some comment")
        .match("pytest_archon.col*")
        .exclude("pytest_archon.colgate")
        .should_not_import("pytest_archon.import_finder")
        .should_import("pytest_archon.core*")
        .check("pytest_archon")
    )
```

- To match the modules and constraints,
  [fnmatch](https://docs.python.org/3/library/fnmatch.html) syntax is used (the
  default). You can also use
  [regular expressions](https://docs.python.org/3/library/re.html#regular-expression-syntax)
  by supplying the `use_regex=True` argument to `archrule()`. Example: `archrule(..., use_regex=True).match(...)`.
- `.exclude()` is optional
- `.should_import()` and `.should_not_import()` can be combined and can occur multiple
  times.
- `.may_import()` can be used in combination with `.should_not_import()`.
- `.check()` needs either a module object or a string

The `check()` method can have a few optional parameters, that alter the way the checks
are performed.

- Without parameters, the whole file is checked for imports. So imports done in
  functions and methods are also found. Transitive dependencies are also checked
- Option `only_toplevel_imports=True` will only check for toplevel imports. Conditional
  imports and import in functions and methods are ignored.
- `skip_type_checking=True` will check all imports, but skip imports defined in
  `if typing.TYPE_CHECKING` blocks.
- `only_direct_imports=True` will only check for imports performed by the module
  directly and will not check transitive imports.
- If `only_toplevel_imports=True` is set, `skip_type_checking=True` has no effect.
- Options can be combined.

|                              | Check toplevel imports | Check `TYPE_CHECKING` imports | Check conditional imports, and imports in functions and methods | Check transitive imports |
| ---------------------------- | :--------------------: | :---------------------------: | :-------------------------------------------------------------: | :----------------------: |
| no options enabled           |           ✓            |               ✓               |                                ✓                                |            ✓             |
| `skip_type_checking=True`    |           ✓            |               ✗               |                                ✓                                |            ✓             |
| `only_toplevel_imports=True` |           ✓            |               ✗               |                                ✗                                |            ✓             |
| `only_direct_imports=True`   |           ✓            |               ✓               |                                ✓                                |            ✗             |

## Example

```python
def test_domain():
    # test if the domain model does not import other submodules
    # (the domain model should be standing on its own and be used by other modules)
    (
        archrule("domain", comment="domain does not import any other submodules")
        .match("packageX.domain*") # matches packageX.domain and packageX.domain.*
        .should_not_import("packageX*")
        .may_import("packageX.domain.*")
        .check("packageX")
    )
```

## Similar projects

- [Archunit](https://www.archunit.org/) (Java)
- [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) (Javascript)
- [import-linter](https://github.com/seddonym/import-linter) (Python)
- [pytestarch](https://pypi.org/project/pytestarch/) (Python)
- [Maintain A Clean Architecture With Dependency Rules - sourcery.ai](https://sourcery.ai/blog/dependency-rules/)
  (Python)
