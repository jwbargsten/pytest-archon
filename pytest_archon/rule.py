from __future__ import annotations

from fnmatch import fnmatch
from types import ModuleType
from typing import Iterable, Sequence

from pytest_check.check_log import log_failure  # type: ignore[import]

from pytest_archon.collect import ImportMap, collect_imports, walk, walk_runtime, walk_toplevel


def archrule(name: str, comment: str | None = None) -> Rule:
    """Define a new architectural rule with a name and an optional comment."""
    return Rule(name, comment=comment)


# https://peps.python.org/pep-0451/
# the path is the package path: where the submodules are in
class Rule:
    def __init__(self, name: str, comment: str | None) -> None:
        """Define a new architectural rule with a name and a comment."""
        self.name = name
        self.comment = comment

    def match(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should match."""
        return RuleTargets(self).match(*pattern)

    def exclude(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should exclude from matching.

        Exclusion takes precedence of matching.
        """
        return RuleTargets(self).exclude(*pattern)


class RuleTargets:
    def __init__(self, rule: Rule) -> None:
        self.rule = rule
        self.match_criteria: list[str] = []
        self.exclude_criteria: list[str] = []

    def match(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should match."""
        self.match_criteria.extend(pattern)
        return self

    def exclude(self, *pattern: str) -> RuleTargets:
        """A glob pattern for modules this rule should exclude from matching.

        Exclusion takes precedence of matching.
        """
        self.exclude_criteria.extend(pattern)
        return self

    def should_not_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        not import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        return RuleConstraints(self.rule, self).should_not_import(*pattern)

    def should_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        return RuleConstraints(self.rule, self).should_import(*pattern)

    def may_import(self, *pattern: str) -> RuleConstraints:
        """Loosen the constraints from should_import and
        should_not_import: modules matching may_import are
        excluded/ignored from the constraint check.
        """
        return RuleConstraints(self.rule, self).may_import(*pattern)


class RuleConstraints:
    def __init__(self, rule: Rule, targets: RuleTargets) -> None:
        self.rule = rule
        self.targets = targets
        self.forbidden: list[str] = []
        self.required: list[str] = []
        self.ignored: list[str] = []

    def should_not_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        not import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        self.forbidden.extend(pattern)
        return self

    def should_import(self, *pattern: str) -> RuleConstraints:
        """Define a constraint that the defined modules should
        import modules that match the given pattern.

        Keep in mind that module dependencies are checked transtively.

        E.g. 'mymodule.submodule', 'mymodule.*'
        """
        self.required.extend(pattern)
        return self

    def may_import(self, *pattern: str) -> RuleConstraints:
        """Loosen the constraints from should_import and
        should_not_import: modules matching may_import are
        excluded/ignored from the constraint check.
        """
        self.ignored.extend(pattern)
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
            candidates.extend(k for k in all_imports.keys() if fnmatch(k, mp))
        for ep in exclude_criteria:
            candidates = [k for k in candidates if not fnmatch(k, ep)]

        if not candidates:
            log_failure(
                f"NO CANDIDATES MATCHED. Match criteria: {match_criteria}, "
                f"exclude_criteria: {exclude_criteria}",
            )
            return

        candidates = sorted(candidates)

        for candidate in candidates:
            import_map = {candidate: all_imports[candidate]} if only_direct_imports else all_imports

            for constraint in self._check_required_constraints(candidate, import_map):
                log_failure(
                    _fmt_rule(
                        rule_name,
                        rule_comment,
                        f"module '{candidate}' is missing REQUIRED imports matching pattern /{constraint}/",
                    ),
                )

            for constraint, path in self._check_forbidden_constraints(candidate, import_map):
                log_failure(
                    _fmt_rule(
                        rule_name,
                        rule_comment,
                        f"module '{candidate}' has FORBIDDEN imports:\n{path[-1]} "
                        f"(matched by /{constraint}/), "
                        f"through modules {' ↣ '.join(path[:-1])}.",
                    ),
                )

    def _check_required_constraints(self, module: str, all_imports: ImportMap):
        for constraint in self.required:
            if not any(
                imp for path in recurse_imports(module, all_imports) if fnmatch(imp := path[-1], constraint)
            ):
                yield constraint

    def _check_forbidden_constraints(
        self,
        module: str,
        all_imports: ImportMap,
    ):
        for constraint in self.forbidden:
            yield from (
                (constraint, path)
                for path in recurse_imports(module, all_imports)
                if fnmatch(path[-1], constraint)
                and not any(fnmatch(m, ignore) for ignore in self.ignored for m in path)
            )


def _fmt_rule(name, comment, text):
    res = f"RULE {name}: {text}"
    if comment:
        res += f"\n({comment})"
    return res


def recurse_imports(module: str, all_imports: ImportMap) -> Iterable[Sequence[str]]:
    seen = set()

    def recurse(path):
        mod = path[-1]
        if mod in seen or mod not in all_imports:
            return

        seen.add(mod)
        for imp in all_imports[mod]:
            new_path = path + (imp,)
            yield new_path
            yield from recurse(new_path)

    yield from recurse((module,))
