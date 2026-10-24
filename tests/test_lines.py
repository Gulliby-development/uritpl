# BEGIN acceptance rows: cases from the spec's acceptance table.
# Edit acceptance_actual, not this block.
_acceptance_json = __import__("json")
_acceptance_pytest = __import__("pytest")

_ACCEPTANCE_TEXT = [
    '[{"id":"AC-002:1","input":" {a","expected":[{"code":"UT001","col":2,"tex',
    't":"unclosed expression"}]},',
    '{"id":"AC-002:2","input":"{a}{a}}","expected":[{"code":"UT002","col":7,"',
    'text":"unmatched \\"}\\""}]},',
    '{"id":"AC-002:3","input":" {}","expected":[{"code":"UT003","col":2,"text',
    '":"empty expression"}]},',
    '{"id":"AC-002:4","input":"{@a}","expected":[{"code":"UT004","col":2,"tex',
    't":"reserved operator \\"@\\""}]},',
    '{"id":"AC-002:5","input":"{ a}","expected":[{"code":"UT005","col":2,"tex',
    't":"bad variable name"}]},',
    '{"id":"AC-002:6","input":"{&a} {b:0}","expected":[{"code":"UT006","col":',
    '8,"text":"bad modifier"}]},',
    '{"id":"AC-002:7","input":"😀{a","expected":[{"code":"UT001","col":2,"tex',
    't":"unclosed expression"}]},',
    '{"id":"AC-003:1","input":"{&a}{&b}","expected":[{"code":"UT102","col":1,',
    '"text":"no query started before this: use \\"?\\" instead of \\"&\\""},{',
    '"code":"UT102","col":5,"text":"no query started before this: use \\"?\\"',
    ' instead of \\"&\\""}]},',
    '{"id":"AC-003:2","input":"{&a}{?b}{?c}{b}","expected":[{"code":"UT102","',
    'col":1,"text":"no query started before this: use \\"?\\" instead of \\"&',
    '\\""},{"code":"UT101","col":9,"text":"query already started: use \\"&\\"',
    ' instead of \\"?\\""},{"code":"UT104","col":14,"text":"variable \\"b\\" ',
    'appears again (first at column 7)"}]},',
    '{"id":"AC-003:3","input":"?{&a}{?b}","expected":[{"code":"UT101","col":6',
    ',"text":"query already started: use \\"&\\" instead of \\"?\\""}]},',
    '{"id":"AC-003:4","input":"%3F{&a}","expected":[{"code":"UT102","col":4,"',
    'text":"no query started before this: use \\"?\\" instead of \\"&\\""}]},',
    '{"id":"AC-003:5","input":"{?a}{#b}{?c}","expected":[{"code":"UT101","col',
    '":9,"text":"query already started: use \\"&\\" instead of \\"?\\""}]},',
    '{"id":"AC-003:6","input":"#{&a}","expected":[{"code":"UT102","col":2,"te',
    'xt":"no query started before this: use \\"?\\" instead of \\"&\\""}]},',
    '{"id":"AC-003:7","input":"{?a}{&b}","expected":[]}]',
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


import pytest

from uritpl.lines import split_lines
from uritpl.rules import find_problems


def acceptance_actual(input):
    return [
        {"col": problem.col, "code": problem.code, "text": problem.text}
        for problem in find_problems(input)
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", []),
        ("\n\n", ["", ""]),
        ("a\n\n{b\n", ["a", "", "{b"]),
        ("/a{b}\r\n/c{d}\r\n", ["/a{b}", "/c{d}"]),
        ("x\ry\n", ["x\ry"]),
        ("x\r", ["x\r"]),
        ("x\r\r\n", ["x\r"]),
        ("\ufeffa\u0085b\u2028c\u2029d\u3000e", ["\ufeffa\u0085b\u2028c\u2029d\u3000e"]),
    ],
)
def test_split_lines_only_cuts_at_lf_and_retains_physical_empty_lines(text, expected):
    assert split_lines(text) == expected


def test_split_lines_retains_an_empty_physical_line_between_lines():
    assert split_lines("a\n\n{b\n") == ["a", "", "{b"]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "100%/%41/%4/%zz/%",
            [
                {
                    "col": 4,
                    "code": "UT103",
                    "text": "literal character U+0025 will be percent-encoded",
                }
            ],
        ),
        ("%41%2f", []),
        (
            "e\u200bf\u200b",
            [
                {
                    "col": 2,
                    "code": "UT103",
                    "text": "literal character U+200B will be percent-encoded",
                }
            ],
        ),
        (
            "a\u2028b\u2029c\u0085d\u3000e",
            [
                {
                    "col": 2,
                    "code": "UT103",
                    "text": "literal character U+2028 will be percent-encoded",
                },
                {
                    "col": 4,
                    "code": "UT103",
                    "text": "literal character U+2029 will be percent-encoded",
                },
                {
                    "col": 6,
                    "code": "UT103",
                    "text": "literal character U+0085 will be percent-encoded",
                },
                {
                    "col": 8,
                    "code": "UT103",
                    "text": "literal character U+3000 will be percent-encoded",
                },
            ],
        ),
        (
            "\ufeff/a",
            [
                {
                    "col": 1,
                    "code": "UT103",
                    "text": "literal character U+FEFF will be percent-encoded",
                }
            ],
        ),
        (
            "/c\u00a0d",
            [
                {
                    "col": 3,
                    "code": "UT103",
                    "text": "literal character U+00A0 will be percent-encoded",
                }
            ],
        ),
        (
            "g\rh",
            [
                {
                    "col": 2,
                    "code": "UT103",
                    "text": "literal character U+000D will be percent-encoded",
                }
            ],
        ),
        (
            "😀{a}{a}",
            [
                {
                    "col": 1,
                    "code": "UT103",
                    "text": "literal character U+1F600 will be percent-encoded",
                },
                {
                    "col": 6,
                    "code": "UT104",
                    "text": 'variable "a" appears again (first at column 3)',
                },
            ],
        ),
        (
            "{a,a*,a:2}",
            [
                {
                    "col": 4,
                    "code": "UT104",
                    "text": 'variable "a" appears again (first at column 2)',
                },
                {
                    "col": 7,
                    "code": "UT104",
                    "text": 'variable "a" appears again (first at column 2)',
                },
            ],
        ),
        (
            "{%41}{A}{%41}",
            [
                {
                    "col": 10,
                    "code": "UT104",
                    "text": 'variable "%41" appears again (first at column 2)',
                }
            ],
        ),
        (
            "/x y/{id}{id}",
            [
                {
                    "col": 3,
                    "code": "UT103",
                    "text": "literal character U+0020 will be percent-encoded",
                },
                {
                    "col": 11,
                    "code": "UT104",
                    "text": 'variable "id" appears again (first at column 7)',
                },
            ],
        ),
        ("/a?b=c#d", []),
    ],
)
def test_semantic_rule_examples_have_literal_expected_problems(line, expected):
    assert acceptance_actual(line) == expected


def test_empty_valid_text_has_no_problems():
    assert find_problems("") == []
    assert find_problems("/users{/id}{?q}") == []


def test_semantic_state_resets_between_lines():
    assert acceptance_actual("?{a}\u200b") == [
        {"col": 5, "code": "UT103", "text": "literal character U+200B will be percent-encoded"}
    ]
    assert acceptance_actual("{?a}") == []
    assert acceptance_actual("{a}") == []
    assert acceptance_actual("{a}") == []


def test_repeated_changed_literal_character_across_segments_is_reported_once():
    assert acceptance_actual("e\u200b{a}\u200bf") == [
        {"col": 2, "code": "UT103", "text": "literal character U+200B will be percent-encoded"}
    ]


def test_valid_percent_triplet_does_not_mask_later_bad_percent():
    assert acceptance_actual("%41%4") == [
        {"col": 4, "code": "UT103", "text": "literal character U+0025 will be percent-encoded"}
    ]
