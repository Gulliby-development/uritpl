from uritpl.io import Io
from uritpl.model import Expression
from uritpl.options import need, parse
from uritpl.parse import read_template

USAGE = "names TEMPLATE"


def run_names(args: list[str], io: Io) -> int:
    """List each variable name in a template once, in first-appearance order."""
    parsed = parse(args, [])
    need(USAGE, parsed.args, 1, 1)
    items = read_template(parsed.args[0])

    names: list[str] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, Expression):
            for spec in item.specs:
                if spec.name not in seen:
                    seen.add(spec.name)
                    names.append(spec.name)

    if not names:
        return 1
    io.out("\n".join(names) + "\n")
    return 0
