import string


def base_6(value: int) -> str:
    return to_base(value, 6, False)


def from_base(value: str, base: int) -> int:
    return int(value, base=base)


def to_base(value, base: int, caps: bool = False) -> str:
    value = int(value)
    if value < 0:
        return "-" + to_base(value * -1, base)
    out = ""
    values = string.digits + (string.ascii_uppercase if caps else string.ascii_lowercase)
    while value > 0:
        out = f"{values[value % base]}{out}"
        value //= base
    return out if out else "0"
