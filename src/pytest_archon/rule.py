from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from types import ModuleType
from typing import Callable, Set


from pytest_archon.collect import (
    ImportMap,
    collect_imports,
    recurse_imports,
    walk,
    walk_runtime,
    walk_toplevel,
)
from pytest_archon.failure import add_failure  # type: ignore[import]


ConstraintPredicate = Callable[[str, Set[str], ImportMap], bool]


@dataclass
class RulePattern:
    is_regex: bool
    pattern: str

    def match(self, k: str):
        if self.is_regex:
            return re.search(self.pattern, k)
        else:
            return fnmatchcase(k, self.pattern)

    def __str__(self):
        if self.is_regex:
            return f"regex pattern /{self.pattern}/"
        else:
            return f"glob pattern /{self.pattern}/"


def _as_rule_patterns(use_regex, patterns):
    return [RulePattern(is_regex=use_regex, pattern=p) for p in patterns]


def archrule(name: str, comment: str | None = None, *, use_regex: bool = False) -> Rule:
    """Define a new architectural rule with a name and an optional comment."""
    return Rule(name, comment=comment, use_regex=use_regex)


# https://peps.python.org/pep-0451/
# the path is the package path: where the submodules are in
class Rule:
    def __init__(self, name: str, comment: str | None, use_regex: bool = False) -> None:
        """Define a new architectural rule with a name and a comment."""
        self.name = name
        self.comment = comment
        self.use_regex = use_regex

    def match(self, *pattern: str, **kwargs) -> RuleTargets:
        """A glob pattern for modules this rule should match."""
        return RuleTargets(self).match(*pattern, **kwargs)

    def exclude(self, *pattern: str, **kwargs) -> RuleTargets:
        """A glob pattern for modules this rule should exclude from matching.

        Exclusion takes precedence of matching.
        """
        return RuleTargets(self).exclude(*pattern, **kwargs)


class RuleTargets:
    def __init__(self, rule: Rule) -> None:
        self.rule = rule
        self.match_criteria: list[RulePattern] = []
        self.exclude_criteria: list[RulePattern] = []

    def match(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should match."""

        self.match_criteria.extend(_as_rule_patterns(self.rule.use_regex, pattern))
        return self

    def exclude(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should exclude from matching.

        Exclusion takes precedence of matching.
        """
        self.exclude_criteria.extend(_as_rule_patterns(self.rule.use_regex, pattern))
        return self

    def should_not_import(self, *pattern: str, **kwargs) -> RuleConstraints:
        """Define a constraint that the defined modules should
        not import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        return RuleConstraints(self.rule, self).should_not_import(*pattern, **kwargs)

    def should(self, pred: ConstraintPredicate, name=None) -> RuleConstraints:
        """Define a constraint using a supplied function/predicate.

        If the predicate function returns ``False``, the constraint is
        considered as being violated.

        :param pred: a function with the signature
            ``pred(module, direct_imports, all_imports)``
        :type pred: ConstraintPredicate
        :param name: An optional name for this constraint. If omitted,
            the name will be inferred from the predicate function.
        :rtype: RuleConstraints
        """
        return RuleConstraints(self.rule, self).should(pred, name)

    def should_import(self, *pattern: str, **kwargs) -> RuleConstraints:
        """Define a constraint that the defined modules should
        import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        return RuleConstraints(self.rule, self).should_import(*pattern, **kwargs)

    def may_import(self, *pattern: str, **kwargs) -> RuleConstraints:
        """Loosen the constraints from should_import and
        should_not_import: modules matching may_import are
        excluded/ignored from the constraint check.
        """
        return RuleConstraints(self.rule, self).may_import(*pattern, **kwargs)


class RuleConstraints:
    def __init__(self, rule: Rule, targets: RuleTargets) -> None:
        self.rule = rule
        self.targets = targets
        self.forbidden: list[RulePattern] = []
        self.required: list[RulePattern] = []
        self.ignored: list[RulePattern] = []
        self.constraint_preds: list[tuple[ConstraintPredicate, str]] = []

    def should_not_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        not import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        self.forbidden.extend(_as_rule_patterns(self.rule.use_regex, pattern))
        return self

    def should_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        self.required.extend(_as_rule_patterns(self.rule.use_regex, pattern))
        return self

    def should(self, pred: ConstraintPredicate, name=None):
        self.constraint_preds.append((pred, name or pred.__name__))
        return self

    def may_import(self, *pattern: str) -> RuleConstraints:
        """Loosen the constraints from should_import and
        should_not_import: modules matching may_import are
        excluded/ignored from the constraint check.
        """
        self.ignored.extend(_as_rule_patterns(self.rule.use_regex, pattern))
        return self

    def check(
        self,
        package: str | ModuleType,
        *,
        skip_type_checking=False,
        only_toplevel_imports=False,
        only_direct_imports=False,
    ) -> None:
        """Check the rule against a package or module.

        Options:

        skip_type_checking:
           Do not check TYPE_CHECKING blocks, used by static code analysers
        only_toplevel_imports:
            Do not traverse functions and methods, looking for imports
        only_direct_imports:
            Only check imports done by the module, not indirect imports
        """
        rule_name = self.rule.name
        rule_comment = self.rule.comment

        if only_toplevel_imports:
            walker = walk_toplevel
        elif skip_type_checking:
            walker = walk_runtime
        else:
            walker = walk

        all_imports = collect_imports(
            package,
            walker,
        )
        match_criteria = self.targets.match_criteria
        exclude_criteria = self.targets.exclude_criteria

        candidates: list[str] = []
        for mp in match_criteria:
            candidates.extend(k for k in all_imports.keys() if mp.match(k))
        for ep in exclude_criteria:
            candidates = [k for k in candidates if not ep.match(k)]

        match_criteria_pretty = [str(c) for c in match_criteria]
        exclude_criteria_pretty = [str(c) for c in exclude_criteria]
        if not candidates:
            add_failure(
                rule_name,
                rule_comment,
                f"NO CANDIDATES MATCHED. Match criteria: {match_criteria_pretty}, "
                f"exclude_criteria: {exclude_criteria_pretty}",
            )
            return

        candidates = sorted(candidates)

        for candidate in candidates:
            import_map = {candidate: all_imports[candidate]} if only_direct_imports else all_imports

            for constraint in self._find_required_constraints(candidate, import_map):
                add_failure(
                    rule_name,
                    rule_comment,
                    f"module '{candidate}' is missing REQUIRED imports matching {constraint}",
                    ["."],
                )

            for constraint, path in self._find_forbidden_constraints(candidate, import_map):
                add_failure(
                    rule_name,
                    rule_comment,
                    f"module '{candidate}' has FORBIDDEN import {path[-1]} (matched by {constraint})",
                    path,
                )

            for constraint in self._find_constraint_predicates(candidate, import_map):
                add_failure(
                    rule_name,
                    rule_comment,
                    f"module '{candidate}' VIOLATED constraint '{constraint}'",
                    ["."],
                )

    def _find_required_constraints(self, module: str, all_imports: ImportMap):
        for constraint in self.required:
            if not any(
                imp for path in recurse_imports(module, all_imports) if constraint.match(imp := path[-1])
            ):
                yield constraint

    def _find_constraint_predicates(self, module: str, all_imports: ImportMap):
        direct_imports = all_imports[module]
        for pred, name in self.constraint_preds:
            if not pred(module, direct_imports, all_imports):
                yield name

    def _find_forbidden_constraints(
        self,
        module: str,
        all_imports: ImportMap,
    ):
        for constraint in self.forbidden:
            yield from (
                (constraint, path)
                for path in recurse_imports(module, all_imports)
                if constraint.match(path[-1]) and not any(ignore.match(path[-1]) for ignore in self.ignored)
            )
