import pytest
from pathlib import Path
from pytest_check import check

import re
from types import ModuleType
from py3arch.import_finder import find_spec
from py3arch.collect import collect_modules,update_with_transitive_imports
from py3arch.core_modules import list_core_modules

# the path is the package path: where the submodules are in
def _resolve_package(package, path=None):
    if isinstance(package, ModuleType):
        if not hasattr(package, "__path__"):
            raise AttributeError("module {name} does not have __path__".format(name=package.__name__))
        path = package.__path__
        package = package.__name__
    elif path:
        package = package
        path = path
    else:
        spec = find_spec(package, path=path, with_sys_modules=False)
        if not spec or spec.submodule_search_locations is None:
            raise ModuleNotFoundError("error", spec)
        path = spec.submodule_search_locations
        package = package
    return (package, path)

def _collect_imports(path, package):
    core_modules = list_core_modules()
    all_imports = {}
    for path in [Path(p) for p in path]:
        for name, imports in collect_modules(path.parent, package):
            direct_imports = {i for i in imports if i != name and i not in core_modules}
            if name in all_imports:
                raise KeyError("WTF? duplicate module {}".format(name))
            all_imports[name] = {"direct": direct_imports}
    update_with_transitive_imports(all_imports)
    return all_imports

class Rule:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment

    def match(self, regex):
        return RuleTargets(self).match(regex)

    def exclude(self, regex):
        return RuleTargets(self).exclude(regex)


def rule(name, comment=None):
    return Rule(name, comment=comment)


class RuleTargets:
    def __init__(self, rule):
        self.rule = rule
        self.match_criteria = []
        self.exclude_criteria = []

    def match(self, regex):
        self.match_criteria.append(regex)
        return self

    def exclude(self, regex):
        # update self
        self.exclude_criteria.append(regex)
        return self

    def should_not_import(self, regex):
        return RuleConstraints(self.rule, self).should_not_import(regex)

    def should_import(self, regex):
        return RuleConstraints(self.rule, self).should_import(regex)


class RuleConstraints:
    def __init__(self, rule, targets):
        self.rule = rule
        self.targets = targets
        self.forbidden = []
        self.required = []

    def should_not_import(self, regex):
        self.forbidden.append(regex)
        return self

    def should_import(self, regex):
        self.required.append(regex)
        return self

    def check(self, package, path=None):
        all_imports = _collect_imports(package, path)

        candidates = []
        for mp in self.targets.match_criteria:
            candidates.extend([k for k in all_imports.keys() if re.search(mp, k)])
        for ep in self.targets.exclude_criteria:
            candidates = [k for k in candidates if not re.search(ep, k)]

        for c in candidates:
            imports = all_imports[c].get("direct", []) | all_imports[c].get("transitive", [])
            for constraint in self.required:
                matches = [imp for imp in imports if re.search(constraint, imp)]
                check.is_true(matches, f"module {c} did not import anything that matches /{constraint}/")
            for constraint in self.forbidden:
                matches = [imp for imp in imports if re.search(constraint, imp)]
                check.is_false(matches, f"module {c} has forbidden imports {matches} (rule /{constraint}/)")
