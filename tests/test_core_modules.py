import py3arch.core_modules as cm

def test_read():
  modules = cm.list_core_modules([3, 9])
  assert "__future__" in modules

