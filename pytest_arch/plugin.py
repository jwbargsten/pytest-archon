import pytest

from pytest_arch.rule import archrule


@pytest.fixture(name="archrule")
def check_fixture():
    return archrule
