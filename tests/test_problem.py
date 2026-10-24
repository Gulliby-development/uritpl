from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from uritpl.codes import QUERY_AGAIN, QUERY_MISSING, again_text, encoded_text
from uritpl.io import Inputs, MemIo
from uritpl.problem import Problem, render, sorted_problems


def test_problem_is_a_frozen_dataclass_with_value_equality():
    problem = Problem(3, "UT103", "encoded")
    assert is_dataclass(problem)
    assert problem == Problem(3, "UT103", "encoded")
    assert problem != Problem(4, "UT103", "encoded")
    assert (problem.col, problem.code, problem.text) == (3, "UT103", "encoded")
    with pytest.raises(FrozenInstanceError):
        problem.col = 4


def test_sorted_problems_returns_fresh_empty_and_singleton_lists():
    found = []
    empty = sorted_problems(found)
    assert empty == []
    assert empty is not found

    problem = Problem(2, "UT101", "again")
    found = [problem]
    ordered = sorted_problems(found)
    assert ordered == [problem]
    assert ordered is not found
    assert found == [problem]


def test_sorted_problems_uses_column_then_code():
    late_column = Problem(8, "UT001", "late")
    later_code = Problem(2, "UT104", "later code")
    earlier_code = Problem(2, "UT101", "earlier code")
    found = [late_column, later_code, earlier_code]
    assert sorted_problems(found) == [earlier_code, later_code, late_column]
    assert found == [late_column, later_code, earlier_code]


def test_sorted_problems_preserves_equal_keys_and_input():
    first = Problem(4, "UT103", "first text")
    second = Problem(4, "UT103", "second text")
    found = [second, first]
    ordered = sorted_problems(found)
    assert ordered == [second, first]
    assert ordered[0] is second
    assert ordered[1] is first
    assert found == [second, first]


def test_render_has_exact_punctuation_and_no_line_ending():
    assert render("templates/a.txt", 12, Problem(34, "UT101", "bad query")) == (
        "templates/a.txt:12:34: UT101 bad query"
    )


def test_render_supports_stdin_display():
    assert render("<stdin>", 1, Problem(1, "UT102", "missing query")) == (
        "<stdin>:1:1: UT102 missing query"
    )


def test_render_uses_sanitized_display_from_inputs():
    source = Inputs(MemIo(files={"é.txt": b"x"})).read("é.txt")
    assert source.display == "?.txt"
    assert render(source.display, 7, Problem(2, "UT103", "encoded")) == ("?.txt:7:2: UT103 encoded")


def test_query_message_vocabulary_is_exact():
    assert QUERY_AGAIN == 'query already started: use "&" instead of "?"'
    assert QUERY_MISSING == 'no query started before this: use "?" instead of "&"'


@pytest.mark.parametrize(
    ("ch", "expected"),
    [
        ("\x00", "literal character U+0000 will be percent-encoded"),
        (" ", "literal character U+0020 will be percent-encoded"),
        ("%", "literal character U+0025 will be percent-encoded"),
        ("\r", "literal character U+000D will be percent-encoded"),
        ("\u00a0", "literal character U+00A0 will be percent-encoded"),
        ("\u0085", "literal character U+0085 will be percent-encoded"),
        ("\u2028", "literal character U+2028 will be percent-encoded"),
        ("\u2029", "literal character U+2029 will be percent-encoded"),
        ("\ufeff", "literal character U+FEFF will be percent-encoded"),
        ("\u200b", "literal character U+200B will be percent-encoded"),
        ("\u3000", "literal character U+3000 will be percent-encoded"),
        ("😀", "literal character U+1F600 will be percent-encoded"),
    ],
)
def test_encoded_text_uses_uppercase_minimum_width_codepoints(ch, expected):
    assert encoded_text(ch) == expected


@pytest.mark.parametrize(
    ("name", "first_col", "expected"),
    [
        ("item", 1, 'variable "item" appears again (first at column 1)'),
        ("", 12, 'variable "" appears again (first at column 12)'),
        ("%41", 23, 'variable "%41" appears again (first at column 23)'),
        ("café", 4, 'variable "caf?" appears again (first at column 4)'),
        ("\x00x\r", 9, 'variable "?x?" appears again (first at column 9)'),
        ("a\ud800b", 31, 'variable "a?b" appears again (first at column 31)'),
    ],
)
def test_again_text_sanitizes_names_and_keeps_first_column(name, first_col, expected):
    assert again_text(name, first_col) == expected
