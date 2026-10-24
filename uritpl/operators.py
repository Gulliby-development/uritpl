from dataclasses import dataclass


@dataclass(frozen=True)
class Operator:
    """Expansion behavior associated with one URI-template operator."""

    symbol: str
    first: str
    sep: str
    named: bool
    ifemp: str
    allow_reserved: bool


OPERATORS = {
    "": Operator("", "", ",", False, "", False),
    "+": Operator("+", "", ",", False, "", True),
    "#": Operator("#", "#", ",", False, "", True),
    ".": Operator(".", ".", ".", False, "", False),
    "/": Operator("/", "/", "/", False, "", False),
    ";": Operator(";", ";", ";", True, "", False),
    "?": Operator("?", "?", "&", True, "=", False),
    "&": Operator("&", "&", "&", True, "=", False),
}
