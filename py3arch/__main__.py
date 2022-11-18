import sys
from pathlib import Path

from py3arch.collect import collect_modules
from py3arch.core_modules import list_core_modules

if __name__ == "__main__":
    for name, path, modules in collect_modules(Path(sys.argv[1]), sys.argv[2]):
        for m in modules:
            print(".".join(name), "->", m.__name__)
        # break
