import subprocess
import sys
from pathlib import Path

import pytest

from uritpl.cli import COMMANDS, USAGE, run
from uritpl.io import MemIo


def invoke(argv, files=None, stdin=b""):
    io = MemIo(stdin=stdin, files=files)
    status = run(argv, io)
    return status, io


def test_help_uses_the_single_ordered_registry_and_one_output_call(monkeypatch):
    expected = (
        "usage: uritpl expand [--strict] TEMPLATE VARS\n"
        "usage: uritpl trace [--strict] [--only=N] TEMPLATE VARS\n"
        "usage: uritpl explain TEMPLATE\n"
        "usage: uritpl names TEMPLATE\n"
        "usage: uritpl encode [--reserved] TEXT\n"
        "usage: uritpl check FILE...\n"
    )
    assert list(COMMANDS) == ["expand", "trace", "explain", "names", "encode", "check"]
    assert [usage for usage, adapter in COMMANDS.values()] == [
        "expand [--strict] TEMPLATE VARS",
        "trace [--strict] [--only=N] TEMPLATE VARS",
        "explain TEMPLATE",
        "names TEMPLATE",
        "encode [--reserved] TEXT",
        "check FILE...",
    ]
    assert all(callable(adapter) for _, adapter in COMMANDS.values())
    assert USAGE == expected

    io = MemIo()
    calls = []
    monkeypatch.setattr(io, "out", calls.append)
    assert run(["--help"], io) == 0
    assert calls == [expected]
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("argv", "expected_stderr"),
    [
        ([], "uritpl: missing command (expand, trace, explain, names, encode or check)\n"),
        (["frobé\u00a0"], 'uritpl: unknown command "frob??"\n'),
        (["--help", "names"], 'uritpl: unknown command "--help"\n'),
        (["frob", "--oops"], 'uritpl: unknown command "frob"\n'),
    ],
)
def test_command_selection_errors_are_exact(argv, expected_stderr):
    status, io = invoke(argv)
    assert status == 2
    assert io.stdout == ""
    assert io.stderr == expected_stderr


@pytest.mark.parametrize(
    ("argv", "files", "expected_status", "expected_stdout"),
    [
        (
            ["expand", "/users{/id}{?q}", "v.json"],
            {"v.json": b'{"id":"42","q":"a b"}'},
            0,
            "/users/42?q=a%20b",
        ),
        (
            ["trace", "/users{/id}{?q,page}", "v.json"],
            {"v.json": b'{"id":"42","q":"a b"}'},
            0,
            'N  EXPRESSION   RESULT\n1  "{/id}"      "/42"\n2  "{?q,page}"  "?q=a%20b"\n',
        ),
        (
            ["explain", "{a}{/b:2}"],
            {},
            0,
            (
                "N  COL  OP  FORM    NAME  MODIFIER\n"
                "1  1    -   simple  a     -\n"
                "2  4    /   path    b     prefix 2\n"
            ),
        ),
        (["names", "{a}{b}{a}"], {}, 0, "a\nb\n"),
        (["encode", "é😀"], {}, 0, "%C3%A9%F0%9F%98%80"),
        (["encode", "--reserved", "a/b?c#d"], {}, 0, "a/b?c#d"),
        (
            ["check", "t.txt"],
            {"t.txt": b"/users{/id}{?q}\n"},
            0,
            "1 template checked, 0 problems\n",
        ),
        (["explain", "abc"], {}, 1, ""),
        (["names", "abc"], {}, 1, ""),
        (["trace", "/static", "v.json"], {"v.json": b"{}"}, 0, ""),
    ],
)
def test_all_commands_dispatch_through_memio(argv, files, expected_status, expected_stdout):
    status, io = invoke(argv, files=files)
    assert status == expected_status
    assert io.stdout == expected_stdout
    assert io.stderr == ""


@pytest.mark.parametrize(
    ("argv", "files", "expected_message"),
    [
        (["expand", "--oops"], {}, 'unknown option "--oops"'),
        (["expand", "{a"], {}, "usage: expand [--strict] TEMPLATE VARS"),
        (
            ["expand", "{a}", "v.json", "w.json"],
            {"v.json": b"{}", "w.json": b"{}"},
            "usage: expand [--strict] TEMPLATE VARS",
        ),
        (
            ["expand", "{a", "missing.json"],
            {},
            "template:1: UT001 unclosed expression",
        ),
        (
            ["expand", "a\ud800", "missing.json"],
            {},
            'invalid text "a?"',
        ),
        (["expand", "{a}", "missing.json"], {}, "missing.json: cannot read the file"),
        (
            ["expand", "--strict", "{a:2}{b}", "v.json"],
            {"v.json": b'{"a":["x"]}'},
            'variable "a": prefix modifier on a list value',
        ),
        (
            ["trace", "--strict", "--strict", "{b}{a}", "v.json"],
            {"v.json": b'{"a":["x"]}'},
            'undefined variable "b"',
        ),
        (["names", "--help", "{a}"], {}, 'unknown option "--help"'),
        (["encode", "a\ud800"], {}, 'invalid text "a?"'),
        (["check"], {}, "usage: check FILE..."),
        (
            ["expand", "{a}", "v.json"],
            {"v.json": b"{\xff}"},
            "v.json: input is not valid UTF-8",
        ),
        (
            ["expand", "{a}", "v.json"],
            {"v.json": b'{"a":1}'},
            'v.json: variable "a": unsupported value',
        ),
        (["expand", "{a}", "v.json"], {"v.json": b"{"}, "v.json: not valid JSON"),
    ],
)
def test_failures_have_one_exact_stderr_line_and_no_stdout(argv, files, expected_message):
    status, io = invoke(argv, files=files)
    assert status == 2
    assert io.stdout == ""
    assert io.stderr == f"uritpl: {expected_message}\n"


@pytest.mark.parametrize(
    ("argv", "files", "stdin", "expected_status", "expected_stdout", "expected_stderr"),
    [
        (
            ["check", "t.txt"],
            {"t.txt": b"{a}{a}\n"},
            b"",
            1,
            (
                't.txt:1:5: UT104 variable "a" appears again (first at column 2)\n'
                "1 template checked, 1 problem\n"
            ),
            "",
        ),
        (
            ["check", "t.txt", "u.txt"],
            {"t.txt": b"{a}{a}\n"},
            b"",
            2,
            "",
            "uritpl: u.txt: cannot read the file\n",
        ),
        (
            ["check", "-", "-"],
            {},
            b"/a\n",
            2,
            "",
            "uritpl: standard input is named twice\n",
        ),
    ],
)
def test_check_reports_duplicate_columns_and_keeps_multi_file_errors_atomic(
    argv, files, stdin, expected_status, expected_stdout, expected_stderr
):
    status, io = invoke(argv, files=files, stdin=stdin)
    assert status == expected_status
    assert io.stdout == expected_stdout
    assert io.stderr == expected_stderr


def test_invalid_utf8_stdin_process():
    repository_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "uritpl", "check", "-"],
        input=b"a\xff\n",
        check=False,
        capture_output=True,
        timeout=60,
        cwd=repository_root,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == b"uritpl: <stdin>: input is not valid UTF-8\n"
