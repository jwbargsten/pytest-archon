import optparse
import sys
from pathlib import Path

from py3arch.collect import collect_modules
from py3arch.config import read_options, read_rules
from py3arch.rule import rule

usage = "usage: %prog -d [dir] [modules...]"


def main(argv=sys.argv) -> int:
    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-d", "--dir", dest="dir", help="base directory")

    options, args = parser.parse_args(argv)
    base_path = Path(options.dir) if options.dir else Path.cwd()

    rules = read_rules(base_path / "pyproject.toml")
    if not rules:
        print("No [tool.py3arch.rules] section found in pyproject.toml")
        return 1

    options = read_options(base_path / "pyproject.toml")

    package = args[1] if len(args) > 1 else options.get("source", ".")
    src_path = Path(options.get("base", base_path))

    mapping = collect_modules(src_path, package)
    voilations = [
        voilation for module, imports in mapping for i in imports if (voilation := rule(rules, module, i))
    ]

    for v in voilations:
        print(v)

    return int(bool(voilations))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
