import optparse
import sys
from pathlib import Path

from py3arch.collect import collect_imports_from_path
from py3arch.config import read_options, read_rules
from py3arch.rule import rule

usage = "usage: %prog -d [dir] [modules...]"


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv
    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-d", "--dir", dest="dir", help="base directory")

    options, args = parser.parse_args(argv)
    base_path = Path(options.dir) if options.dir else Path.cwd()

    rules = read_rules(base_path / "pyproject.toml")
    if not rules:
        print("No [tool.py3arch.rules] section found in pyproject.toml")
        return 1

    options = read_options(base_path / "pyproject.toml")

    package = args[0] if args else options.get("package", None)
    if package is None:
        raise KeyError("no package supplied via commandline option or via pyproject.toml")
    src_path = Path(options.get("base", base_path))

    sys.path.append(str(src_path))
    mapping = collect_imports_from_path(src_path / package, package)

    violations = [
        violations
        for module, imports in mapping
        for imp in imports
        if (violations := rule(rules, module, imp))
    ]

    for v in violations:
        print(v)

    return int(bool(violations))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
