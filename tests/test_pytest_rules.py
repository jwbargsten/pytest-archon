from types import ModuleType
from py3arch.import_finder import find_spec
import sys


class Rule:
    def __init__(self, name, comment, package=None, path=None):
        self.name = name
        self.comment = comment
        self.package = package
        self.path = path

    def root(self, package, path=None):
        if isinstance(package, ModuleType):
            if not hasattr(package, "__path__"):
                raise AttributeError("module {name} does not have __path__".format(name=package.__name__))
            self.path = package.__path__
            self.package = package.__name__
        elif isinstance(package, str):
            spec = find_spec(package, path=path, with_sys_modules=False)
            if not spec or spec.submodule_search_locations is None:
                raise ModuleNotFoundError("error")
            print(spec)
            self.path = spec.submodule_search_locations
            self.package = package
        # package can be module object
        # package can be string with path set ->
        # package can be string -> use find_spec to figure out path
        self.package = package
        return self

    def for_module(self):
        return RuleFrom()

    def without_module(self):
        return RuleFrom()

def rule(name, comment=None):
    return Rule(name, comment=comment)

class RuleFrom:
    def for_module(self):
        # update self
        return self

    def without_module(self):
        # update self
        return self


class RuleTo:
    pass


def test_rules2():
    x = rule("abc", "def").root("py3arch")
    print(vars(x))
    x = rule("abc", "def").root("py3arch", path=["."])
    print(vars(x))


def test_rules():
    pass
    # (
    #     rule("always import py3arch", comment="because I want it")
    #     .for_module(r".*")
    #     .without_module("special.module")
    #     .should_import("py3arch")
    # )

    # (
    #     rule("never import py3arch", comment="because I want it")
    #     .for_module(r".*")
    #     .should_not_import("py3arch")
    # )
    # api rule: only one module, the api, can be imported. submodules not
