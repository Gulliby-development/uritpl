from uritpl.fault import Failure
from uritpl.model import Expression, Item, Literal
from uritpl.operators import OPERATORS
from uritpl.percent import encode
from uritpl.text import show
from uritpl.value import Value, is_undefined
from uritpl.varexp import expand_varspec


def expand_expression(expr: Expression, variables: dict[str, Value | None], strict: bool) -> str:
    """Expand one parsed expression using the supplied variable values."""
    operator = OPERATORS[expr.op]
    pieces: list[str] = []

    for spec in expr.specs:
        value = variables.get(spec.name)
        if is_undefined(value):
            if strict:
                raise Failure(f"undefined variable {show(spec.name)}")
            continue
        pieces.extend(expand_varspec(operator, spec, value))

    if not pieces:
        return ""
    return operator.first + operator.sep.join(pieces)


def expand_template(items: list[Item], variables: dict[str, Value | None], strict: bool) -> str:
    """Expand parsed template items, percent-encoding literal text."""
    pieces: list[str] = []
    for item in items:
        if isinstance(item, Literal):
            pieces.append(encode(item.text, True))
        else:
            pieces.append(expand_expression(item, variables, strict))
    return "".join(pieces)


def trace_template(
    items: list[Item], variables: dict[str, Value | None], strict: bool
) -> list[tuple[str, str]]:
    """Return each expression's source spelling and expanded result."""
    return [
        (item.source, expand_expression(item, variables, strict))
        for item in items
        if isinstance(item, Expression)
    ]
