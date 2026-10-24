from dataclasses import dataclass


@dataclass(frozen=True)
class Varspec:
    """A parsed variable specification and its source column."""

    name: str
    modifier: str
    length: int
    col: int


@dataclass(frozen=True)
class Literal:
    """A literal segment of a URI template."""

    text: str
    col: int


@dataclass(frozen=True)
class Expression:
    """A parsed URI-template expression."""

    op: str
    specs: tuple[Varspec, ...]
    col: int
    source: str


Item = Literal | Expression

FORMS = {
    "": "simple",
    "+": "reserved",
    "#": "fragment",
    ".": "label",
    "/": "path",
    ";": "parameter",
    "?": "query",
    "&": "continuation",
}
