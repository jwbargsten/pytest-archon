import modulefinder
import os
import importlib
from pathlib import Path
import marshal
from py3arch.modulefinder import  ModuleFinder as P3MF


def _calc___package__(globals):
    """Calculate what __package__ should be.
    __package__ is not guaranteed to be defined or could be set to None
    to represent that its proper value is unknown.
    """
    package = globals.get("__package__")
    spec = globals.get("__spec__")
    if package is not None:
        if spec is not None and package != spec.parent:
            return package
    elif spec is not None:
        return spec.parent
    else:
        package = globals["__name__"]
        if "__path__" not in globals:
            package = package.rpartition(".")[0]
    return package


from modulefinder import ModuleFinder
from py3arch.core_modules import list_core_modules
import os
import sys
import importlib

_SEARCH_ERROR = 0
_PY_SOURCE = 1
_PY_COMPILED = 2
_C_EXTENSION = 3
_PKG_DIRECTORY = 5
_C_BUILTIN = 6
_PY_FROZEN = 7


class MyMf2(modulefinder.ModuleFinder):
    def __init__(self, path=None, debug=0, excludes=None, replace_paths=None, pkgPath=None):
        self.pkgPath = pkgPath
        super().__init__(path, debug, excludes, replace_paths)

    def add_module2(self, fqname, pathname):
        if fqname in self.modules:
            return self.modules[fqname]
        m = MyModule(fqname, pathname, pkgPath=self.pkgPath)
        # print(f"ADDMODULES: {m.__name__}")
        self.modules[m.__name__] = m
        if fqname == "__init__":
            self.modules[m.__name__.removesuffix(".__init__")] = m

        return m

    def load_module(self, fqname, fp, pathname, file_info):
        suffix, mode, type = file_info
        self.msgin(2, "load_module", fqname, fp and "fp", pathname)
        if type == _PKG_DIRECTORY:
            m = self.load_package(fqname, pathname)
            self.msgout(2, "load_module ->", m)
            return m
        if type == _PY_SOURCE:
            co = compile(fp.read(), pathname, "exec")
        else:
            co = None
        m = self.add_module2(fqname, pathname)
        if co:
            if self.replace_paths:
                co = self.replace_paths_in_code(co)
            m.__code__ = co
            self.scan_code(co, m)
        self.msgout(2, "load_module ->", m)
        return m


class MyMf(modulefinder.ModuleFinder):
    def determine_parent(self, caller, level=0):
        self.msgin(4, "determine_parent", caller, level)
        if not caller or level == 0:
            self.msgout(4, "determine_parent -> None")
            return None
        if level < 0:
            raise ValueError("level must be >= 0")

        # If we got this far, it's a relative import.
        pname = caller.__name__
        if not isinstance(pname, str):
            raise TypeError("__package__ not set to a string")

        if level == 1:
            parent = self.modules[pname]
            self.msgout(4, "determine_parent ->", parent)
            return parent
        if pname.count(".") < level - 1:
            raise ImportError("relative importpath too deep")
        pname = ".".join(pname.split(".")[: -level + 1])
        parent = self.modules[pname]
        self.msgout(4, "determine_parent ->", parent)
        return parent


import io


def load_file(mf, pathname, fqname):
    dir, name = os.path.split(pathname)
    name, ext = os.path.splitext(name)
    with io.open_code(pathname) as fp:
        stuff = (ext, "rb", 1)
        mf.load_module(fqname, fp, pathname, stuff)


def path2module(path, pkgPath=None, name=None):
    if path is None:
        return name
    path = Path(path)
    if name is None:
        name = path.stem

    if pkgPath is None:
        return name

    rel_path = path.relative_to(pkgPath)
    # if name == "__init__":
    #     return ".".join(rel_path.parent.parts)
    return ".".join(rel_path.parent.parts + (name,))


class MyModule(modulefinder.Module):
    def __init__(self, name, file=None, path=None, pkgPath=None):
        self.pkgPath = pkgPath
        fqname = path2module(file, pkgPath, name)
        # print(f"{pkgPath=} {name=} {file=} {fqname=}")

        super().__init__(fqname, file, path)


def test_modules():
    core_modules = list_core_modules()
    pkg_path = "/Users/jwb/entwicklung/meins/pydeps/pydeps"
    for root, dirs, files in os.walk(str(pkg_path), followlinks=False):
        root = Path(root)

        for f in files:

            finder = P3MF(path=[pkg_path] + sys.path, debug=3, excludes=core_modules, pkg_path=pkg_path)
            if not f.lower().endswith(".py"):
                continue
            print(root / f)
            finder.load_file(str(root / f))

            for name, mod in finder.modules.items():
                print(f"---------> {mod.fqname}")

def test_x():
    core_modules = list_core_modules()
    f = "/Users/jwb/entwicklung/meins/pydeps/pydeps/depgraph.py"
    pkg_path = "/Users/jwb/entwicklung/meins/pydeps/pydeps"
    finder = P3MF(path=[pkg_path] + sys.path, debug=0, excludes=core_modules, pkg_path=pkg_path)
    finder.load_file(str(f))

    for name, mod in finder.modules.items():
        print(f"---------> {mod.fqname}")
