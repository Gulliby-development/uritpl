from unittest.mock import Mock

import pytest

from uritpl.check import run_check
from uritpl.fault import Failure
from uritpl.io import MemIo


@pytest.mark.parametrize(
    ("file_text", "expected_code", "expected_output"),
    [
        ("", 0, "0 templates checked, 0 problems\n"),
        ("\n\n", 0, "0 templates checked, 0 problems\n"),
        ("/users{/id}{?q}", 0, "1 template checked, 0 problems\n"),
        ("/a{b}\r\n/c{d}\r\n", 0, "2 templates checked, 0 problems\n"),
        (
            "a\n\n{b\n",
            1,
            "t.txt:3:1: UT001 unclosed expression\n2 templates checked, 1 problem\n",
        ),
        (
            "x\ry\n",
            1,
            (
                "t.txt:1:2: UT103 literal character U+000D will be percent-encoded\n"
                "1 template checked, 1 problem\n"
            ),
        ),
        ("x\r\n", 0, "1 template checked, 0 problems\n"),
        (
            "\ufeff/a\n",
            1,
            (
                "t.txt:1:1: UT103 literal character U+FEFF will be percent-encoded\n"
                "1 template checked, 1 problem\n"
            ),
        ),
        (
            "a\u2028b\u2029c\u0085d\u3000e",
            1,
            (
                "t.txt:1:2: UT103 literal character U+2028 will be percent-encoded\n"
                "t.txt:1:4: UT103 literal character U+2029 will be percent-encoded\n"
                "t.txt:1:6: UT103 literal character U+0085 will be percent-encoded\n"
                "t.txt:1:8: UT103 literal character U+3000 will be percent-encoded\n"
                "1 template checked, 4 problems\n"
            ),
        ),
        (
            "100%/%41/%4/%zz/%\n",
            1,
            (
                "t.txt:1:4: UT103 literal character U+0025 will be percent-encoded\n"
                "1 template checked, 1 problem\n"
            ),
        ),
        (
            "{&a}{?b}{?c}{b}\n",
            1,
            (
                't.txt:1:1: UT102 no query started before this: use "?" instead of "&"\n'
                't.txt:1:9: UT101 query already started: use "&" instead of "?"\n'
                't.txt:1:14: UT104 variable "b" appears again (first at column 7)\n'
                "1 template checked, 3 problems\n"
            ),
        ),
        (
            "{a\n{b}}\n{c,d:0}\n",
            1,
            (
                "t.txt:1:1: UT001 unclosed expression\n"
                't.txt:2:4: UT002 unmatched "}"\n'
                "t.txt:3:5: UT006 bad modifier\n"
                "3 templates checked, 3 problems\n"
            ),
        ),
    ],
)
def test_check_short_file_examples(file_text, expected_code, expected_output):
    io = MemIo(files={"t.txt": file_text.encode("utf-8")})
    output = Mock(wraps=io.out)
    io.out = output

    assert run_check(["t.txt"], io) == expected_code
    assert io.stdout == expected_output
    assert io.stderr == ""
    output.assert_called_once_with(expected_output)


def test_check_five_line_invisible_character_example():
    file_text = "\ufeff/a{b}\n/c\u00a0d\ne\u200bf\u200b\ng\rh\ni\u2028j\u0085k\n"
    expected = (
        "t.txt:1:1: UT103 literal character U+FEFF will be percent-encoded\n"
        "t.txt:2:3: UT103 literal character U+00A0 will be percent-encoded\n"
        "t.txt:3:2: UT103 literal character U+200B will be percent-encoded\n"
        "t.txt:4:2: UT103 literal character U+000D will be percent-encoded\n"
        "t.txt:5:2: UT103 literal character U+2028 will be percent-encoded\n"
        "t.txt:5:4: UT103 literal character U+0085 will be percent-encoded\n"
        "5 templates checked, 6 problems\n"
    )
    io = MemIo(files={"t.txt": file_text.encode("utf-8")})
    output = Mock(wraps=io.out)
    io.out = output

    assert run_check(["t.txt"], io) == 1
    assert io.stdout == expected
    assert io.stderr == ""
    output.assert_called_once_with(expected)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (
            ["a.txt", "b.txt"],
            (
                'a.txt:1:16: UT101 query already started: use "&" instead of "?"\n'
                'a.txt:2:1: UT102 no query started before this: use "?" instead of "&"\n'
                "a.txt:3:3: UT103 literal character U+0020 will be percent-encoded\n"
                'a.txt:3:11: UT104 variable "id" appears again (first at column 7)\n'
                "4 templates checked, 4 problems\n"
            ),
        ),
        (
            ["b.txt", "a.txt"],
            (
                'a.txt:1:16: UT101 query already started: use "&" instead of "?"\n'
                'a.txt:2:1: UT102 no query started before this: use "?" instead of "&"\n'
                "a.txt:3:3: UT103 literal character U+0020 will be percent-encoded\n"
                'a.txt:3:11: UT104 variable "id" appears again (first at column 7)\n'
                "4 templates checked, 4 problems\n"
            ),
        ),
    ],
)
def test_check_aggregates_files_and_preserves_problem_order(arguments, expected):
    files = {
        "a.txt": b"/users{/id}{?q}{?page}\n{&a}\n/x y/{id}{id}\n",
        "b.txt": b"{?z}\n",
    }
    io = MemIo(files=files)
    output = Mock(wraps=io.out)
    io.out = output

    assert run_check(arguments, io) == 1
    assert io.stdout == expected
    assert io.stderr == ""
    output.assert_called_once_with(expected)


def test_check_reports_problem_files_in_reversed_argument_order():
    files = {"a.txt": b"x y\n", "b.txt": b"m n\n"}
    io = MemIo(files=files)
    expected = (
        "b.txt:1:2: UT103 literal character U+0020 will be percent-encoded\n"
        "a.txt:1:2: UT103 literal character U+0020 will be percent-encoded\n"
        "2 templates checked, 2 problems\n"
    )

    assert run_check(["b.txt", "a.txt"], io) == 1
    assert io.stdout == expected
    assert io.stderr == ""


def test_check_resets_query_and_duplicate_state_for_each_line_and_file():
    files = {
        "first.txt": b"{?a}\n{&b}\n{a}\n",
        "second.txt": b"{a}\n{&c}\n",
    }
    expected = (
        'first.txt:2:1: UT102 no query started before this: use "?" instead of "&"\n'
        'second.txt:2:1: UT102 no query started before this: use "?" instead of "&"\n'
        "5 templates checked, 2 problems\n"
    )
    io = MemIo(files=files)

    assert run_check(["first.txt", "second.txt"], io) == 1
    assert io.stdout == expected
    assert io.stderr == ""


def test_check_uses_shared_decoder_for_bom_crlf_and_raw_cr_bytes():
    io = MemIo(files={"t.txt": b"\xef\xbb\xbf/a\r\nx\ry\n"})
    expected = (
        "t.txt:1:1: UT103 literal character U+FEFF will be percent-encoded\n"
        "t.txt:2:2: UT103 literal character U+000D will be percent-encoded\n"
        "2 templates checked, 2 problems\n"
    )

    assert run_check(["t.txt"], io) == 1
    assert io.stdout == expected
    assert io.stderr == ""


def test_check_accepts_stdin_unicode_display_names_and_dash_prefixed_paths():
    io = MemIo(
        stdin=b"/ok\n",
        files={"é.txt": b" \n", "-x": b"/ok\n"},
    )
    output = Mock(wraps=io.out)
    io.out = output
    expected = (
        "?.txt:1:1: UT103 literal character U+0020 will be percent-encoded\n"
        "3 templates checked, 1 problem\n"
    )

    assert run_check(["-", "é.txt", "-x"], io) == 1
    assert io.stdout == expected
    assert io.stderr == ""
    output.assert_called_once_with(expected)

    stdin_only = MemIo(stdin=b"/ok\n")
    assert run_check(["-"], stdin_only) == 0
    assert stdin_only.stdout == "1 template checked, 0 problems\n"
    assert stdin_only.stderr == ""


@pytest.mark.parametrize(
    ("arguments", "expected_message"),
    [
        ([], "usage: check FILE..."),
        (["--oops"], 'unknown option "--oops"'),
        (["--"], 'unknown option "--"'),
        (["--help"], 'unknown option "--help"'),
        (["t.txt", "u.txt"], "u.txt: cannot read the file"),
        (["t.txt", "bad.txt"], "bad.txt: input is not valid UTF-8"),
        (["-", "-"], "standard input is named twice"),
        (["missing\u200bé.txt", "bad.txt"], "missing??.txt: cannot read the file"),
        (["missing.txt", "--oops"], 'unknown option "--oops"'),
    ],
)
def test_check_failure_precedence_is_atomic(arguments, expected_message):
    io = MemIo(
        stdin=b"{a}{a}\n",
        files={
            "t.txt": b"{a}{a}\n",
            "bad.txt": b"\x7b\x61\x7d\x0a\xe9\x0a",
        },
    )
    output = Mock(wraps=io.out)
    io.out = output

    with pytest.raises(Failure) as error:
        run_check(arguments, io)

    assert error.value.message == expected_message
    assert io.stdout == ""
    assert io.stderr == ""
    output.assert_not_called()
