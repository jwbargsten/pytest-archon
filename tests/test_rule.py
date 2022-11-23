import pytest_arch
from pytest_arch import archrule


def test_rule_basic():
    (
        archrule("basic rule")
        .match("*.collect")
        .constrain()
        .should_not_import("pytest_arch.rule")
        .check(pytest_arch)
    )


def test_rule_exclusion():
    (
        archrule("rule exclusion")
        .exclude("pytest_arch")
        .match("*")
        .exclude("pytest_arch.plugin")
        .constrain()
        .should_not_import("pytest_arch.rule")
        .check("pytest_arch")
    )


def test_rule_should_import():
    (
        archrule("rule exclusion")
        .match("pytest_arch.plugin")
        .constrain()
        .should_import("pytest_arch.rule")
        .check(pytest_arch)
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        from pytest_arch.plugin import archrule
        import pytest_arch

        def test_rule_fail():
            (
                archrule("abc", "def")
                .match("*collect")
                .constrain()
                .should_not_import("importl*")
                .check(pytest_arch)
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
