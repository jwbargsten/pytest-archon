from py3arch.pytest.plugin import rule


def test_rule_basic():
    (
        rule("abc", "def")
        .match("*collect")
        .should_not_import("py3arch.import_finder")
        .check("py3arch", path=["."])
    )


def test_rule_fail(pytester):
    pytester.makepyfile(
        """
        from py3arch.pytest.plugin import rule
        import py3arch

        def test_rule_fail():
            (
                rule("abc", "def")
                .match("*collect")
                .should_not_import("importl*")
                .check(py3arch)
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
