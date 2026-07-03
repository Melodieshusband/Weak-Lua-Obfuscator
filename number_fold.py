import re

_NUMBER_RE = re.compile(r'0[xX][0-9a-fA-F]+|(?:\d+\.\d+|\.\d+|\d+)(?:[eE][+-]?\d+)?')
_IDENT_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')

def _is_ident_boundary_ok(source, start, end):
    if start > 0 and source[start-1] in _IDENT_CHARS:
        return False
    if end < len(source) and source[end] in _IDENT_CHARS:
        return False
    return True

def extract_numbers(source):
    found = []
    i = 0
    n = len(source)
    in_string = None
    in_long_bracket = None
    long_level = None
    while i < n:
        if in_string is not None:
            if source[i] == '\\' and i + 1 < n:
                i += 2
                continue
            if source[i] == in_string:
                in_string = None
            i += 1
            continue
        if in_long_bracket is not None:
            close = ']' + ('=' * long_level) + ']'
            if source[i:i+len(close)] == close:
                i += len(close)
                in_long_bracket = None
                long_level = None
            else:
                i += 1
            continue
        if source[i] == '-' and i + 1 < n and source[i+1] == '-':
            j = i + 2
            if j < n and source[j] == '[':
                k = j + 1
                level = 0
                while k < n and source[k] == '=':
                    level += 1
                    k += 1
                if k < n and source[k] == '[':
                    in_long_bracket = True
                    long_level = level
                    i = k + 1
                    continue
            while i < n and source[i] != '\n':
                i += 1
            continue
        if source[i] == '[' and i + 1 < n:
            j = i + 1
            level = 0
            while j < n and source[j] == '=':
                level += 1
                j += 1
            if j < n and source[j] == '[':
                in_long_bracket = True
                long_level = level
                i = j + 1
                continue
        if source[i] in ('"', "'"):
            in_string = source[i]
            i += 1
            continue
        if source[i].isdigit() or (source[i] == '.' and i + 1 < n and source[i+1].isdigit()):
            m = _NUMBER_RE.match(source, i)
            if m and _is_ident_boundary_ok(source, m.start(), m.end()):
                text = m.group(0)
                found.append((m.start(), m.end(), text))
                i = m.end()
                continue
        i += 1
    return found

def _parse_number(text):
    if text.lower().startswith('0x'):
        return int(text, 16), True
    if '.' in text or 'e' in text.lower():
        return float(text), False
    return int(text), False

def _make_expr(value, is_hex, rng):
    if isinstance(value, float) or not float(value).is_integer():
        return repr(value)
    ival = int(value)
    style = rng.randint(1, 4)
    if style == 1:
        a = rng.randint(1, 999999)
        b = ival - a
        return f"({a}+({b}))"
    elif style == 2:
        a = rng.randint(1, 999999)
        b = ival + a
        return f"({b}-{a})"
    elif style == 3 and ival != 0:
        a = rng.randint(2, 17)
        if ival % a == 0:
            return f"({a}*{ival // a})"
        a = rng.randint(1, 999999)
        b = ival - a
        return f"({a}+({b}))"
    else:
        a = rng.randint(1, 999999)
        b = ival - a
        return f"({a}+({b}))"

def fold_numbers(source, rng, min_value=2):
    numbers = extract_numbers(source)
    if not numbers:
        return source
    result = []
    prev = 0
    for start, end, text in numbers:
        value, is_hex = _parse_number(text)
        if isinstance(value, int) and abs(value) < min_value:
            continue
        result.append(source[prev:start])
        expr = _make_expr(value, is_hex, rng)
        result.append(expr)
        prev = end
    result.append(source[prev:])
    return ''.join(result)
  
