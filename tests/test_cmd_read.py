import pytest

from uritpl.cmd_encode import USAGE as ENCODE_USAGE
from uritpl.cmd_encode import run_encode
from uritpl.cmd_explain import USAGE as EXPLAIN_USAGE
from uritpl.cmd_explain import run_explain
from uritpl.cmd_names import USAGE as NAMES_USAGE
from uritpl.cmd_names import run_names
from uritpl.fault import Failure
from uritpl.io import MemIo


def acceptance_actual(input):
    command, args = input
    io = MemIo()
    run_command = {
        "explain": run_explain,
        "names": run_names,
        "encode": run_encode,
    }[command]
    try:
        run_command(args, io)
    except Failure as error:
        assert io.stdout == ""
        assert io.stderr == ""
        return error.message
    raise AssertionError("command unexpectedly succeeded")


# BEGIN acceptance rows: cases from the spec's acceptance table.
# Edit acceptance_actual, not this block.
_acceptance_json = __import__("json")
_acceptance_pytest = __import__("pytest")

_ACCEPTANCE_TEXT = [
    '[{"id":"AC-005:1","input":["explain",["--oops","{"]],"expected":"unknown',
    ' option \\"--oops\\""},',
    '{"id":"AC-005:2","input":["names",["{","extra","--help"]],"expected":"un',
    'known option \\"--help\\""},',
    '{"id":"AC-005:3","input":["encode",["--","--oops"]],"expected":"unknown ',
    'option \\"--\\""},',
    '{"id":"AC-005:4","input":["explain",[]],"expected":"usage: explain TEMPL',
    'ATE"},',
    '{"id":"AC-005:5","input":["explain",["{","extra"]],"expected":"usage: ex',
    'plain TEMPLATE"},',
    '{"id":"AC-005:6","input":["names",[]],"expected":"usage: names TEMPLATE"',
    "},",
    '{"id":"AC-005:7","input":["names",["a\\ud800","extra"]],"expected":"usag',
    'e: names TEMPLATE"},',
    '{"id":"AC-005:8","input":["encode",["--reserved"]],"expected":"usage: en',
    'code [--reserved] TEXT"},',
    '{"id":"AC-005:9","input":["encode",["a\\ud800","extra"]],"expected":"usa',
    'ge: encode [--reserved] TEXT"},',
    '{"id":"AC-005:10","input":["encode",["--reserved=1"]],"expected":"unknow',
    'n option \\"--reserved=1\\""},',
    '{"id":"AC-005:11","input":["explain",["--reserved","{a}"]],"expected":"u',
    'nknown option \\"--reserved\\""},',
    '{"id":"AC-005:12","input":["names",["--reserved","{a}"]],"expected":"unk',
    'nown option \\"--reserved\\""},',
    '{"id":"AC-005:13","input":["encode",["a\\ud800"]],"expected":"invalid te',
    'xt \\"a?\\""},',
    '{"id":"AC-005:14","input":["encode",["--reserved","\\udfff"]],"expected"',
    ':"invalid text \\"?\\""},',
    '{"id":"AC-005:15","input":["explain",["a\\ud800"]],"expected":"invalid t',
    'ext \\"a?\\""},',
    '{"id":"AC-005:16","input":["names",["a\\ud800"]],"expected":"invalid tex',
    't \\"a?\\""}]',
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


def test_public_exports_match_the_command_contract():
    assert EXPLAIN_USAGE == "explain TEMPLATE"
    assert NAMES_USAGE == "names TEMPLATE"
    assert ENCODE_USAGE == "encode [--reserved] TEXT"
    assert callable(run_explain)
    assert callable(run_names)
    assert callable(run_encode)


@pytest.mark.parametrize(
    ("template", "expected_code", "expected_stdout"),
    [
        (
            "{a}{/b:2}",
            0,
            (
                "N  COL  OP  FORM    NAME  MODIFIER\n"
                "1  1    -   simple  a     -\n"
                "2  4    /   path    b     prefix 2\n"
            ),
        ),
        (
            "{+a,b*}x{#c}{.d}{;e}{?f}{&g:4}",
            0,
            (
                "N  COL  OP  FORM          NAME  MODIFIER\n"
                "1  1    +   reserved      a     -\n"
                "1  1    +   reserved      b     explode\n"
                "2  9    #   fragment      c     -\n"
                "3  13   .   label         d     -\n"
                "4  17   ;   parameter     e     -\n"
                "5  21   ?   query         f     -\n"
                "6  25   &   continuation  g     prefix 4\n"
            ),
        ),
        ("😀{a}", 0, "N  COL  OP  FORM    NAME  MODIFIER\n1  2    -   simple  a     -\n"),
        ("abc", 1, ""),
        ("", 1, ""),
    ],
)
def test_explain_outputs_every_specification_exactly(template, expected_code, expected_stdout):
    io = MemIo()
    assert run_explain([template], io) == expected_code
    assert io.stdout == expected_stdout
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("template", "expected_code", "expected_stdout"),
    [
        ("{a}{b}{a}", 0, "a\nb\n"),
        ("{/a*,b:3}{?c}", 0, "a\nb\nc\n"),
        ("{x.y}{%41}", 0, "x.y\n%41\n"),
        ("{a,a*,a:2,A,%41,%4a,%4A}", 0, "a\nA\n%41\n%4a\n%4A\n"),
        ("abc", 1, ""),
        ("", 1, ""),
    ],
)
def test_names_preserve_first_appearance_and_exact_spelling(
    template, expected_code, expected_stdout
):
    io = MemIo()
    assert run_names([template], io) == expected_code
    assert io.stdout == expected_stdout
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("args", "expected_stdout"),
    [
        ([""], ""),
        (["abc-._~XYZ019"], "abc-._~XYZ019"),
        (["a b"], "a%20b"),
        (["a/b?c#d"], "a%2Fb%3Fc%23d"),
        (["--reserved", "a/b?c#d"], "a/b?c#d"),
        (["--reserved", "%41%4 %2f"], "%41%254%20%2f"),
        (["%41"], "%2541"),
        (["\ufeff"], "%EF%BB%BF"),
        (["\u200b\u00a0"], "%E2%80%8B%C2%A0"),
        (["--reserved", "\u0085"], "%C2%85"),
        (["\r"], "%0D"),
        (["a\u2028b"], "a%E2%80%A8b"),
        (["é😀"], "%C3%A9%F0%9F%98%80"),
        (["--reserved", '{}\\^"<>'], "%7B%7D%5C%5E%22%3C%3E"),
        (["a/b", "--reserved", "--reserved"], "a/b"),
        (["-"], "-"),
        (["-x"], "-x"),
    ],
)
def test_encode_matches_the_literal_command_cases(args, expected_stdout):
    io = MemIo()
    assert run_encode(args, io) == 0
    assert io.stdout == expected_stdout
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("run_command", "template", "expected"),
    [
        (run_explain, "{a", "template:1: UT001 unclosed expression"),
        (run_names, "{a", "template:1: UT001 unclosed expression"),
        (run_explain, "x{a}}", 'template:5: UT002 unmatched "}"'),
        (run_names, "x{a}}", 'template:5: UT002 unmatched "}"'),
        (run_explain, "{}", "template:1: UT003 empty expression"),
        (run_names, "{}", "template:1: UT003 empty expression"),
        (run_explain, "{=a}", 'template:2: UT004 reserved operator "="'),
        (run_names, "{=a}", 'template:2: UT004 reserved operator "="'),
        (run_explain, "{a,}", "template:4: UT005 bad variable name"),
        (run_names, "{a,}", "template:4: UT005 bad variable name"),
        (run_explain, "{a}{b:0}", "template:6: UT006 bad modifier"),
        (run_names, "{a}{b:0}", "template:6: UT006 bad modifier"),
    ],
)
def test_template_failures_are_atomic_for_both_listing_adapters(run_command, template, expected):
    io = MemIo()
    with pytest.raises(Failure) as error:
        run_command([template], io)
    assert error.value.message == expected
    assert io.stdout == ""
    assert io.stderr == ""


def test_adapters_make_only_atomic_output_calls_and_no_input_calls(monkeypatch):
    io = MemIo()
    output_calls = []
    error_calls = []
    read_calls = []
    monkeypatch.setattr(io, "out", output_calls.append)
    monkeypatch.setattr(io, "err", error_calls.append)
    monkeypatch.setattr(io, "read_stdin", lambda: read_calls.append("stdin"))
    monkeypatch.setattr(io, "read_file", lambda path: read_calls.append(path))

    assert run_explain(["{a}"], io) == 0
    assert output_calls == ["N  COL  OP  FORM    NAME  MODIFIER\n1  1    -   simple  a     -\n"]
    output_calls.clear()

    assert run_names(["{a}"], io) == 0
    assert output_calls == ["a\n"]
    output_calls.clear()

    assert run_encode(["a b"], io) == 0
    assert output_calls == ["a%20b"]
    output_calls.clear()

    assert run_encode([""], io) == 0
    assert len(output_calls) <= 1
    output_calls.clear()

    assert run_explain(["abc"], io) == 1
    assert output_calls == []
    assert run_names(["abc"], io) == 1
    assert output_calls == []

    with pytest.raises(Failure) as error:
        run_explain(["{a}{b:0}"], io)
    assert error.value.message == "template:6: UT006 bad modifier"
    assert output_calls == []
    with pytest.raises(Failure) as error:
        run_names(["{a}{b:0}"], io)
    assert error.value.message == "template:6: UT006 bad modifier"
    assert output_calls == []

    with pytest.raises(Failure) as error:
        run_explain(["--oops", "{"], io)
    assert error.value.message == 'unknown option "--oops"'
    with pytest.raises(Failure) as error:
        run_encode(["a\ud800", "extra"], io)
    assert error.value.message == "usage: encode [--reserved] TEXT"

    assert output_calls == []
    assert error_calls == []
    assert read_calls == []
    assert io.stdout == ""
    assert io.stderr == ""
