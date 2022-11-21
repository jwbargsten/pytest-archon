import pytest


@pytest.fixture(scope="session")
def py3arch_modules():
    return "abc"
