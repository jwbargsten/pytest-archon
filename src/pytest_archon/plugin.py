from itertools import groupby
from operator import attrgetter

import pytest
from _pytest._code.code import ExceptionInfo

from pytest_archon.failure import pop_failures
from pytest_archon.rule import archrule


@pytest.fixture(name="archrule")
def check_fixture():
    return archrule


from _pytest.skipping import xfailed_key


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    failures = pop_failures()

    if failures and item._store[xfailed_key]:
        report.outcome = "skipped"
        report.wasxfail = item._store[xfailed_key].reason
        return

    longrepr = format_failures(failures)
    if longrepr:
        report.longrepr = longrepr
        report.outcome = "failed"

    if failures:
        try:
            raise AssertionError(report.longrepr)
        except AssertionError:
            excinfo = ExceptionInfo.from_current()
        call.excinfo = excinfo


def format_failures(failures):
    longrepr = []
    for rule_name, rule_failures in groupby(failures, attrgetter("rule_name")):
        longrepr.append(f"FAILED Rule '{rule_name}':")
        for reason, reason_failures in groupby(rule_failures, attrgetter("reason")):
            longrepr.append(f"- {reason}")
            for path in set(f.path for f in reason_failures):
                longrepr.append(f"    from {' ↣ '.join(path)}")
    return "\n".join(longrepr)


class ModelViolation(AssertionError):
    pass
