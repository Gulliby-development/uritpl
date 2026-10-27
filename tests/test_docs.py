from pathlib import Path

import pytest

from uritpl.cli import USAGE, run
from uritpl.io import MemIo

README = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
HELP_TEXT = (
    "usage: uritpl expand [--strict] TEMPLATE VARS\n"
    "usage: uritpl trace [--strict] [--only=N] TEMPLATE VARS\n"
    "usage: uritpl explain TEMPLATE\n"
    "usage: uritpl names TEMPLATE\n"
    "usage: uritpl encode [--reserved] TEXT\n"
    "usage: uritpl check FILE...\n"
)


def test_readme_covers_audience_offline_setup_and_development():
    assert "## Install" in README
    assert "## Usage" in README
    assert "## Commands" in README
    assert "## Development" in README
    assert "API clients, OpenAPI" in README
    assert "link headers" in README
    assert "Python 3.11 or newer" in README
    assert "uses only the Python standard library" in README
    assert "makes no network requests" in README
    assert "python -m uritpl" in README
    assert "ruff check ." in README
    assert "ruff format --check ." in README
    assert "pytest" in README


def test_readme_usage_block_matches_cli_help():
    assert USAGE == HELP_TEXT
    assert HELP_TEXT in README


@pytest.mark.parametrize(
    (
        "argv",
        "files",
        "invocation",
        "fixture",
        "documented_output",
        "expected_status",
        "expected_stdout",
    ),
    [
        (
            ["expand", "/users{/id}{?q}", "v.json"],
            {"v.json": b'{"id": "42", "q": "a b"}'},
            '$ python -m uritpl expand "/users{/id}{?q}" v.json',
            '{"id": "42", "q": "a b"}',
            "/users/42?q=a%20b",
            0,
            "/users/42?q=a%20b",
        ),
        (
            ["trace", "/users{/id}{?q,page}", "v.json"],
            {"v.json": b'{"id": "42", "q": "a b"}'},
            '$ python -m uritpl trace "/users{/id}{?q,page}" v.json',
            '{"id": "42", "q": "a b"}',
            ('N  EXPRESSION   RESULT\n1  "{/id}"      "/42"\n2  "{?q,page}"  "?q=a%20b"\n'),
            0,
            ('N  EXPRESSION   RESULT\n1  "{/id}"      "/42"\n2  "{?q,page}"  "?q=a%20b"\n'),
        ),
        (
            ["explain", "{a}{/b:2}"],
            {},
            '$ python -m uritpl explain "{a}{/b:2}"',
            "No files are needed for this example:",
            (
                "N  COL  OP  FORM    NAME  MODIFIER\n"
                "1  1    -   simple  a     -\n"
                "2  4    /   path    b     prefix 2"
            ),
            0,
            (
                "N  COL  OP  FORM    NAME  MODIFIER\n"
                "1  1    -   simple  a     -\n"
                "2  4    /   path    b     prefix 2\n"
            ),
        ),
        (
            ["names", "{a}{b}{a}"],
            {},
            '$ python -m uritpl names "{a}{b}{a}"',
            "No files are needed:",
            "a\nb",
            0,
            "a\nb\n",
        ),
        (
            ["encode", "--reserved", "a/b?c#d"],
            {},
            '$ python -m uritpl encode --reserved "a/b?c#d"',
            "No files are needed:",
            "a/b?c#d",
            0,
            "a/b?c#d",
        ),
        (
            ["check", "t.txt"],
            {"t.txt": b"/users{/id}{?q}\n"},
            "$ python -m uritpl check t.txt",
            "/users{/id}{?q}",
            "1 template checked, 0 problems",
            0,
            "1 template checked, 0 problems\n",
        ),
    ],
)
def test_documented_examples_match_command_results(
    argv, files, invocation, fixture, documented_output, expected_status, expected_stdout
):
    assert invocation in README
    assert fixture in README
    assert documented_output in README
    io = MemIo(files=files)
    assert run(argv, io) == expected_status
    assert io.stdout == expected_stdout
    assert io.stderr == ""
