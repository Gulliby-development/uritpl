from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from uritpl.fault import Fault
from uritpl.model import Varspec
from uritpl.varspec import parse_varspec


@pytest.mark.parametrize(
    ("text", "offset", "expected"),
    [
        ("a", 0, Varspec("a", "", 0, 1)),
        ("Az09_", 2, Varspec("Az09_", "", 0, 3)),
        ("a.b", 0, Varspec("a.b", "", 0, 1)),
        ("%41", 0, Varspec("%41", "", 0, 1)),
        ("a:1", 0, Varspec("a", "prefix", 1, 1)),
        ("a:9999", 4, Varspec("a", "prefix", 9999, 5)),
        ("a*", 2, Varspec("a", "explode", 0, 3)),
    ],
)
def test_valid_varspecs_preserve_names_offsets_and_modifiers(text, offset, expected):
    actual = parse_varspec(text, offset)
    assert actual == expected
    assert is_dataclass(actual)


@pytest.mark.parametrize(
    "text",
    [
        "",
        ".a",
        "a.",
        "a..b",
        "%",
        "%4",
        "%zz",
        "a%Q0",
        "é",
        "٣",
        "a ",
        "a/b",
    ],
)
def test_invalid_names_raise_ut005_at_specification_start(text):
    with pytest.raises(Fault) as error:
        parse_varspec(text, 6)
    assert (error.value.code, error.value.col, error.value.arg, error.value.text) == (
        "UT005",
        7,
        "",
        "bad variable name",
    )


@pytest.mark.parametrize(
    "text",
    ["a:", "a:0", "a:05", "a:12345", "a:٣", "a:x", "a:3*", "a*b", "a*:3"],
)
def test_invalid_modifiers_raise_ut006_at_modifier(text):
    with pytest.raises(Fault) as error:
        parse_varspec(text, 4)
    assert (error.value.code, error.value.col, error.value.arg, error.value.text) == (
        "UT006",
        6,
        "",
        "bad modifier",
    )


@pytest.mark.parametrize("text", ["a b:0", "%4:0", "a..b:0"])
def test_name_errors_take_precedence_over_bad_modifiers(text):
    with pytest.raises(Fault) as error:
        parse_varspec(text, 8)
    assert (error.value.code, error.value.col) == ("UT005", 9)


def test_varspec_records_are_frozen():
    spec = parse_varspec("a:9999", 0)
    assert isinstance(spec, Varspec)
    with pytest.raises(FrozenInstanceError):
        spec.length = 1
