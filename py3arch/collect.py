import sys
from pathlib import Path
from typing import Iterable
from modulefinder import ModuleFinder, Module


def collect_modules(base_path: Path) -> Iterable[tuple[tuple[str], Path, Module]]:
    for module_path in base_path.glob('**/*.py'):
        finder = ModuleFinder(path=[str(base_path), *sys.path])
        finder.run_script(str(module_path))

        yield (path_to_module_name(module_path, base_path), module_path, list(finder.modules.values()))


def path_to_module_name(module_path: Path, base_path: Path):
    rel_path = module_path.relative_to(base_path)
    return rel_path.parent.parts + (rel_path.stem,)
