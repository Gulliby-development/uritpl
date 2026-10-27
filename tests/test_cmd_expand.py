import pytest

from uritpl.cmd_expand import USAGE as EXPAND_USAGE
from uritpl.cmd_expand import run_expand
from uritpl.cmd_trace import USAGE as TRACE_USAGE
from uritpl.cmd_trace import run_trace
from uritpl.fault import Failure
from uritpl.io import MemIo

_ADAPTERS = [
    (run_expand, EXPAND_USAGE, "expand [--strict] TEMPLATE VARS"),
    (run_trace, TRACE_USAGE, "trace [--strict] [--only=N] TEMPLATE VARS"),
]


def _memory(json_text: str | None = "{}") -> MemIo:
    files = {} if json_text is None else {"v.json": json_text.encode("utf-8")}
    return MemIo(files=files)


@pytest.mark.parametrize(("run", "exported_usage", "expected_usage"), _ADAPTERS)
def test_usage_arity_and_option_validation(run, exported_usage, expected_usage) -> None:
    assert exported_usage == expected_usage

    for args in ([], ["{a}"], ["{a}", "v.json", "w.json"]):
        with pytest.raises(Failure) as error:
            run(args, _memory())
        assert error.value.message == f"usage: {expected_usage}"

    for args, message in (
        (["--oops"], 'unknown option "--oops"'),
        (["--bad", "--worse"], 'unknown option "--bad"'),
        (["--"], 'unknown option "--"'),
        (["--help"], 'unknown option "--help"'),
        (["--strict=1"], 'unknown option "--strict=1"'),
    ):
        with pytest.raises(Failure) as error:
            run(args, _memory())
        assert error.value.message == message

    for args in (
        ["--strict", "{a}", "--strict", "v.json"],
        ["{a}", "v.json", "--strict"],
    ):
        io = _memory('{"a":"1"}')
        assert run(args, io) == 0
        assert io.stderr == ""
        if run is run_expand:
            assert io.stdout == "1"
        else:
            assert io.stdout == 'N  EXPRESSION  RESULT\n1  "{a}"       "1"\n'

    io = _memory()
    assert run(["-x", "v.json"], io) == 0
    assert io.stderr == ""
    assert io.stdout == ("-x" if run is run_expand else "")


@pytest.mark.parametrize("run", [run_expand, run_trace])
@pytest.mark.parametrize(
    ("args", "files", "stdin", "message"),
    [
        (
            ["{a", "missing.json"],
            {},
            b"",
            "template:1: UT001 unclosed expression",
        ),
        (
            ["a\ud800", "missing.json"],
            {},
            b"",
            'invalid text "a?"',
        ),
        (
            ["{a}", "missing\u200bé.json"],
            {},
            b"",
            "missing??.json: cannot read the file",
        ),
        (
            ["{a}", "v.json"],
            {"v.json": b"{\xff}"},
            b"",
            "v.json: input is not valid UTF-8",
        ),
        (
            ["--strict", "{missing}", "v.json"],
            {"v.json": b'{"a":1}'},
            b"",
            'v.json: variable "a": unsupported value',
        ),
        (
            ["/static", "v.json"],
            {"v.json": b""},
            b"",
            "v.json: not valid JSON",
        ),
        (
            ["", "missing.json"],
            {},
            b"",
            "missing.json: cannot read the file",
        ),
        (
            ["{a}", "-"],
            {},
            b'{"a":1}',
            '<stdin>: variable "a": unsupported value',
        ),
    ],
)
def test_template_and_input_failure_precedence(run, args, files, stdin, message) -> None:
    io = MemIo(stdin=stdin, files=files)
    with pytest.raises(Failure) as error:
        run(args, io)
    assert error.value.message == message
    assert io.stdout == ""
    assert io.stderr == ""


@pytest.mark.parametrize("run", [run_expand, run_trace])
@pytest.mark.parametrize(
    ("args", "json_text", "message"),
    [
        (["--strict", "{a}"], "{}", 'undefined variable "a"'),
        (["--strict", "{a}"], '{"a":null}', 'undefined variable "a"'),
        (["--strict", "{a}"], '{"a":[]}', 'undefined variable "a"'),
        (["--strict", "{a}"], '{"a":{}}', 'undefined variable "a"'),
        (["--strict", "{a,b}"], '{"a":"1"}', 'undefined variable "b"'),
        (
            ["--strict", "--strict", "{a}{b}{c}"],
            '{"a":"1","b":null}',
            'undefined variable "b"',
        ),
        (
            ["--strict", "{a:2}{b}"],
            '{"a":["x"]}',
            'variable "a": prefix modifier on a list value',
        ),
        (
            ["--strict", "{b}{a:2}"],
            '{"a":["x"]}',
            'undefined variable "b"',
        ),
        (
            ["{/b}{/a:2}"],
            '{"a":{"k":"v"}}',
            'variable "a": prefix modifier on an object value',
        ),
        (
            ["{?x,a:2,b}"],
            '{"x":"1","a":["x"]}',
            'variable "a": prefix modifier on a list value',
        ),
    ],
)
def test_strictness_and_expansion_failure_order(run, args, json_text, message) -> None:
    io = _memory(json_text)
    with pytest.raises(Failure) as error:
        run([*args, "v.json"], io)
    assert error.value.message == message
    assert io.stdout == ""
    assert io.stderr == ""


@pytest.mark.parametrize("run", [run_expand, run_trace])
@pytest.mark.parametrize(
    "json_text",
    [
        "{}",
        '{"a":null}',
        '{"a":[]}',
        '{"a":{}}',
    ],
)
def test_undefined_values_are_skipped_by_default(run, json_text) -> None:
    io = _memory(json_text)
    assert run(["{a}", "v.json"], io) == 0
    assert io.stderr == ""
    if run is run_expand:
        assert io.stdout == ""
    else:
        assert io.stdout == 'N  EXPRESSION  RESULT\n1  "{a}"       ""\n'


@pytest.mark.parametrize("run", [run_expand, run_trace])
def test_strict_accepts_defined_empty_string_and_reads_stdin_bom(run) -> None:
    io = MemIo(stdin=b'\xef\xbb\xbf{"a":"x"}')
    assert run(["--strict", "{a}", "-"], io) == 0
    assert io.stderr == ""
    if run is run_expand:
        assert io.stdout == "x"
    else:
        assert io.stdout == 'N  EXPRESSION  RESULT\n1  "{a}"       "x"\n'

    empty_io = _memory('{"a":""}')
    assert run(["--strict", "{/a}", "v.json"], empty_io) == 0
    assert empty_io.stderr == ""
    if run is run_expand:
        assert empty_io.stdout == "/"
    else:
        assert empty_io.stdout == 'N  EXPRESSION  RESULT\n1  "{/a}"      "/"\n'


@pytest.mark.parametrize(
    ("template", "json_text", "expected"),
    [
        ("", "{}", ""),
        ("/a/b?c=d#e", "{}", "/a/b?c=d#e"),
        ("a\rb", "{}", "a%0Db"),
        (
            "/users{/id}{?q,page}",
            '{"id":"42","q":"a b"}',
            "/users/42?q=a%20b",
        ),
        ("{x:2}", '{"x":"é😀ab"}', "%C3%A9%F0%9F%98%80"),
        ("{+x:2}", '{"x":"%41%42"}', "%254"),
        ("{/a,b}", '{"a":"","b":"x"}', "//x"),
    ],
)
def test_expand_output_is_exact_and_has_no_added_lf(template, json_text, expected) -> None:
    io = _memory(json_text)
    assert run_expand([template, "v.json"], io) == 0
    assert io.stdout == expected
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("template", "json_text", "expected"),
    [
        (
            "/users{/id}{?q,page}",
            '{"id":"42","q":"a b"}',
            'N  EXPRESSION   RESULT\n1  "{/id}"      "/42"\n2  "{?q,page}"  "?q=a%20b"\n',
        ),
        (
            "/a{/b}x{c}",
            '{"b":"1"}',
            'N  EXPRESSION  RESULT\n1  "{/b}"      "/1"\n2  "{c}"       ""\n',
        ),
        ("/static", "{}", ""),
        ("", "{}", ""),
    ],
)
def test_trace_table_alignment_and_empty_templates(template, json_text, expected) -> None:
    io = _memory(json_text)
    assert run_trace([template, "v.json"], io) == 0
    assert io.stdout == expected
    assert io.stderr == ""


@pytest.mark.parametrize("run", [run_expand, run_trace])
def test_late_strict_failure_is_atomic(run) -> None:
    io = _memory('{"a":"1"}')
    with pytest.raises(Failure) as error:
        run(["--strict", "{a}{b}", "v.json"], io)
    assert error.value.message == 'undefined variable "b"'
    assert io.stdout == ""
    assert io.stderr == ""
