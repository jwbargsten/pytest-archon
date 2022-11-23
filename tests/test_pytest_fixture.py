def test_rule_basic(archrule):
    (
        archrule("abc", "def")
        .match("*collect")
        .constrain()
        .should_not_import("pytest_arch.import_finder")
        .check("pytest_arch")
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        import pytest_arch

        def test_rule_fail(archrule):
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
