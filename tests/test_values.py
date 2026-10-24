import json
from unittest.mock import Mock

import pytest

from uritpl.fault import Failure
from uritpl.io import Inputs, MemIo
from uritpl.load import load_variables
from uritpl.value import Value, is_undefined, kind_of


def _source(text: str):
    io = MemIo(files={"v.json": text.encode("utf-8")})
    return Inputs(io).read("v.json"), io


def _classification_with_memio(value, classify):
    io = MemIo()
    result = classify(value)
    return result, io


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ([], True),
        ({}, True),
        ("", False),
        ("x", False),
        ([""], False),
        ({"k": ""}, False),
    ],
)
def test_is_undefined_boundaries(value, expected):
    result, io = _classification_with_memio(value, is_undefined)
    assert result is expected
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", "string"),
        ("é😀", "string"),
        ([], "list"),
        (["x"], "list"),
        ({}, "object"),
        ({"k": "v"}, "object"),
    ],
)
def test_kind_of_supported_values(value, expected):
    result, io = _classification_with_memio(value, kind_of)
    assert result == expected
    assert io.stdout == io.stderr == ""


def test_value_union_and_supported_values():
    assert Value == str | list[str] | dict[str, str]
    source, io = _source(
        '{"a":"","b":["x","","y/z"],"c":{"k":"1","e":""},"none":null,"nolist":[],"noobj":{}}'
    )
    variables = load_variables(source)
    assert variables == {
        "a": "",
        "b": ["x", "", "y/z"],
        "c": {"k": "1", "e": ""},
        "nolist": [],
        "noobj": {},
    }
    assert list(variables) == ["a", "b", "c", "nolist", "noobj"]
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('\ufeff{"u":"\u200b"}', {"u": "\u200b"}),
        (' \r\n\t{"a":\t"x"}\r\n', {"a": "x"}),
        (
            '{"u":"é😀\\ufeff\\u200b\\u00a0\\u0085\\u2028\\u2029\\u3000",'
            + '"a b":"x","":"y","%41":"p","A":"q"}',
            {
                "u": "é😀\ufeff\u200b\u00a0\u0085\u2028\u2029\u3000",
                "a b": "x",
                "": "y",
                "%41": "p",
                "A": "q",
            },
        ),
        ('{"a":"\\ud83d\\ude00"}', {"a": "😀"}),
    ],
)
def test_json_strings_bom_whitespace_and_unicode(text, expected):
    source, io = _source(text)
    assert load_variables(source) == expected
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("text", "expected", "keys"),
    [
        ('{"b":"old","a":"A","b":"B"}', {"b": "B", "a": "A"}, ["b", "a"]),
        ('{"a":1,"a":"x"}', {"a": "x"}, ["a"]),
        ('{"a":"x","a":null}', {}, []),
        ('{"a":"\\ud800","a":"x"}', {"a": "x"}, ["a"]),
    ],
)
def test_duplicate_members_keep_first_position_and_last_value(text, expected, keys):
    source, io = _source(text)
    variables = load_variables(source)
    assert variables == expected
    assert list(variables) == keys
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("text", "expected", "keys"),
    [
        ('{"a":{"z":"old","k":"K","z":"Z"}}', {"z": "Z", "k": "K"}, ["z", "k"]),
        ('{"a":{"k":1,"k":"v"}}', {"k": "v"}, ["k"]),
    ],
)
def test_nested_duplicate_members_keep_first_position_and_last_value(text, expected, keys):
    source, io = _source(text)
    variables = load_variables(source)
    assert list(variables) == ["a"]
    assert variables["a"] == expected
    assert list(variables["a"]) == keys
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    "text",
    [
        "",
        '{"a":"x",}',
        "{'a':'x'}",
        '{"a":NaN}',
        '{"a":Infinity}',
        '{"a":-Infinity}',
        '{"a":01}',
        '{"a":"x"} {}',
        "/*x*/{}",
        '{"a":"\t"}',
        "\u00a0{}",
        "\ufeff\ufeff{}",
    ],
)
def test_invalid_json_has_exact_failure(text):
    source, io = _source(text)
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == "v.json: not valid JSON"
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize("text", ["[]", "null", "true", "0", "-12", "1.5", "1e3", '"x"'])
def test_valid_non_object_documents_have_exact_failure(text):
    source, io = _source(text)
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == "v.json: variables must be a JSON object"
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    "text",
    [
        '{"a":1}',
        '{"a":true}',
        '{"a":false}',
        '{"a":1.5}',
        '{"a":1e9999}',
        '{"a":["b",1]}',
        '{"a":[null]}',
        '{"a":[[]]}',
        '{"a":{"k":["v"]}}',
        '{"a":{"k":null}}',
        '{"a":0,"a":1}',
    ],
)
def test_unsupported_retained_values_have_exact_failure(text):
    source, io = _source(text)
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == 'v.json: variable "a": unsupported value'
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('{"b":1,"a":2}', 'v.json: variable "b": unsupported value'),
        (
            '{"b":"ok","a":2,"b":1}',
            'v.json: variable "b": unsupported value',
        ),
        (
            '{"a":[1,"\\ud800"]}',
            'v.json: variable "a": unsupported value',
        ),
        (
            '{"a":{"k":1,"\\ud800":"x"}}',
            'v.json: variable "a": unsupported value',
        ),
        ('{"a":1,}', "v.json: not valid JSON"),
    ],
)
def test_validation_follows_retained_member_and_parse_precedence(text, message):
    source, io = _source(text)
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == message
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('{"a":"\\ud800"}', 'v.json: variable "a": invalid text'),
        ('{"a":"\\udfff"}', 'v.json: variable "a": invalid text'),
        ('{"a":["\\ud800"]}', 'v.json: variable "a": invalid text'),
        ('{"a":["\\ud800",1]}', 'v.json: variable "a": invalid text'),
        ('{"a":{"k":"\\ud800"}}', 'v.json: variable "a": invalid text'),
        ('{"é\\ud800":"x"}', 'v.json: variable "??": invalid text'),
        ('{"\\ud800":1}', 'v.json: variable "?": invalid text'),
        ('{"a":{"\\ud800":1}}', 'v.json: variable "a": invalid text'),
    ],
)
def test_retained_surrogates_are_rejected(text, message):
    source, io = _source(text)
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == message
    assert io.stdout == io.stderr == ""


def test_stdin_source_uses_stdin_display_and_keeps_errors_unprefixed():
    io = MemIo(stdin=b'{"a":1}')
    source = Inputs(io).read("-")
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == '<stdin>: variable "a": unsupported value'
    assert io.stdout == io.stderr == ""


@pytest.mark.parametrize("exception", [ValueError, RecursionError, MemoryError, OverflowError])
def test_excessive_parser_failures_become_invalid_json(monkeypatch, exception):
    source, io = _source("{}")
    monkeypatch.setattr(json, "loads", Mock(side_effect=exception("parser failure")))
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == "v.json: not valid JSON"
    assert io.stdout == io.stderr == ""


def test_parser_failure_uses_source_display_name(monkeypatch):
    io = MemIo(files={"DISPLAY": b"{}"})
    source = Inputs(io).read("DISPLAY")
    monkeypatch.setattr(json, "loads", Mock(side_effect=RecursionError("parser failure")))
    with pytest.raises(Failure) as error:
        load_variables(source)
    assert error.value.message == "DISPLAY: not valid JSON"
    assert io.stdout == io.stderr == ""
