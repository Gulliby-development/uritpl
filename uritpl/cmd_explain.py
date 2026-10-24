from uritpl.io import Io
from uritpl.model import FORMS, Expression
from uritpl.options import need, parse
from uritpl.parse import read_template
from uritpl.text import table

USAGE = "explain TEMPLATE"


def run_explain(args: list[str], io: Io) -> int:
    """List every variable specification in a URI template."""
    parsed = parse(args, [])
    need(USAGE, parsed.args, 1, 1)
    items = read_template(parsed.args[0])

    rows: list[list[str]] = []
    expression_number = 0
    for item in items:
        if not isinstance(item, Expression):
            continue
        expression_number += 1
        operator = item.op if item.op else "-"
        for spec in item.specs:
            if spec.modifier == "prefix":
                modifier = f"prefix {spec.length}"
            elif spec.modifier == "explode":
                modifier = "explode"
            else:
                modifier = "-"
            rows.append(
                [
                    str(expression_number),
                    str(item.col),
                    operator,
                    FORMS[item.op],
                    spec.name,
                    modifier,
                ]
            )

    if not rows:
        return 1

    output = "\n".join(table(["N", "COL", "OP", "FORM", "NAME", "MODIFIER"], rows)) + "\n"
    io.out(output)
    return 0
