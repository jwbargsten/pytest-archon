import pytest

from pytest_archon.rule import Rule, RuleConstraints, RuleTargets


@pytest.mark.parametrize(
    "method1,method2",
    [
        (Rule.match, RuleTargets.match),
        (Rule.exclude, RuleTargets.exclude),
        (RuleTargets.should_import, RuleConstraints.should_import),
        (RuleTargets.should_not_import, RuleConstraints.should_not_import),
    ],
)
def test_docstrings_match(method1, method2):
    assert method1.__doc__ == method2.__doc__
