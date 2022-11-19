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
    def match(pats):
        return any(fnmatch(imported, p.strip()) for p in pats.split(","))

    for pat, rules in ruleset.items():
        if not fnmatch(module, pat):
            continue

        if isinstance(rules, str):
            rules = [rules]

        for rule in rules:
            parts = rule.split(" ", 1)
            if len(parts) == 1:
                if match(parts[0]):
                    # expicit allow
                    return
            elif parts[0] == "not":
                if match(parts[1]):
                    # explicit deny
                    return f"Import '{imported}' is not allows in '{module}' (rule: '{pat} => {rule}')"
            elif parts[0] == "only":
                # todo: split by comma
                if match(parts[1]):
                    # explicit allow
                    return
                else:
                    return f"Import '{imported}' is not allows in '{module}' (rule: '{pat} => {rule}')"
            else:
                raise ValueError(f"Don't know how to interpret rule '{rule}'")

    # No rule matches. 
    # TODO: What is our default? Should we add a 'strict' option?
    