import pytest
import sys

import py3arch.core_modules as cm


def test_read_legacy():
    modules = cm.list_core_modules((3, 9))
    assert "__future__" in modules


def test_read():
    if sys.version_info >= (3, 10):
        modules = cm.list_core_modules((3, 10))
        assert "__future__" in modules


def test_read_error():
    with pytest.raises(FileNotFoundError):
        cm.list_core_modules((3, 5))
