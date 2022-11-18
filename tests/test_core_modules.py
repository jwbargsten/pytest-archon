import py3arch.core_modules as cm

def test_read():
  modules = cm.list_core_modules({"major": 3, "minor": 6})
  assert modules == []

