from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def read_rules(file_path: Path) -> dict[str, str | list[str]] | None:
    toml_text = file_path.read_text(encoding="utf-8")
    config = tomllib.loads(toml_text)
    rules_section = config.get("tool", {}).get("py3arch", {}).get("rules", None)
    if not rules_section:
        return None  # Empty rule set?

    return rules_section
