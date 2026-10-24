from uritpl.charset import is_reserved, is_unreserved, triplet_at


def encode_char(ch: str) -> str:
    """Encode one Unicode scalar character as uppercase UTF-8 percent bytes."""
    return "".join(f"%{byte:02X}" for byte in ch.encode("utf-8"))


def encode(text: str, allow_reserved: bool) -> str:
    """Percent-encode text, optionally preserving reserved characters and triplets."""
    pieces: list[str] = []
    index = 0

    while index < len(text):
        character = text[index]
        if is_unreserved(character):
            pieces.append(character)
            index += 1
        elif allow_reserved and triplet_at(text, index):
            pieces.append(text[index : index + 3])
            index += 3
        elif allow_reserved and is_reserved(character):
            pieces.append(character)
            index += 1
        else:
            pieces.append(encode_char(character))
            index += 1

    return "".join(pieces)
