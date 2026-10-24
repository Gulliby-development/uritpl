from dataclasses import dataclass

from uritpl.fault import Failure
from uritpl.text import show


@dataclass
class Parsed:
    """Parsed command-line options and the remaining ordinary arguments."""

    flags: set[str]
    args: list[str]


def parse(argv: list[str], specs: list[str] | set[str]) -> Parsed:
    """Separate recognized long options from ordinary arguments."""
    allowed = set(specs)
    flags: set[str] = set()
    args: list[str] = []
    for argument in argv:
        if argument.startswith("--"):
            if argument not in allowed:
                raise Failure(f"unknown option {show(argument)}")
            flags.add(argument)
        else:
            args.append(argument)
    return Parsed(flags=flags, args=args)


def need(words: str, args: list[str], low: int, high: int) -> None:
    """Require an argument count within the specified inclusive bounds."""
    if len(args) < low or (high >= 0 and len(args) > high):
        raise Failure(f"usage: {words}")
