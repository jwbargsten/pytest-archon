import optparse
import sys
from pathlib import Path

from py3arch.collect import collect_modules
from py3arch.config import read_rules
from py3arch.rule import rule

usage = "usage: %prog -d [dir] [package]"


def main(argv=sys.argv) -> int:
    parser = optparse.OptionParser(usage=usage)

    parser.add_option("-d", "--dir", dest="dir", help="base directory")

    options, args = parser.parse_args(argv)
    base_path = Path(options.dir) if options.dir else Path.cwd()
    package = args[1] if len(args) > 1 else "."

    rules = read_rules(base_path / "pyproject.toml")
    if not rules:
        print("No [tool.py3arch.rules] section found in pyproject.toml")
        return 1

    mapping = collect_modules(base_path, package)
    voilations = [voilation for module, imported in mapping if (voilation := rule(rules, module, imported))]

    for v in voilations:
        print(v)

    return int(bool(voilations))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
