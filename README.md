# Py3arch

_(pronounce: py-triarch)_

Py3arch is a little tool that helps you structure (large) Python projects.
This tool allows you to define architectural boundries in your code, also
known as _forbidden dependencies_.

Explicitly defined architectural boundaries help you keep your code in shape.
It avoids the creation of circular dependencies. New people on the project
are made aware of the structure through a simple set of rules, instead of lore.

## Installation


The simple way:

```sh
pip install git+https://github.com/jwbargsten/py3arch.git
```


### As pre-commit hook

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/jwbargsten/py3arch
    rev: main
    hooks:
      - id: py3arch
```

## Usage

Py3arch can be used in two different ways: with configuration defined in `pyproject.toml` and
through (test) code.

Both approaches have the own advantages and disadvantages. `pyproject.toml` based configuration
is relatively simple, but the configurability is limited. They can be executed as part of
a pre-commit hook.

Code based rules can be more flexible, especially for bigger, existing code bases. They are
written as tests.

### `pyproject.toml`

Add rules and configuration options to your `pyproject.toml`:

```toml
[tool.py3arch.options]
source = "py3arch"

[tool.py3arch.rules]
"py3arch.collect" = [ "not py3arch.rule" ]
```

In the above example, py3arch will examine the source files in the `py3arch` package.
The module `py3arch.collect` is not supposed to access the module `py3arch.rule`.

The left side of the expression (`py3arch.collect`) should adhere to the rules defined on the right.

The syntax is pretty simple:

* `module.submodule` to define a module is allowed
* `not module.submodule` to define a dependency is not allowed
* `only module` A module or package is only allowed to import from the module package, and its submodules.

Modules can be combined, by separating them with a comma: `module,othermodule`.

### Tests

We're figuring this out.

## Similar projects

* [Archunit](https://www.archunit.org/) (Java)
* [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) (Javascript)
<<<<<<< Updated upstream
=======
* [Import Linter](https://github.com/seddonym/import-linter) (Python)
>>>>>>> Stashed changes
