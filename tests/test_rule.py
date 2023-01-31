import pytest_archon
from pytest_archon import archrule
from pytest_archon.failure import pop_failures
from pytest_archon.plugin import format_failures
import re


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


def test_rule_exclusion_regex():
    (
        archrule("rule exclusion", use_regex=True)
        .exclude(r"^pytest_archon$")
        .match(".*")
        .exclude(r"^pytest_archon\..lugin")
        .should_not_import(r"^pytest\warchon\.rule$")
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
    # may_import does not protect against forbidden imports from transitive dependencies
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
    failures = pop_failures()
    assert len(failures) == 1
    assert re.search(r"abcz\.moduleA.*has FORBIDDEN import abcz\.moduleD", failures[0].reason)


def test_bug_may_import_allows_other_modules_pt1(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/common/util.py", "import abcz.app\nimport abcz.common.date"),
        ("abcz/common/date.py", ""),
        ("abcz/app.py", ""),
    )

    (
        archrule("common has no dependencies")
        .match("abcz.common*")
        .should_not_import("abcz*")
        .may_import("abcz.common*")
        .check("abcz")
    )
    failures = pop_failures()
    assert len(failures) == 1
    assert re.search(r"abcz\.common\.util.*has FORBIDDEN import abcz\.app", failures[0].reason)


def test_bug_may_import_allows_other_modules_pt2(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/common/util.py", "import abcz.app"),
        ("abcz/app.py", ""),
    )

    (archrule("common has no dependencies").match("abcz.common*").should_not_import("abcz*").check("abcz"))
    failures = pop_failures()
    assert len(failures) == 1
    assert re.search(r"abcz\.common\.util.*has FORBIDDEN import abcz\.app", failures[0].reason)


def test_bug_may_import_allows_other_modules_pt3(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/common/util.py", "import abcz.app\nimport abcz.common.date"),
        ("abcz/common/date.py", ""),
        ("abcz/app.py", ""),
    )

    (archrule("common has no dependencies").match("abcz.common*").should_not_import("abcz*").check("abcz"))
    failures = pop_failures()
    assert len(failures) == 2
    assert any(
        re.search(r"abcz\.common\.util.*has FORBIDDEN import abcz\.app", failure.reason)
        for failure in failures
    )
    assert any(
        re.search(r"abcz\.common\.util.*has FORBIDDEN import abcz\.common\.date", failure.reason)
        for failure in failures
    )


def test_required_transitive_dependency_fails(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", ""),
    )
    (archrule("rule exclusion").match("abcz.moduleA").should_import("abcz.moduleD").check("abcz"))

    failures = pop_failures()
    longrepr = format_failures(failures)

    assert failures

    assert "FAILED Rule 'rule exclusion':" in longrepr
    assert (
        "- module 'abcz.moduleA' is missing REQUIRED imports matching glob pattern /abcz.moduleD/" in longrepr
    )


def test_forbidden_transitive_dependency_fails(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "import abcz.moduleC"),
        ("abcz/moduleC.py", "import abcz.moduleD"),
        ("abcz/moduleD.py", ""),
    )
    (archrule("rule exclusion").match("abcz.moduleA").should_not_import("abcz.moduleD").check("abcz"))

    failures = pop_failures()
    longrepr = format_failures(failures)

    assert failures
    assert longrepr
    assert "FAILED Rule 'rule exclusion':" in longrepr
    assert "- module 'abcz.moduleA' has FORBIDDEN import" in longrepr
    assert "abcz.moduleD (matched by glob pattern /abcz.moduleD/)" in longrepr
    assert "abcz.moduleA ↣ abcz.moduleB ↣ abcz.moduleC ↣ abcz.moduleD" in longrepr


def test_resolution_non_existing_module(create_testset):
    create_testset(
        ("abcz/__init__.py", ""),
        ("abcz/moduleA.py", "import abcz.moduleB"),
        ("abcz/moduleB.py", "from i_do_not_exist import i_also_do_not_exist\nimport abcz.moduleC"),
        ("abcz/moduleC.py", ""),
    )
    archrule("rule exclusion").match("abcz.moduleA").should_import("abcz.moduleC").check("abcz")
