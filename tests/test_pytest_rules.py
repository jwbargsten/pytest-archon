from pytest_arch.plugin import rule


def test_rule_basic():
    (
        rule("abc", "def")
        .match("*collect")
        .should_not_import("pytest_arch.import_finder")
        .check("pytest_arch", path=["."])
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        from pytest_arch.plugin import rule
        import pytest_arch

        def test_rule_fail():
            (
                rule("abc", "def")
                .match("*collect")
                .should_not_import("importl*")
                .check(pytest_arch)
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
