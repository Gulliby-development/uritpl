from uritpl.fault import Failure, Fault
from uritpl.model import FORMS, Expression, Item, Literal
from uritpl.text import has_surrogate, show
from uritpl.varspec import parse_varspec

_RESERVED_OPERATORS = frozenset("=,!@|")


def _parse_expression(text: str, start: int, end: int) -> Expression:
    source = text[start : end + 1]
    body = text[start + 1 : end]
    if not body:
        raise Fault("UT003", start + 1)

    op = body[0] if body[0] in FORMS else ""
    if not op and body[0] in _RESERVED_OPERATORS:
        raise Fault("UT004", start + 2, body[0])

    specs_text = body[1:] if op else body
    if op and not specs_text:
        raise Fault("UT003", start + 1)

    specs = []
    offset = start + 1 + (1 if op else 0)
    for spec_text in specs_text.split(","):
        specs.append(parse_varspec(spec_text, offset))
        offset += len(spec_text) + 1

    return Expression(op, tuple(specs), start + 1, source)


def parse_template(text: str) -> list[Item]:
    """Parse a URI template from left to right, preserving source columns."""
    items: list[Item] = []
    index = 0
    literal_start = 0

    while index < len(text):
        character = text[index]
        if character == "}":
            raise Fault("UT002", index + 1)
        if character != "{":
            index += 1
            continue

        if literal_start < index:
            items.append(Literal(text[literal_start:index], literal_start + 1))

        close = text.find("}", index + 1)
        if close < 0:
            raise Fault("UT001", index + 1)

        items.append(_parse_expression(text, index, close))
        index = close + 1
        literal_start = index

    if literal_start < len(text):
        items.append(Literal(text[literal_start:], literal_start + 1))
    return items


def read_template(arg: str) -> list[Item]:
    """Parse a command-line template, translating syntax faults to failures."""
    if has_surrogate(arg):
        raise Failure(f"invalid text {show(arg)}")
    try:
        return parse_template(arg)
    except Fault as fault:
        raise Failure(f"template:{fault.col}: {fault.code} {fault.text}") from None
