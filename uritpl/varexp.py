from uritpl.fault import Failure
from uritpl.model import Varspec
from uritpl.operators import Operator
from uritpl.percent import encode
from uritpl.text import show
from uritpl.value import Value, kind_of


def expand_varspec(op: Operator, spec: Varspec, value: Value) -> list[str]:
    """Return the contribution pieces for one defined variable value."""
    kind = kind_of(value)
    if kind == "string":
        text = value[: spec.length] if spec.modifier == "prefix" else value
        encoded = encode(text, op.allow_reserved)
        if not op.named:
            return [encoded]
        if text:
            return [f"{spec.name}={encoded}"]
        return [f"{spec.name}{op.ifemp}"]

    if spec.modifier == "prefix":
        article = "an" if kind == "object" else "a"
        raise Failure(f"variable {show(spec.name)}: prefix modifier on {article} {kind} value")

    if kind == "list":
        if spec.modifier != "explode":
            encoded = ",".join(encode(member, op.allow_reserved) for member in value)
            return [f"{spec.name}={encoded}" if op.named else encoded]

        pieces = []
        for member in value:
            encoded = encode(member, op.allow_reserved)
            if op.named:
                pieces.append(f"{spec.name}={encoded}" if member else f"{spec.name}{op.ifemp}")
            else:
                pieces.append(encoded)
        return pieces

    if spec.modifier != "explode":
        encoded_members = []
        for key, member in value.items():
            encoded_members.extend(
                (encode(key, op.allow_reserved), encode(member, op.allow_reserved))
            )
        encoded = ",".join(encoded_members)
        return [f"{spec.name}={encoded}" if op.named else encoded]

    pieces = []
    for key, member in value.items():
        encoded_key = encode(key, op.allow_reserved)
        encoded_member = encode(member, op.allow_reserved)
        if op.named:
            pieces.append(
                f"{encoded_key}={encoded_member}" if member else f"{encoded_key}{op.ifemp}"
            )
        else:
            pieces.append(f"{encoded_key}={encoded_member}")
    return pieces
