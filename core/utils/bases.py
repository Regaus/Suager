import string


def base_6(value: int) -> str:
    return to_base(value, 6, False)


def from_base(value: str, base: int) -> int:
    return int(value, base=base)


def to_base(value, base: int, caps: bool = False) -> str:
    value = int(value)
    if value < 0:
        return "-" + to_base(value * -1, base, caps)
    out = ""
    values = string.digits + (string.ascii_uppercase if caps else string.ascii_lowercase)
    while value > 0:
        out = f"{values[value % base]}{out}"
        value //= base
    return out if out else "0"


def to_base_float(value: float, base: int, precision: int = 2, caps: bool = False):
    if value < 0:
        return "-" + to_base_float(value * -1, base, precision, caps)
    if value.is_integer() or precision < 1:
        return to_base(int(value), base, caps)
    else:
        out = f"{to_base(int(value), base, caps)}."
        value %= 1
        values = string.digits + (string.ascii_uppercase if caps else string.ascii_lowercase)
        for i in range(1, precision + 1):
            part = (value * base ** i) % base
            # print(part)
            out += values[int(part)]
            # out += str(int(value * base ** i) % base * 10 ** (-i))
        return out
