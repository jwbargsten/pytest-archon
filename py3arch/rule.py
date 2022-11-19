"""
This is te one and only module that will rule if your
dependency si allowed or not.
"""

from fnmatch import fnmatch


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
            if c := rhs_matches(imported, rule):
                # expicit allow
                return None
            elif c is False:
                return f"Import '{imported}' is not allows in '{module}' (rule: '{pat} => {rule}')"

    # No rule matches.
    # TODO: What is our default? Should we add a 'strict' option?
    return None


def lhs_matches(module, rule) -> bool | None:
    """Test if an module matches a rule"""
    parts = rule.split(" ", 1)
    if len(parts) == 1:
        if match(module, parts[0]):
            # expicit allow
            return True
        return False
    elif parts[0] == "not":
        if match(module, parts[1]):
            # explicit deny
            return False
        return True

    raise ValueError(f"Don't know how to interpret rule '{rule}'")


def rhs_matches(imported, rule) -> bool | None:
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
            return True
    elif parts[0] == "not":
        if match(imported, parts[1]):
            # explicit deny
            return False
    elif parts[0] == "only":
        return match(imported, parts[1])
    else:
        raise ValueError(f"Don't know how to interpret rule '{rule}'")

    # undecided
    return None


def match(mod, pats):
    return any(fnmatch(mod, p.strip()) for p in pats.split(","))
