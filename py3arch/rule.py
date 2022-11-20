"""
This is te one and only module that will rule if your
dependency si allowed or not.
"""
from __future__ import annotations

from fnmatch import fnmatch

UNDECIDED, ALLOWED, DENIED = (0, 1, 2)


def rule(ruleset, module, imported) -> str | None:
    """Take a set of rules (module: list[module]) and a
    module and it's import and determine if it's valid.

    The rules should be sound.
    """

    for pat, rules in ruleset.items():
        if not lhs_matches(module, pat):
            continue

        if isinstance(rules, str):
            rules = [rules]

        for rule in rules:
            if (c := rhs_matches(imported, rule)) is ALLOWED:
                return None
            elif c is DENIED:
                return f"Import '{imported}' is not allows in '{module}' (rule: '{pat} => {rule}')"

    # No rule matches.
    # TODO: What is our default? Should we add a 'strict' option?
    return None


def lhs_matches(module, rule) -> bool:
    """Test if an module matches a rule"""
    parts = rule.split(" ", 1)
    if len(parts) == 1:
        return match(module, parts[0])
    elif parts[0] == "not":
        return not match(module, parts[1])

    raise ValueError(f"Don't know how to interpret rule '{rule}'")


def rhs_matches(imported, rule) -> int:
    """Test if an import complies to the rule.

    Return a tri-state: True, False, None.
    True is return on a positive check,
    False on a negating check.
    In case of None, the rule is undecided.
    """
    parts = rule.split(" ", 1)
    if len(parts) == 1:
        if match(imported, parts[0]):
            # expicit allow
            return ALLOWED
    elif parts[0] == "not":
        if match(imported, parts[1]):
            # explicit deny
            return DENIED
    elif parts[0] == "only":
        return ALLOWED if match(imported, parts[1]) else DENIED
    else:
        raise ValueError(f"Don't know how to interpret rule '{rule}'")

    return UNDECIDED


def match(mod, pats):
    return any(fnmatch(mod, p.strip()) or fnmatch(mod, f"{p.strip()}.*") for p in pats.split(","))
