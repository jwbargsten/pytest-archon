from py3arch.pytest.plugin import rule


def test_rule_basic():
    (
        rule("abc", "def")
        .match(r"collect")
        .should_not_import("py3arch.import_finder")
        .check("py3arch", path=["."])
    )


def test_rule_fail(pytester):

    pytester.makepyfile(
        """
        def test_rule_fail():
            (
                rule("abc", "def")
                .match(r"collect")
                .should_not_import("importlib")
                .check("py3arch", path=["."])
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
