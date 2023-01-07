"""
This code is based on pytest-check, by Bryan Okken (MIT License)
https://github.com/okken/pytest-check.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    rule_name: str
    rule_comment: str
    reason: str
    path: tuple[str, ...]


_failures: list[Failure] = []


def add_failure(rule_name, rule_comment, reason, path: list[str] | None = None):
    global _failures
    _failures.append(Failure(rule_name, rule_comment, reason, tuple(path) if path else ()))


def pop_failures():
    global _failures
    try:
        return _failures
    finally:
        _failures = []
