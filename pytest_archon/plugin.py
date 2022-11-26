import pytest

from pytest_archon.rule import archrule


@pytest.fixture(name="archrule")
def check_fixture():
    return archrule
