from uritpl.expand import trace_template
from uritpl.io import Inputs, Io
from uritpl.load import load_variables
from uritpl.options import need, parse
from uritpl.parse import read_template
from uritpl.text import show, table

USAGE = "trace [--strict] TEMPLATE VARS"


def run_trace(args: list[str], io: Io) -> int:
    """Trace each expression in a template using variables from a JSON source."""
    parsed = parse(args, ["--strict"])
    need(USAGE, parsed.args, 2, 2)

    items = read_template(parsed.args[0])
    source = Inputs(io).read(parsed.args[1])
    variables = load_variables(source)
    traces = trace_template(items, variables, "--strict" in parsed.flags)

    if traces:
        rows = [
            [str(number), show(expression), show(result)]
            for number, (expression, result) in enumerate(traces, start=1)
        ]
        io.out("\n".join(table(["N", "EXPRESSION", "RESULT"], rows)) + "\n")
    return 0
