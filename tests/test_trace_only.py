import pytest

from uritpl.cli import run
from uritpl.io import MemIo

VARS = b'{"id": "42", "q": "a b"}'


def trace(*argv, files=None):
    io = MemIo(files={"v.json": VARS} if files is None else files)
    status = run(["trace", *argv], io)
    return status, io.stdout, io.stderr


def test_only_keeps_the_numbered_expression_and_its_number():
    template = "/users{/id}{?q,page}"
    assert trace("--only=1", template, "v.json") == (
        0,
        'N  EXPRESSION  RESULT\n1  "{/id}"     "/42"\n',
        "",
    )
    assert trace("--only=2", template, "v.json") == (
        0,
        'N  EXPRESSION   RESULT\n2  "{?q,page}"  "?q=a%20b"\n',
        "",
    )


def test_without_only_every_expression_is_traced():
    assert trace("/users{/id}{?q,page}", "v.json") == (
        0,
        'N  EXPRESSION   RESULT\n1  "{/id}"      "/42"\n2  "{?q,page}"  "?q=a%20b"\n',
        "",
    )


def test_only_may_stand_anywhere_and_the_last_one_wins():
    expected = (0, 'N  EXPRESSION  RESULT\n2  "{b}"       ""\n', "")
    assert trace("{a}{b}", "v.json", "--only=2") == expected
    assert trace("--only=1", "{a}{b}", "--only=2", "v.json") == expected
    assert trace("--only=02", "{a}{b}", "v.json") == expected


def test_only_past_the_last_expression_is_an_error():
    assert trace("--only=3", "/users{/id}{?q,page}", "v.json") == (
        2,
        "",
        "uritpl: expression 3 not found (the template has 2)\n",
    )
    assert trace("--only=1", "/users", "v.json") == (
        2,
        "",
        "uritpl: expression 1 not found (the template has 0)\n",
    )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("0", 'uritpl: invalid --only value "0"\n'),
        ("", 'uritpl: invalid --only value ""\n'),
        ("abc", 'uritpl: invalid --only value "abc"\n'),
        ("-1", 'uritpl: invalid --only value "-1"\n'),
        ("1.5", 'uritpl: invalid --only value "1.5"\n'),
        (" 1", 'uritpl: invalid --only value " 1"\n'),
    ],
)
def test_only_needs_a_whole_number_from_one(value, message):
    assert trace("--only=" + value, "{id}", "v.json") == (2, "", message)


def test_only_written_without_a_value_is_an_error():
    assert trace("--only", "{id}", "v.json") == (
        2,
        "",
        'uritpl: option "--only" needs a value\n',
    )


def test_the_value_is_checked_before_any_file_is_read():
    assert trace("--only=x", "{id}", "missing.json", files={}) == (
        2,
        "",
        'uritpl: invalid --only value "x"\n',
    )


def test_strict_still_traces_the_whole_template_first():
    assert trace("--strict", "--only=1", "{id}{zz}", "v.json") == (
        2,
        "",
        'uritpl: undefined variable "zz"\n',
    )


def test_other_commands_do_not_take_only():
    io = MemIo(files={"v.json": VARS})
    assert run(["expand", "--only=1", "{id}", "v.json"], io) == 2
    assert io.stderr == 'uritpl: unknown option "--only=1"\n'
