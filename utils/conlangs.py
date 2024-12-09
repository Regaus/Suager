# noinspection SpellCheckingInspection
def rsl_number(value: int, language: str):
    """ Convert number to RSL-1 """
    # limit = int("9" * 36)
    limit = 10 ** 36 - 1  # 16 ** 72 - 1 if base == 16 else
    limit_str = "10^36 - 1"  # "4.97 x 10^86" if base == 16 else
    # if base not in [10, 16]:
    #     return "Error: Only base-10 and base-16 are supported."
    if value > limit:
        return f"Error: Highest allowed number is {limit_str}."
    if value < 0:
        return "Error: Negative values are not supported."
    numbers = {
        "re": {
            0: "inti",
            1:  {1: "ukka", 2: "devi", 3: "teri", 4: "segi", 5: "paki", 6: "senki", 7: "eki", 8: "oni", 9: "zeki", 10: "veri"},
            21: {1: "ukku", 2: "devu", 3: "teru", 4: "segu", 5: "paku", 6: "senku", 7: "eku", 8: "onu", 9: "zeku"},
            11: {11: "uveri", 12: "deveri", 13: "teveri", 14: "severi", 15: "paveri", 16: "seneri", 17: "everi", 18: "overi", 19: "zeveri"},

            10: {2: "devere", 3: "tevere", 4: "segere", 5: "pavere", 6: "senere", 7: "evere", 8: "onere", 9: "zevere"},
            20: {2: "devere", 3: "tevere", 4: "segere", 5: "pavere", 6: "senere", 7: "nevere", 8: "nonere", 9: "zevere"},

            100:  ["arja",  "arjain"],
            1000: ["kirraa", "kirrain"],
            1000000: ["ukkaristu",   "devaristu",   "teraristu",   "segaristu",   "pakaristu",   "senkaristu",   "ekaristu",   "onaristu",   "zekaristu",   "veraristu"],
            2000000: ["ukkaristain", "devaristain", "teraristain", "segaristain", "pakaristain", "senkaristain", "ekaristain", "onaristain", "zekaristain", "veraristain"]
        },
    }
    if language not in numbers:
        return f"Error: `{language}` is not a supported language."
    if value == 0:
        return numbers[language][0]
    _ten, _11, _20, _hundred, _thousand = (10, 11, 20, 100, 1000)  # (16, 17, 32, 256, 65536) if base == 16 else
    _numbers = numbers[language]  # [base]

    def hundred(_val: int):
        if _val <= _ten:
            _99v = _numbers[1][_val]
        elif _11 <= _val < _20:
            _99v = _numbers[11][_val]
        else:
            _v, _u = divmod(_val, _ten)
            _99v = f"{_numbers[21][_u]}{_numbers[20][_v]}" if _u > 0 else _numbers[10][_v]
        return _99v

    def thousand(_val: int):
        _999 = _val % _thousand
        _99 = _999 % _hundred
        _99v = hundred(_99)
        _100 = _999 // _hundred
        _100v = "" if _100 == 0 else ((f"{_numbers[1][1]} {_numbers[100][0]}" if _100 == 1 else f"{hundred(_100)} {_numbers[100][1]}") + (", " if _99 != 0 else ""))
        return _100v + _99v

    _1000 = value % _thousand
    outputs = [thousand(_1000)] if _1000 > 0 else []
    large = []
    _value = value
    _range = len(_numbers[1000000]) + 1
    for i in range(_range):
        _value //= _thousand
        large.append(_value % _thousand)
    for i in range(_range):
        val = large[i]
        if val > 0:
            n1, n2 = _numbers[1000] if i == 0 else (_numbers[1000000][i - 1], _numbers[2000000][i - 1])
            name = n1 if val % _hundred == 1 else n2
            outputs.append(f"{'ukkar' if (val == 1 and i != 0) else thousand(val)} {name}")
    return ", ".join(outputs[::-1])
