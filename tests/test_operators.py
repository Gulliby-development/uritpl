from dataclasses import FrozenInstanceError, fields

import pytest

from uritpl.expand import expand_template
from uritpl.fault import Failure
from uritpl.io import Inputs, MemIo
from uritpl.load import load_variables
from uritpl.operators import OPERATORS, Operator
from uritpl.parse import parse_template
from uritpl.value import Value
from uritpl.varexp import expand_varspec
from uritpl.varspec import parse_varspec


def _mem_io(text: str) -> MemIo:
    return MemIo(stdin=text.encode("utf-8"))


def acceptance_actual(input: str) -> str:
    io = MemIo(
        files={
            "v.json": b'{"empty": "", "str": "a b/c", "list": ["x", "", "y/z"], "obj": {"k": "1", "e": "", "s": ";"}, "none": null, "nolist": [], "noobj": {}}'
        }
    )
    variables = load_variables(Inputs(io).read("v.json"))
    return expand_template(parse_template(input), variables, strict=False)


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{empty}", ""),
        ("{str}", "a%20b%2Fc"),
        ("{list}", "x,,y%2Fz"),
        ("{list*}", "x,,y%2Fz"),
        ("{obj}", "k,1,e,,s,%3B"),
        ("{obj*}", "k=1,e=,s=%3B"),
        ("{+empty}", ""),
        ("{+str}", "a%20b/c"),
        ("{+list}", "x,,y/z"),
        ("{+list*}", "x,,y/z"),
        ("{+obj}", "k,1,e,,s,;"),
        ("{+obj*}", "k=1,e=,s=;"),
        ("{#empty}", "#"),
        ("{#str}", "#a%20b/c"),
        ("{#list}", "#x,,y/z"),
        ("{#list*}", "#x,,y/z"),
        ("{#obj}", "#k,1,e,,s,;"),
        ("{#obj*}", "#k=1,e=,s=;"),
        ("{.empty}", "."),
        ("{.str}", ".a%20b%2Fc"),
        ("{.list}", ".x,,y%2Fz"),
        ("{.list*}", ".x..y%2Fz"),
        ("{.obj}", ".k,1,e,,s,%3B"),
        ("{.obj*}", ".k=1.e=.s=%3B"),
        ("{/empty}", "/"),
        ("{/str}", "/a%20b%2Fc"),
        ("{/list}", "/x,,y%2Fz"),
        ("{/list*}", "/x//y%2Fz"),
        ("{/obj}", "/k,1,e,,s,%3B"),
        ("{/obj*}", "/k=1/e=/s=%3B"),
        ("{;empty}", ";empty"),
        ("{;str}", ";str=a%20b%2Fc"),
        ("{;list}", ";list=x,,y%2Fz"),
        ("{;list*}", ";list=x;list;list=y%2Fz"),
        ("{;obj}", ";obj=k,1,e,,s,%3B"),
        ("{;obj*}", ";k=1;e;s=%3B"),
        ("{?empty}", "?empty="),
        ("{?str}", "?str=a%20b%2Fc"),
        ("{?list}", "?list=x,,y%2Fz"),
        ("{?list*}", "?list=x&list=&list=y%2Fz"),
        ("{?obj}", "?obj=k,1,e,,s,%3B"),
        ("{?obj*}", "?k=1&e=&s=%3B"),
        ("{&empty}", "&empty="),
        ("{&str}", "&str=a%20b%2Fc"),
        ("{&list}", "&list=x,,y%2Fz"),
        ("{&list*}", "&list=x&list=&list=y%2Fz"),
        ("{&obj}", "&obj=k,1,e,,s,%3B"),
        ("{&obj*}", "&k=1&e=&s=%3B"),
    ],
)
def test_operator_value_acceptance_matrix(template: str, expected: str) -> None:
    assert acceptance_actual(template) == expected


@pytest.mark.parametrize(
    ("symbol", "first", "sep", "named", "ifemp", "allow_reserved"),
    [
        ("", "", ",", False, "", False),
        ("+", "", ",", False, "", True),
        ("#", "#", ",", False, "", True),
        (".", ".", ".", False, "", False),
        ("/", "/", "/", False, "", False),
        (";", ";", ";", True, "", False),
        ("?", "?", "&", True, "=", False),
        ("&", "&", "&", True, "=", False),
    ],
)
def test_operator_record_properties(
    symbol: str, first: str, sep: str, named: bool, ifemp: str, allow_reserved: bool
) -> None:
    assert OPERATORS[symbol] == Operator(symbol, first, sep, named, ifemp, allow_reserved)


def test_operator_record_shape_and_frozen() -> None:
    assert tuple(field.name for field in fields(Operator)) == (
        "symbol",
        "first",
        "sep",
        "named",
        "ifemp",
        "allow_reserved",
    )
    assert set(OPERATORS) == {"", "+", "#", ".", "/", ";", "?", "&"}
    with pytest.raises(FrozenInstanceError):
        OPERATORS[""].symbol = "changed"


@pytest.mark.parametrize(
    ("symbol", "spec_text", "value", "expected"),
    [
        ("/", "x*", ["", "a", ""], ["", "a", ""]),
        (";", "x", [""], ["x="]),
        (";", "x*", [""], ["x"]),
        ("?", "x*", [""], ["x="]),
        (";", "x", {"": ""}, ["x=,"]),
        (";", "x*", {"": ""}, [""]),
        ("/", "x*", {"": ""}, ["="]),
        ("?", "%41", "v", ["%41=v"]),
        ("+", "x*", "a/b", ["a/b"]),
        ("?", "x*", {"a b": "x/y"}, ["a%20b=x%2Fy"]),
    ],
)
def test_named_and_empty_contribution_examples(
    symbol: str, spec_text: str, value: Value, expected: list[str]
) -> None:
    spec_source = Inputs(_mem_io(spec_text)).read("-").text
    spec = parse_varspec(spec_source, 0)
    assert expand_varspec(OPERATORS[symbol], spec, value) == expected


@pytest.mark.parametrize(
    ("symbol", "spec_text", "value", "expected"),
    [
        ("", "x", "a b/c", ["a%20b%2Fc"]),
        ("+", "x", "a b/c", ["a%20b/c"]),
        ("#", "x", "a b/c", ["a%20b/c"]),
        (".", "x", "a b/c", ["a%20b%2Fc"]),
        ("/", "x", "a b/c", ["a%20b%2Fc"]),
        (";", "x", "a b/c", ["x=a%20b%2Fc"]),
        ("?", "x", "a b/c", ["x=a%20b%2Fc"]),
        ("&", "x", "a b/c", ["x=a%20b%2Fc"]),
        ("", "x", ["x", "", "y/z"], ["x,,y%2Fz"]),
        ("+", "x", ["x", "", "y/z"], ["x,,y/z"]),
        ("#", "x", ["x", "", "y/z"], ["x,,y/z"]),
        (".", "x", ["x", "", "y/z"], ["x,,y%2Fz"]),
        ("/", "x", ["x", "", "y/z"], ["x,,y%2Fz"]),
        (";", "x", ["x", "", "y/z"], ["x=x,,y%2Fz"]),
        ("?", "x", ["x", "", "y/z"], ["x=x,,y%2Fz"]),
        ("&", "x", ["x", "", "y/z"], ["x=x,,y%2Fz"]),
        ("", "x*", ["x", "", "y/z"], ["x", "", "y%2Fz"]),
        ("+", "x*", ["x", "", "y/z"], ["x", "", "y/z"]),
        ("#", "x*", ["x", "", "y/z"], ["x", "", "y/z"]),
        (".", "x*", ["x", "", "y/z"], ["x", "", "y%2Fz"]),
        ("/", "x*", ["x", "", "y/z"], ["x", "", "y%2Fz"]),
        (";", "x*", ["x", "", "y/z"], ["x=x", "x", "x=y%2Fz"]),
        ("?", "x*", ["x", "", "y/z"], ["x=x", "x=", "x=y%2Fz"]),
        ("&", "x*", ["x", "", "y/z"], ["x=x", "x=", "x=y%2Fz"]),
        ("", "x", {"k": "1", "e": "", "s": ";"}, ["k,1,e,,s,%3B"]),
        ("+", "x", {"k": "1", "e": "", "s": ";"}, ["k,1,e,,s,;"]),
        ("#", "x", {"k": "1", "e": "", "s": ";"}, ["k,1,e,,s,;"]),
        (".", "x", {"k": "1", "e": "", "s": ";"}, ["k,1,e,,s,%3B"]),
        ("/", "x", {"k": "1", "e": "", "s": ";"}, ["k,1,e,,s,%3B"]),
        (";", "x", {"k": "1", "e": "", "s": ";"}, ["x=k,1,e,,s,%3B"]),
        ("?", "x", {"k": "1", "e": "", "s": ";"}, ["x=k,1,e,,s,%3B"]),
        ("&", "x", {"k": "1", "e": "", "s": ";"}, ["x=k,1,e,,s,%3B"]),
        ("", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=%3B"]),
        ("+", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=;"]),
        ("#", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=;"]),
        (".", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=%3B"]),
        ("/", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=%3B"]),
        (";", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e", "s=%3B"]),
        ("?", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=%3B"]),
        ("&", "x*", {"k": "1", "e": "", "s": ";"}, ["k=1", "e=", "s=%3B"]),
    ],
)
def test_defined_contributions_for_each_operator_shape(
    symbol: str, spec_text: str, value: Value, expected: list[str]
) -> None:
    spec_source = Inputs(_mem_io(spec_text)).read("-").text
    spec = parse_varspec(spec_source, 0)
    assert expand_varspec(OPERATORS[symbol], spec, value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (["x", "y"], 'variable "a": prefix modifier on a list value'),
        ({"k": "v"}, 'variable "a": prefix modifier on an object value'),
    ],
)
def test_prefix_on_collections_raises_failure(value: Value, message: str) -> None:
    spec_source = Inputs(_mem_io("a:2")).read("-").text
    spec = parse_varspec(spec_source, 0)
    with pytest.raises(Failure) as error:
        expand_varspec(OPERATORS[""], spec, value)
    assert error.value.message == message


# BEGIN acceptance rows: cases from the spec's acceptance table.
# Edit acceptance_actual, not this block.
_acceptance_json = __import__("json")
_acceptance_pytest = __import__("pytest")

_ACCEPTANCE_TEXT = [
    '[{"id":"AC-002:1","input":"{empty}","expected":""},',
    '{"id":"AC-002:2","input":"{str}","expected":"a%20b%2Fc"},',
    '{"id":"AC-002:3","input":"{list}","expected":"x,,y%2Fz"},',
    '{"id":"AC-002:4","input":"{list*}","expected":"x,,y%2Fz"},',
    '{"id":"AC-002:5","input":"{obj}","expected":"k,1,e,,s,%3B"},',
    '{"id":"AC-002:6","input":"{obj*}","expected":"k=1,e=,s=%3B"},',
    '{"id":"AC-002:7","input":"{+empty}","expected":""},',
    '{"id":"AC-002:8","input":"{+str}","expected":"a%20b/c"},',
    '{"id":"AC-002:9","input":"{+list}","expected":"x,,y/z"},',
    '{"id":"AC-002:10","input":"{+list*}","expected":"x,,y/z"},',
    '{"id":"AC-002:11","input":"{+obj}","expected":"k,1,e,,s,;"},',
    '{"id":"AC-002:12","input":"{+obj*}","expected":"k=1,e=,s=;"},',
    '{"id":"AC-002:13","input":"{#empty}","expected":"#"},',
    '{"id":"AC-002:14","input":"{#str}","expected":"#a%20b/c"},',
    '{"id":"AC-002:15","input":"{#list}","expected":"#x,,y/z"},',
    '{"id":"AC-002:16","input":"{#list*}","expected":"#x,,y/z"},',
    '{"id":"AC-002:17","input":"{#obj}","expected":"#k,1,e,,s,;"},',
    '{"id":"AC-002:18","input":"{#obj*}","expected":"#k=1,e=,s=;"},',
    '{"id":"AC-002:19","input":"{.empty}","expected":"."},',
    '{"id":"AC-002:20","input":"{.str}","expected":".a%20b%2Fc"},',
    '{"id":"AC-002:21","input":"{.list}","expected":".x,,y%2Fz"},',
    '{"id":"AC-002:22","input":"{.list*}","expected":".x..y%2Fz"},',
    '{"id":"AC-002:23","input":"{.obj}","expected":".k,1,e,,s,%3B"},',
    '{"id":"AC-002:24","input":"{.obj*}","expected":".k=1.e=.s=%3B"},',
    '{"id":"AC-002:25","input":"{/empty}","expected":"/"},',
    '{"id":"AC-002:26","input":"{/str}","expected":"/a%20b%2Fc"},',
    '{"id":"AC-002:27","input":"{/list}","expected":"/x,,y%2Fz"},',
    '{"id":"AC-002:28","input":"{/list*}","expected":"/x//y%2Fz"},',
    '{"id":"AC-002:29","input":"{/obj}","expected":"/k,1,e,,s,%3B"},',
    '{"id":"AC-002:30","input":"{/obj*}","expected":"/k=1/e=/s=%3B"},',
    '{"id":"AC-002:31","input":"{;empty}","expected":";empty"},',
    '{"id":"AC-002:32","input":"{;str}","expected":";str=a%20b%2Fc"},',
    '{"id":"AC-002:33","input":"{;list}","expected":";list=x,,y%2Fz"},',
    '{"id":"AC-002:34","input":"{;list*}","expected":";list=x;list;list=y%2Fz',
    '"},',
    '{"id":"AC-002:35","input":"{;obj}","expected":";obj=k,1,e,,s,%3B"},',
    '{"id":"AC-002:36","input":"{;obj*}","expected":";k=1;e;s=%3B"},',
    '{"id":"AC-002:37","input":"{?empty}","expected":"?empty="},',
    '{"id":"AC-002:38","input":"{?str}","expected":"?str=a%20b%2Fc"},',
    '{"id":"AC-002:39","input":"{?list}","expected":"?list=x,,y%2Fz"},',
    '{"id":"AC-002:40","input":"{?list*}","expected":"?list=x&list=&list=y%2F',
    'z"},',
    '{"id":"AC-002:41","input":"{?obj}","expected":"?obj=k,1,e,,s,%3B"},',
    '{"id":"AC-002:42","input":"{?obj*}","expected":"?k=1&e=&s=%3B"},',
    '{"id":"AC-002:43","input":"{&empty}","expected":"&empty="},',
    '{"id":"AC-002:44","input":"{&str}","expected":"&str=a%20b%2Fc"},',
    '{"id":"AC-002:45","input":"{&list}","expected":"&list=x,,y%2Fz"},',
    '{"id":"AC-002:46","input":"{&list*}","expected":"&list=x&list=&list=y%2F',
    'z"},',
    '{"id":"AC-002:47","input":"{&obj}","expected":"&obj=k,1,e,,s,%3B"},',
    '{"id":"AC-002:48","input":"{&obj*}","expected":"&k=1&e=&s=%3B"}]',
]
_ACCEPTANCE_ROWS = _acceptance_json.loads("".join(_ACCEPTANCE_TEXT))


@_acceptance_pytest.mark.parametrize(
    "row",
    _ACCEPTANCE_ROWS,
    ids=[row["id"] for row in _ACCEPTANCE_ROWS],
)
def test_acceptance_row(row):
    assert acceptance_actual(row["input"]) == row["expected"]


# END acceptance rows
