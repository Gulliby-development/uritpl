import pytest

from uritpl.charset import RESERVED, UNRESERVED, is_reserved, is_unreserved, triplet_at
from uritpl.io import Inputs, MemIo
from uritpl.percent import encode, encode_char


def _mem_io(text: str) -> MemIo:
    return MemIo(stdin=text.encode("utf-8"))


def test_charset_constants_are_exact_frozensets() -> None:
    assert type(UNRESERVED) is frozenset
    assert UNRESERVED == frozenset(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    )
    assert type(RESERVED) is frozenset
    assert RESERVED == frozenset(":/?#[]@!$&'()*+,;=")


@pytest.mark.parametrize(
    ("character", "expected_unreserved", "expected_reserved"),
    [
        ("A", True, False),
        ("z", True, False),
        ("0", True, False),
        ("9", True, False),
        ("-", True, False),
        (".", True, False),
        ("_", True, False),
        ("~", True, False),
        ("/", False, True),
        ("'", False, True),
        ("%", False, False),
        (" ", False, False),
        ("é", False, False),
        ("٣", False, False),
        (" ", False, False),
        ("😀", False, False),
    ],
)
def test_character_classification(
    character: str, expected_unreserved: bool, expected_reserved: bool
) -> None:
    source = Inputs(_mem_io(character)).read("-")
    assert is_unreserved(source.text) is expected_unreserved
    assert is_reserved(source.text) is expected_reserved


@pytest.mark.parametrize(
    ("text", "index", "expected"),
    [
        ("%41", 0, True),
        ("%2f", 0, True),
        ("%AF", 0, True),
        ("x%aFz", 1, True),
        ("%", 0, False),
        ("%4", 0, False),
        ("%zz", 0, False),
        ("%4G", 0, False),
        ("%٤1", 0, False),
        ("%Ｆ1", 0, False),
        ("41", 0, False),
        ("", 0, False),
        ("%41", 3, False),
        ("%41", -3, False),
        ("😀%41", 1, True),
    ],
)
def test_triplet_at(text: str, index: int, expected: bool) -> None:
    source = Inputs(_mem_io(text)).read("-")
    assert triplet_at(source.text, index) is expected


@pytest.mark.parametrize(
    ("character", "expected"),
    [
        ("A", "%41"),
        ("/", "%2F"),
        ("%", "%25"),
        (" ", "%20"),
        ("\u0000", "%00"),
        ("\t", "%09"),
        ("\n", "%0A"),
        ("\r", "%0D"),
        ("\u007f", "%7F"),
        ("é", "%C3%A9"),
        ("😀", "%F0%9F%98%80"),
    ],
)
def test_encode_char(character: str, expected: str) -> None:
    source = Inputs(_mem_io(character)).read("-")
    assert encode_char(source.text) == expected


def test_encode_char_preserves_nul_from_input_bytes() -> None:
    source = Inputs(MemIo(stdin=b"\x00")).read("-")
    assert source.text == "\x00"
    assert encode_char(source.text) == "%00"


@pytest.mark.parametrize(
    ("text", "allow_reserved", "expected"),
    [
        ("", False, ""),
        ("", True, ""),
        ("abc-._~XYZ019", False, "abc-._~XYZ019"),
        ("a b", False, "a%20b"),
        ("a/b?c#d", False, "a%2Fb%3Fc%23d"),
        ("a/b?c#d", True, "a/b?c#d"),
        (":/?#[]@!$&'()*+,;=", True, ":/?#[]@!$&'()*+,;="),
        (
            ":/?#[]@!$&'()*+,;=",
            False,
            "%3A%2F%3F%23%5B%5D%40%21%24%26%27%28%29%2A%2B%2C%3B%3D",
        ),
        ('{}\\^"<>', True, "%7B%7D%5C%5E%22%3C%3E"),
    ],
)
def test_encode_reserved_and_unreserved(text: str, allow_reserved: bool, expected: str) -> None:
    source = Inputs(_mem_io(text)).read("-")
    assert encode(source.text, allow_reserved) == expected


@pytest.mark.parametrize(
    ("text", "allow_reserved", "expected"),
    [
        ("%41", False, "%2541"),
        ("%41%4 %2f", True, "%41%254%20%2f"),
        ("%2f%AF", True, "%2f%AF"),
        ("%2f%AF", False, "%252f%25AF"),
        ("%4", True, "%254"),
        ("%zz/%", True, "%25zz/%25"),
        ("%%41", True, "%25%41"),
        ("%٤1", True, "%25%D9%A41"),
    ],
)
def test_encode_percent_sequences(text: str, allow_reserved: bool, expected: str) -> None:
    source = Inputs(_mem_io(text)).read("-")
    assert encode(source.text, allow_reserved) == expected


@pytest.mark.parametrize(
    ("text", "allow_reserved", "expected"),
    [
        ("\ufeff", False, "%EF%BB%BF"),
        ("\u200b\u00a0", False, "%E2%80%8B%C2%A0"),
        ("\u0085", True, "%C2%85"),
        ("\r", False, "%0D"),
        ("a\u2028b", False, "a%E2%80%A8b"),
        ("é😀", False, "%C3%A9%F0%9F%98%80"),
        ("a\u0085\u2028\u2029\u3000b", True, "a%C2%85%E2%80%A8%E2%80%A9%E3%80%80b"),
        ("\x00\t\n\r\x7f", True, "%00%09%0A%0D%7F"),
        ("e\u0301", True, "e%CC%81"),
    ],
)
def test_encode_controls_invisible_and_unicode(
    text: str, allow_reserved: bool, expected: str
) -> None:
    source = Inputs(_mem_io(text)).read("-")
    assert encode(source.text, allow_reserved) == expected


def test_encode_preserves_bom_from_input_bytes() -> None:
    source = Inputs(MemIo(stdin=b"\xef\xbb\xbf")).read("-")
    assert source.text == "\ufeff"
    assert encode(source.text, False) == "%EF%BB%BF"
