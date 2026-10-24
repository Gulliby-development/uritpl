import pytest

from uritpl.expand import expand_expression, expand_template, trace_template
from uritpl.fault import Failure
from uritpl.io import Inputs, MemIo
from uritpl.load import load_variables
from uritpl.operators import OPERATORS
from uritpl.parse import parse_template
from uritpl.varexp import expand_varspec


def _parse(text: str):
    source = Inputs(MemIo(stdin=text.encode("utf-8"))).read("-")
    return parse_template(source.text)


def _load_variables(text: str):
    source = Inputs(MemIo(stdin=text.encode("utf-8"))).read("-")
    return load_variables(source)


@pytest.mark.parametrize(
    ("template", "variables", "expected"),
    [
        ("{x:3}", {"x": "abcdef"}, "abc"),
        ("{x:9}", {"x": "ab"}, "ab"),
        ("{;x:2}", {"x": ""}, ";x"),
        ("{x:2}", {"x": "é😀ab"}, "%C3%A9%F0%9F%98%80"),
        ("{+x:3}", {"x": "%41%42"}, "%41"),
        ("{+x:2}", {"x": "%41%42"}, "%254"),
        ("{x*}", {"x": "a/b"}, "a%2Fb"),
    ],
)
def test_prefix_and_explode_expansion(
    template: str, variables: dict[str, object], expected: str
) -> None:
    assert expand_template(_parse(template), variables, False) == expected


@pytest.mark.parametrize(
    ("template", "variables", "expected"),
    [
        ("", {}, ""),
        ("{#x}", {}, ""),
        ("{?x}", {"x": []}, ""),
        ("{/x}", {"x": {}}, ""),
        ("{/a,b}", {"a": "", "b": "x"}, "//x"),
        ("{/a,b}", {"b": "x"}, "/x"),
        ("{?a,b}", {"a": None, "b": ""}, "?b="),
        ("{;a,b}", {"a": "1", "b": ""}, ";a=1;b"),
        ("{x.y}{%41}", {"x.y": "1", "%41": "p", "A": "q"}, "1p"),
        ("{#x}", {"x": ""}, "#"),
    ],
)
def test_template_composition_and_undefined_values(
    template: str, variables: dict[str, object], expected: str
) -> None:
    assert (
        expand_template(_parse(template), variables, template == "{#x}" and variables == {"x": ""})
        == expected
    )


def test_expand_expression_composes_specifications() -> None:
    items = _parse("{/a,b}")
    assert expand_expression(items[0], {"a": "", "b": "x"}, False) == "//x"
    query = _parse("{?a,b}")
    assert expand_expression(query[0], {"a": None, "b": ""}, False) == "?b="


@pytest.mark.parametrize(
    ("template", "variables", "strict", "message", "expression_index"),
    [
        ("{a:2}", {"a": ["x", "y"]}, False, 'variable "a": prefix modifier on a list value', 0),
        (
            "{b}{/a:2}",
            {"a": {"k": "v"}},
            False,
            'variable "a": prefix modifier on an object value',
            1,
        ),
        (
            "{?x,a:2,b}",
            {"x": "1", "a": ["x"]},
            False,
            'variable "a": prefix modifier on a list value',
            0,
        ),
        ("{a,b}", {"a": "1"}, True, 'undefined variable "b"', 0),
        ("{a}{b}{c}", {"a": "1", "b": None}, True, 'undefined variable "b"', 1),
        ("{a:2}{b}", {"a": ["x"]}, True, 'variable "a": prefix modifier on a list value', 0),
        ("{b,a:2}", {"a": ["x"]}, True, 'undefined variable "b"', 0),
        ("{x:2}", {"x": []}, True, 'undefined variable "x"', 0),
        ("{x}", {"x": {}}, True, 'undefined variable "x"', 0),
    ],
)
def test_expansion_failure_precedence(
    template: str,
    variables: dict[str, object],
    strict: bool,
    message: str,
    expression_index: int,
) -> None:
    memory = MemIo(stdin=template.encode("utf-8"))
    source = Inputs(memory).read("-")
    items = parse_template(source.text)
    with pytest.raises(Failure) as expand_error:
        expand_template(items, variables, strict)
    assert expand_error.value.message == message
    assert memory.stdout == ""
    assert memory.stderr == ""

    with pytest.raises(Failure) as trace_error:
        trace_template(items, variables, strict)
    assert trace_error.value.message == message
    assert memory.stdout == ""
    assert memory.stderr == ""

    expression = items[expression_index]
    with pytest.raises(Failure) as expression_error:
        expand_expression(expression, variables, strict)
    assert expression_error.value.message == message

    if "prefix modifier on a list value" in message:
        spec = expression.specs[1] if template == "{?x,a:2,b}" else expression.specs[0]
        with pytest.raises(Failure) as contribution_error:
            expand_varspec(OPERATORS[expression.op], spec, variables[spec.name])
        assert contribution_error.value.message == message
    if "prefix modifier on an object value" in message:
        spec = expression.specs[0]
        with pytest.raises(Failure) as contribution_error:
            expand_varspec(OPERATORS[expression.op], spec, variables[spec.name])
        assert contribution_error.value.message == message


@pytest.mark.parametrize(
    ("template", "variables", "expected"),
    [
        ("/a/b?c=d#e", {}, "/a/b?c=d#e"),
        ("%41%4 %2f", {}, "%41%254%20%2f"),
        ("a\ufeffb", {}, "a%EF%BB%BFb"),
        ("a\u200bb", {}, "a%E2%80%8Bb"),
        ("a\u00a0b", {}, "a%C2%A0b"),
        ("a\rb", {}, "a%0Db"),
        ("\r", {}, "%0D"),
        ("a\u0085\u2028\u2029\u3000b", {}, "a%C2%85%E2%80%A8%E2%80%A9%E3%80%80b"),
        ('a"b<c>d\\e^f', {}, "a%22b%3Cc%3Ed%5Ce%5Ef"),
        ("{u}", {"u": "\ufeff\u200b\u00a0"}, "%EF%BB%BF%E2%80%8B%C2%A0"),
        ("{+u}", {"u": "a\rb"}, "a%0Db"),
        (
            "{;u*}",
            {"u": ["\ufeff", "", "\u00a0"]},
            ";u=%EF%BB%BF;u;u=%C2%A0",
        ),
        (
            "{/u*}",
            {"u": {"\u200b": "\u00a0", "k": ""}},
            "/%E2%80%8B=%C2%A0/k=",
        ),
    ],
)
def test_template_literal_and_value_unicode(
    template: str, variables: dict[str, object], expected: str
) -> None:
    assert expand_template(_parse(template), variables, False) == expected


@pytest.mark.parametrize(
    ("template", "variables", "expected"),
    [
        (
            "/users{/id}{?q,page}",
            {"id": "42", "q": "a b"},
            [("{/id}", "/42"), ("{?q,page}", "?q=a%20b")],
        ),
        ("/a{/b}x{c}", {"b": "1"}, [("{/b}", "/1"), ("{c}", "")]),
        ("/static", {}, []),
        (
            "{+%41}{x:2}",
            {"%41": "%2f", "x": "é😀a"},
            [("{+%41}", "%2f"), ("{x:2}", "%C3%A9%F0%9F%98%80")],
        ),
    ],
)
def test_trace_returns_expression_source_and_result(
    template: str, variables: dict[str, object], expected: list[tuple[str, str]]
) -> None:
    assert trace_template(_parse(template), variables, False) == expected


def test_loaded_json_preserves_first_key_order_and_last_values() -> None:
    ordered = _load_variables('{"x":{"z":"1","a":"2","z":"3"}}')
    assert expand_template(_parse("{?x*}"), ordered, False) == "?z=3&a=2"

    duplicate_value = _load_variables('{"x":"1","x":"2"}')
    assert expand_template(_parse("{x}"), duplicate_value, False) == "2"

    omitted_null = _load_variables('{"x":"1","x":null}')
    assert expand_template(_parse("{x}"), omitted_null, False) == ""
