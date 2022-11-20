from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def read_options(pyproject: Path) -> dict[str, str | list[str]] | None:
    return _read_pyproject(pyproject, "options", {})


def read_rules(pyproject: Path) -> dict[str, str | list[str]] | None:
    rules_section = _read_pyproject(pyproject, "rules")
    if not rules_section:
        return None  # Empty rule set?

    return rules_section


def _read_pyproject(pyproject: Path, section: str, default=None):
    toml_text = pyproject.read_text(encoding="utf-8")
    config = tomllib.loads(toml_text)
    return config.get("tool", {}).get("py3arch", {}).get(section, default)
