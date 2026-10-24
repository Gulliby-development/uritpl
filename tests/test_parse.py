from dataclasses import FrozenInstanceError

import pytest

from uritpl.fault import Failure, Fault
from uritpl.model import FORMS, Expression, Literal, Varspec
from uritpl.parse import parse_template, read_template


def test_model_records_are_frozen_and_forms_are_exact():
    assert FORMS == {
        "": "simple",
        "+": "reserved",
        "#": "fragment",
        ".": "label",
        "/": "path",
        ";": "parameter",
        "?": "query",
        "&": "continuation",
    }
    records = [Varspec("a", "", 0, 1), Literal("x", 1), Expression("", (), 1, "{}")]
    for record in records:
        with pytest.raises(FrozenInstanceError):
            record.col = 2


@pytest.mark.parametrize(
    ("operator", "source", "spec_col"),
    [
        ("", "{a}", 2),
        ("+", "{+a}", 3),
        ("#", "{#a}", 3),
        (".", "{.a}", 3),
        ("/", "{/a}", 3),
        (";", "{;a}", 3),
        ("?", "{?a}", 3),
        ("&", "{&a}", 3),
    ],
)
def test_every_operator_preserves_expression_and_specification(operator, source, spec_col):
    assert parse_template(source) == [
        Expression(operator, (Varspec("a", "", 0, spec_col),), 1, source)
    ]


def test_templates_preserve_literal_segments_sources_and_codepoint_columns():
    assert parse_template("") == []
    assert parse_template("abc") == [Literal("abc", 1)]
    assert parse_template("😀{x}é{/y}z") == [
        Literal("😀", 1),
        Expression("", (Varspec("x", "", 0, 3),), 2, "{x}"),
        Literal("é", 5),
        Expression("/", (Varspec("y", "", 0, 8),), 6, "{/y}"),
        Literal("z", 10),
    ]
    assert parse_template("{%41:2,b_9*}") == [
        Expression(
            "",
            (Varspec("%41", "prefix", 2, 2), Varspec("b_9", "explode", 0, 8)),
            1,
            "{%41:2,b_9*}",
        )
    ]


@pytest.mark.parametrize(
    ("template", "code", "col", "arg", "message"),
    [
        ("{a", "UT001", 1, "", "unclosed expression"),
        ("x{a}}", "UT002", 5, "", 'unmatched "}"'),
        ("{}", "UT003", 1, "", "empty expression"),
        ("{+}", "UT003", 1, "", "empty expression"),
        ("{=a}", "UT004", 2, "=", 'reserved operator "="'),
        ("{,a}", "UT004", 2, ",", 'reserved operator ","'),
        ("{!a}", "UT004", 2, "!", 'reserved operator "!"'),
        ("{@a}", "UT004", 2, "@", 'reserved operator "@"'),
        ("{|a}", "UT004", 2, "|", 'reserved operator "|"'),
        ("{ a}", "UT005", 2, "", "bad variable name"),
        ("{a,}", "UT005", 4, "", "bad variable name"),
        ("{a,,b}", "UT005", 4, "", "bad variable name"),
        ("{.a}{/.b}", "UT005", 7, "", "bad variable name"),
        ("{%4}", "UT005", 2, "", "bad variable name"),
        ("{a }", "UT005", 2, "", "bad variable name"),
        ("{a:}", "UT006", 3, "", "bad modifier"),
        ("{a:0}", "UT006", 3, "", "bad modifier"),
        ("{a:05}", "UT006", 3, "", "bad modifier"),
        ("{a:٣}", "UT006", 3, "", "bad modifier"),
        ("{a*b}", "UT006", 3, "", "bad modifier"),
        ("{a:3*}", "UT006", 3, "", "bad modifier"),
        ("{a{b}", "UT005", 2, "", "bad variable name"),
        ("ab{c,d:0}", "UT006", 7, "", "bad modifier"),
    ],
)
def test_template_faults_and_read_template_messages(template, code, col, arg, message):
    with pytest.raises(Fault) as error:
        parse_template(template)
    assert (error.value.code, error.value.col, error.value.arg, error.value.text) == (
        code,
        col,
        arg,
        message,
    )
    with pytest.raises(Failure) as failure:
        read_template(template)
    assert failure.value.message == f"template:{col}: {code} {message}"


def test_parsing_stops_at_first_fault_and_checks_unclosed_before_body():
    with pytest.raises(Fault) as error:
        parse_template("{a:0,b*}")
    assert (error.value.code, error.value.col) == ("UT006", 3)

    with pytest.raises(Fault) as error:
        parse_template("x{a:0}{b:0}")
    assert (error.value.code, error.value.col) == ("UT006", 4)

    with pytest.raises(Fault) as error:
        parse_template("{a:0")
    assert (error.value.code, error.value.col) == ("UT001", 1)


def test_read_template_returns_parsed_items_and_rejects_surrogates_before_syntax():
    assert read_template("x{%41:2}{/y*}") == [
        Literal("x", 1),
        Expression("", (Varspec("%41", "prefix", 2, 3),), 2, "{%41:2}"),
        Expression("/", (Varspec("y", "explode", 0, 11),), 9, "{/y*}"),
    ]
    for argument, expected in [
        ("\ud800{", 'invalid text "?{"'),
        ("\udfff}", 'invalid text "?}"'),
    ]:
        with pytest.raises(Failure) as error:
            read_template(argument)
        assert error.value.message == expected
