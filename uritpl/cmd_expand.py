from uritpl.expand import expand_template
from uritpl.io import Inputs, Io
from uritpl.load import load_variables
from uritpl.options import need, parse
from uritpl.parse import read_template

USAGE = "expand [--strict] TEMPLATE VARS"


def run_expand(args: list[str], io: Io) -> int:
    """Expand one URI template using variables read from a JSON source."""
    parsed = parse(args, ["--strict"])
    need(USAGE, parsed.args, 2, 2)

    items = read_template(parsed.args[0])
    source = Inputs(io).read(parsed.args[1])
    variables = load_variables(source)
    result = expand_template(items, variables, "--strict" in parsed.flags)

    if result:
        io.out(result)
    return 0
