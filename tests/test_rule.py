import pytest_archon
from pytest_archon import archrule


def test_rule_basic():
    (archrule("basic rule").match("*.collect").should_not_import("pytest_archon.rule").check(pytest_archon))


def test_rule_exclusion():
    (
        archrule("rule exclusion")
        .exclude("pytest_archon")
        .match("*")
        .exclude("pytest_archon.plugin")
        .should_not_import("pytest_archon.rule")
        .check("pytest_archon")
    )


def test_rule_should_import():
    (
        archrule("rule exclusion")
        .match("pytest_archon.plugin")
        .should_import("pytest_archon.rule")
        .check(pytest_archon)
    )


def test_rule_should_import_list():
    (
        archrule("rule exclusion")
        .match("pytest_archon.plugin")
        .should_import("pytest_archon.rule", "pytest")
        .check(pytest_archon)
    )


def test_toplevel_imports_only():
    (
        archrule("rule exclusion")
        .match("pytest_archon.plugin")
        .should_import("pytest_archon.rule")
        .check(pytest_archon, only_toplevel_imports=True)
    )


def test_only_direct():
    (
        archrule("rule exclusion")
        .match("pytest_archon.plugin")
        .should_not_import("pytest_archon.collect")
        .check("pytest_archon", only_direct_imports=True)
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        from pytest_archon.plugin import archrule
        import pytest_archon

        def test_rule_fail():
            (
                archrule("abc", "def")
                .match("*collect")
                .should_not_import("importl*")
                .check(pytest_archon)
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
