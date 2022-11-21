# Py3arch

_(pronounce: py-triarch)_

Py3arch is a little tool that helps you structure (large) Python projects.
This tool allows you to define architectural boundries in your code, also
known as _forbidden dependencies_.

## Installation

### As pre-commit hook

Add the following to your `.pre-commit-config.yaml`:

```yaml

```
## Usage

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


## Similar projects

* [Archunit](https://www.archunit.org/) (Java)
* [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) (Javascript)
* [import-linter](https://github.com/seddonym/import-linter) (Python)
