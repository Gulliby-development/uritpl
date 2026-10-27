from dataclasses import dataclass, field

from uritpl.fault import Failure
from uritpl.text import show


@dataclass
class Parsed:
    """Parsed command-line options and the remaining ordinary arguments."""

    flags: set[str]
    args: list[str]
    values: dict[str, str] = field(default_factory=dict)


def parse(
    argv: list[str],
    specs: list[str] | set[str],
    value_specs: list[str] | set[str] | tuple[str, ...] = (),
) -> Parsed:
    """Separate recognized long options from ordinary arguments.

    A flag is written as `--name`. An option that takes a value is written `--name=VALUE`
    and is recognized only when it is listed in `value_specs`.
    """
    allowed = set(specs)
    value_allowed = set(value_specs)
    flags: set[str] = set()
    values: dict[str, str] = {}
    args: list[str] = []
    for argument in argv:
        if argument.startswith("--"):
            name, equals, text = argument.partition("=")
            if name in value_allowed:
                if not equals:
                    raise Failure(f"option {show(name)} needs a value")
                values[name] = text
            elif argument not in allowed:
                raise Failure(f"unknown option {show(argument)}")
            else:
                flags.add(argument)
        else:
            args.append(argument)
    return Parsed(flags=flags, args=args, values=values)


def need(words: str, args: list[str], low: int, high: int) -> None:
    """Require an argument count within the specified inclusive bounds."""
    if len(args) < low or (high >= 0 and len(args) > high):
        raise Failure(f"usage: {words}")
