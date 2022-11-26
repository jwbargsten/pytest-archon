def test_rule_basic(archrule):
    (
        archrule("abc", "def")
        .match("*collect")
        .should_not_import("pytest_archon.import_finder")
        .check("pytest_archon")
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        import pytest_archon

        def test_rule_fail(archrule):
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
