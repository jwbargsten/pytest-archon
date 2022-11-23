from pytest_arch import archrule


def test_rule_basic():
    (
        archrule("abc", "def")
        .match("*collect")
        .should_not_import("pytest_arch.import_finder")
        .check("pytest_arch", path=["."])
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
                .should_not_import("importl*")
                .check(pytest_arch)
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
