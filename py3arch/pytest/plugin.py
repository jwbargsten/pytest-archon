import pytest
from pytest_check import check

import re
from types import ModuleType
from py3arch.import_finder import find_spec
from py3arch.collect import collect_from_pkg2

class Rule:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment

    def for_module(self, regex):
        return RuleFrom(self).for_module(regex)

    def without_module(self, regex):
        return RuleFrom(self).without_module(regex)


def rule(name, comment=None):
    return Rule(name, comment=comment)


class RuleFrom:
    def __init__(self, rule):
        self.rule = rule
        self.search = []
        self.no_search = []

    def for_module(self, regex):
        self.search.append(regex)
        return self

    def without_module(self, regex):
        # update self
        self.no_search.append(regex)
        return self

    def should_not_import(self, regex):
        return RuleTo(self.rule, self).should_not_import(regex)

    def should_import(self, regex):
        return RuleTo(self.rule, self).should_import(regex)


class RuleTo:
    def __init__(self, rule, rule_from):
        self.rule = rule
        self.rule_from = rule_from
        self.forbidden = []
        self.required = []

    def should_not_import(self, regex):
        self.forbidden.append(regex)
        return self

    def should_import(self, regex):
        self.required.append(regex)
        return self

    def check(self, package, path=None):
        if isinstance(package, ModuleType):
            if not hasattr(package, "__path__"):
                raise AttributeError("module {name} does not have __path__".format(name=package.__name__))
            path = package.__path__
            package = package.__name__
        elif isinstance(package, str):
            spec = find_spec(package, path=path, with_sys_modules=False)
            if not spec or spec.submodule_search_locations is None:
                raise ModuleNotFoundError("error", spec)
            path = spec.submodule_search_locations
            package = package
        res = collect_from_pkg2(path, package)

        candidates = []
        for s in self.rule_from.search:
            candidates.extend([k for k in res.keys() if re.search(s, k)])
        for s in self.rule_from.no_search:
            candidates = [k for k in candidates if not re.search(s, k)]

        for c in candidates:
            imports = res[c].get("direct", []) | res[c].get("transitive", [])
            for s in self.required:
                matches = [i for i in imports if re.search(s, i)]
                check.is_true(matches, f"module {c} did not import anything that matches /{s}/")
            for s in self.forbidden:
                matches = [i for i in imports if re.search(s, i)]
                check.is_false(matches, f"module {c} has forbidden imports {matches} (rule /{s}/)")



        # package can be module object
        # package can be string with path set ->
        # package can be string -> use find_spec to figure out path


@pytest.fixture(scope="session")
def py3arch_modules():
    return "abc"
