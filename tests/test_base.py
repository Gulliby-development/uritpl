# BEGIN acceptance rows: cases from the spec's acceptance table.
# Edit acceptance_actual, not this block.
_acceptance_json = __import__("json")
_acceptance_pytest = __import__("pytest")

_ACCEPTANCE_TEXT = [
    '[{"id":"AC-003:1","input":["plain",""],"expected":""},',
    '{"id":"AC-003:2","input":["plain"," ~AZ09\\""],"expected":" ~AZ09\\""},',
    '{"id":"AC-003:3","input":["plain","a\\t\\r\\n\\u007fé😀"],"expected":"a?',
    '?????"},',
    '{"id":"AC-003:4","input":["plain","\\u0085\\u2028\\u2029\\ufeff\\u200b\\',
    'u00a0\\u3000"],"expected":"???????"},',
    '{"id":"AC-003:5","input":["show","a\\ud800"],"expected":"\\"a?\\""},',
    '{"id":"AC-003:6","input":["show","a\\"b"],"expected":"\\"a\\"b\\""},',
    '{"id":"AC-003:7","input":["show",""],"expected":"\\"\\""},',
    '{"id":"AC-004:1","input":[0,"problem"],"expected":"0 problems"},',
    '{"id":"AC-004:2","input":[1,"problem"],"expected":"1 problem"},',
    '{"id":"AC-004:3","input":[2,"problem"],"expected":"2 problems"},',
    '{"id":"AC-005:1","input":["is_alpha","A"],"expected":true},',
    '{"id":"AC-005:2","input":["is_alpha","z"],"expected":true},',
    '{"id":"AC-005:3","input":["is_alpha","é"],"expected":false},',
    '{"id":"AC-005:4","input":["is_alpha","_"],"expected":false},',
    '{"id":"AC-005:5","input":["is_digit","0"],"expected":true},',
    '{"id":"AC-005:6","input":["is_digit","9"],"expected":true},',
    '{"id":"AC-005:7","input":["is_digit","٣"],"expected":false},',
    '{"id":"AC-005:8","input":["is_hex","F"],"expected":true},',
    '{"id":"AC-005:9","input":["is_hex","a"],"expected":true},',
    '{"id":"AC-005:10","input":["is_hex","0"],"expected":true},',
    '{"id":"AC-005:11","input":["is_hex","g"],"expected":false},',
    '{"id":"AC-005:12","input":["is_hex","٣"],"expected":false},',
    '{"id":"AC-005:13","input":["has_surrogate",""],"expected":false},',
    '{"id":"AC-005:14","input":["has_surrogate","é😀"],"expected":false},',
    '{"id":"AC-005:15","input":["has_surrogate","a\\ud800"],"expected":true},',
    '{"id":"AC-005:16","input":["has_surrogate","\\udfff"],"expected":true},',
    '{"id":"AC-005:17","input":["has_surrogate","퟿"],"expected":false},',
    '{"id":"AC-006:1","input":[["N","NAME"],[["1","a"],["22","longer"]]],"exp',
    'ected":["N   NAME","1   a","22  longer"]},',
    '{"id":"AC-006:2","input":[["A","B"],[["😀","x"],["zz",""]]],"expected":[',
    '"A   B","😀   x","zz"]},',
    '{"id":"AC-006:3","input":[["NAME","X"],[]],"expected":["NAME  X"]}]',
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


from dataclasses import is_dataclass
from unittest.mock import Mock

import pytest

from uritpl import text
from uritpl.fault import Failure, Fault
from uritpl.io import Inputs, MemIo, Source
from uritpl.options import Parsed, need, parse


def acceptance_actual(input):
    first = input[0]
    if isinstance(first, str):
        return getattr(text, first)(input[1])
    if isinstance(first, int):
        return text.plural(first, input[1])
    return text.table(first, input[1])


@pytest.mark.parametrize(
    ("code", "col", "arg", "expected"),
    [
        ("UT001", 1, "", "unclosed expression"),
        ("UT002", 5, "", 'unmatched "}"'),
        ("UT003", 1, "", "empty expression"),
        ("UT004", 2, "=", 'reserved operator "="'),
        ("UT004", 2, "é", 'reserved operator "?"'),
        ("UT005", 4, "", "bad variable name"),
        ("UT006", 3, "", "bad modifier"),
    ],
)
def test_fault_contract(code, col, arg, expected):
    fault = Fault(code, col, arg)
    assert fault.code == code
    assert fault.col == col
    assert fault.arg == arg
    assert fault.text == expected
    assert str(fault) == expected
    assert Fault("UT001", 1).arg == ""


def test_failure_exposes_message():
    failure = Failure("bad input")
    assert failure.message == "bad input"
    assert str(failure) == "bad input"


@pytest.mark.parametrize(
    ("argv", "specs", "expected_flags", "expected_args", "message"),
    [
        ([], [], set(), [], None),
        (
            ["-", "--strict", "-x", "--strict", "a"],
            ["--strict"],
            {"--strict"},
            ["-", "-x", "a"],
            None,
        ),
        (["--"], [], None, None, 'unknown option "--"'),
        (["--help"], [], None, None, 'unknown option "--help"'),
        (["--strict=1"], ["--strict"], None, None, 'unknown option "--strict=1"'),
        (["--é", "--oops"], [], None, None, 'unknown option "--?"'),
    ],
)
def test_parse_options(argv, specs, expected_flags, expected_args, message):
    if message is not None:
        with pytest.raises(Failure) as error:
            parse(argv, specs)
        assert error.value.message == message
        return
    parsed = parse(argv, specs)
    assert isinstance(parsed, Parsed)
    assert is_dataclass(parsed)
    assert parsed.flags == expected_flags
    assert parsed.args == expected_args


@pytest.mark.parametrize(
    ("words", "args", "low", "high", "message"),
    [
        ("check FILE...", [], 1, -1, "usage: check FILE..."),
        ("check FILE...", ["a", "b", "c"], 1, -1, None),
        ("names TEMPLATE", ["a"], 1, 1, None),
        ("names TEMPLATE", ["a", "b"], 1, 1, "usage: names TEMPLATE"),
        ("none", [], 0, 0, None),
    ],
)
def test_need_arity(words, args, low, high, message):
    if message is not None:
        with pytest.raises(Failure) as error:
            need(words, args, low, high)
        assert error.value.message == message
        return
    assert need(words, args, low, high) is None


def test_package_modules_import():
    import uritpl
    import uritpl.__main__
    import uritpl.charset
    import uritpl.check
    import uritpl.cli
    import uritpl.cmd_encode
    import uritpl.cmd_expand
    import uritpl.cmd_explain
    import uritpl.cmd_names
    import uritpl.cmd_trace
    import uritpl.codes
    import uritpl.expand
    import uritpl.lines
    import uritpl.load
    import uritpl.model
    import uritpl.operators
    import uritpl.parse
    import uritpl.percent
    import uritpl.problem
    import uritpl.rules
    import uritpl.value
    import uritpl.varexp
    import uritpl.varspec

    assert uritpl.__name__ == "uritpl"
    assert uritpl.__file__ is not None


def test_memio_preserves_bytes_and_appends_output():
    io = MemIo()
    assert io.read_stdin() == b""
    assert io.stdout == ""
    assert io.stderr == ""
    assert io.files == {}
    with pytest.raises(FileNotFoundError):
        io.read_file("missing")
    io.out("a")
    io.err("x")
    io.out("b\n")
    io.err("y")
    assert io.stdout == "ab\n"
    assert io.stderr == "xy"

    raw = b"\xef\xbb\xbfa\r\nb\rc\xc2\x85\xe2\x80\xa8\xe2\x80\xa9"
    file_io = MemIo(files={"é.txt": raw})
    assert file_io.read_file("é.txt") == raw


def test_inputs_preserves_text_and_tracks_stdin():
    stdin = b"a\r\n"
    raw = b"\xef\xbb\xbfa\r\nb\rc\xc2\x85\xe2\x80\xa8\xe2\x80\xa9"
    io = MemIo(stdin=stdin, files={"é.txt": raw})
    inputs = Inputs(io)

    source = inputs.read("é.txt")
    assert isinstance(source, Source)
    assert is_dataclass(source)
    assert source.display == "?.txt"
    assert source.text == "\ufeffa\r\nb\rc\u0085\u2028\u2029"
    assert inputs.read("é.txt") == source
    assert inputs.read("-") == Source("<stdin>", "a\r\n")
    with pytest.raises(Failure) as error:
        inputs.read("-")
    assert error.value.message == "standard input is named twice"
    assert io.stdout == ""
    assert io.stderr == ""


def test_inputs_translates_read_and_decode_errors():
    invalid_file = Inputs(MemIo(files={"v.json": b"{\xff}"}))
    with pytest.raises(Failure) as error:
        invalid_file.read("v.json")
    assert error.value.message == "v.json: input is not valid UTF-8"

    invalid_stdin_io = MemIo(stdin=b"a\xff\n")
    with pytest.raises(Failure) as error:
        Inputs(invalid_stdin_io).read("-")
    assert error.value.message == "<stdin>: input is not valid UTF-8"
    assert invalid_stdin_io.stdout == ""
    assert invalid_stdin_io.stderr == ""

    missing_path = "missing\u200bé.json"
    missing_io = MemIo()
    with pytest.raises(FileNotFoundError):
        missing_io.read_file(missing_path)
    with pytest.raises(Failure) as error:
        Inputs(missing_io).read(missing_path)
    assert error.value.message == "missing??.json: cannot read the file"

    failed_file_io = MemIo()
    failed_file_io.read_file = Mock(side_effect=OSError("unavailable"))
    with pytest.raises(Failure) as error:
        Inputs(failed_file_io).read("DISPLAY")
    assert error.value.message == "DISPLAY: cannot read the file"

    failed_stdin_io = MemIo()
    failed_stdin_io.read_stdin = Mock(side_effect=OSError("unavailable"))
    with pytest.raises(Failure) as error:
        Inputs(failed_stdin_io).read("-")
    assert error.value.message == "<stdin>: cannot read the file"
    assert failed_file_io.stdout == failed_file_io.stderr == ""
    assert failed_stdin_io.stdout == failed_stdin_io.stderr == ""
