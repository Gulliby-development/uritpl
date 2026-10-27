from uritpl.expand import trace_template
from uritpl.fault import Failure
from uritpl.io import Inputs, Io
from uritpl.load import load_variables
from uritpl.options import need, parse
from uritpl.parse import read_template
from uritpl.text import show, table

USAGE = "trace [--strict] [--only=N] TEMPLATE VARS"


def only_number(text: str) -> int:
    """Return the expression number given to --only, a whole number from 1."""
    if not (text.isascii() and text.isdigit()) or int(text) < 1:
        raise Failure(f"invalid --only value {show(text)}")
    return int(text)


def run_trace(args: list[str], io: Io) -> int:
    """Trace each expression in a template using variables from a JSON source."""
    parsed = parse(args, ["--strict"], ["--only"])
    need(USAGE, parsed.args, 2, 2)
    only = only_number(parsed.values["--only"]) if "--only" in parsed.values else None

    items = read_template(parsed.args[0])
    source = Inputs(io).read(parsed.args[1])
    variables = load_variables(source)
    traces = trace_template(items, variables, "--strict" in parsed.flags)

    numbered = list(enumerate(traces, start=1))
    if only is not None:
        if only > len(numbered):
            raise Failure(f"expression {only} not found (the template has {len(numbered)})")
        numbered = [numbered[only - 1]]
    if numbered:
        rows = [
            [str(number), show(expression), show(result)]
            for number, (expression, result) in numbered
        ]
        io.out("\n".join(table(["N", "EXPRESSION", "RESULT"], rows)) + "\n")
    return 0
