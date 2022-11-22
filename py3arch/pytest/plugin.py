from pytest_check import check
import sys
import re

from py3arch.collect import collect_imports


# https://peps.python.org/pep-0451/
# the path is the package path: where the submodules are in
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
        if path is not None:
            sys.path.append(path) if isinstance(path, str) else sys.path.extend(path)

        all_imports = collect_imports(package)

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
