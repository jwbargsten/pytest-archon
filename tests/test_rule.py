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


def test_transitive_dependency_succeeds(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", "import abcz.moduleD"),
        ("abcz/moduleD.py", ""),
    )
    archrule("rule exclusion").match("abcz.moduleA").should_import("abcz.moduleD").check("abcz")


def test_transitive_dependency_via_may_import_succeeds(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", "import abcz.moduleD"),
        ("abcz/moduleD.py", ""),
    )
    (
        archrule("rule exclusion")
        .match("abcz.moduleA")
        .may_import("abcz.moduleC")
        .should_not_import("abcz.moduleD")
        .check("abcz")
    )


def test_required_transitive_dependency_fails(create_testset, pytester):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", ""),
    )
    pytester.makepyfile(
        """
        from pytest_archon.plugin import archrule
        import pytest_archon

        def test_rule_fail():
            (
                archrule("rule exclusion")
                .match("abcz.moduleA")
                .should_import("abcz.moduleD")
                .check("abcz")
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        "FAILURE: RULE rule exclusion: module 'abcz.moduleA' is missing REQUIRED imports "
        "matching pattern glob /abcz.moduleD/"
    )


def test_forbidden_transitive_dependency_fails(create_testset, pytester):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", "import abcz.moduleD"),
        ("abcz/moduleD.py", ""),
    )
    pytester.makepyfile(
        """
        from pytest_archon.plugin import archrule
        import pytest_archon

        def test_rule_fail():
            (
                archrule("rule exclusion")
                .match("abcz.moduleA")
                .should_not_import("abcz.moduleD")
                .check("abcz")
            )
    """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("FAILURE: RULE rule exclusion: module 'abcz.moduleA' has FORBIDDEN imports*")
    result.stdout.fnmatch_lines("abcz.moduleD (matched by glob /abcz.moduleD/)*")
    result.stdout.fnmatch_lines("*through modules abcz.moduleA ↣ abcz.moduleB ↣ abcz.moduleC.*")
