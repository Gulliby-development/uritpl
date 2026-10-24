from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    """A diagnostic located in a template or source file."""

    col: int
    code: str
    text: str


def sorted_problems(found: Iterable[Problem]) -> list[Problem]:
    """Return diagnostics ordered by column and code, preserving equal-key order."""
    return sorted(found, key=lambda problem: (problem.col, problem.code))


def render(display: str, line: int, problem: Problem) -> str:
    """Render a diagnostic without adding a prefix or line ending."""
    return f"{display}:{line}:{problem.col}: {problem.code} {problem.text}"
