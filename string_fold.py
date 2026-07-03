import re

def match_long_bracket_open(source, i, n):
    if source[i] != '[':
        return None
    j = i + 1
    level = 0
    while j < n and source[j] == '=':
        level += 1
        j += 1
    if j < n and source[j] == '[':
        return level, j + 1
    return None

def find_long_bracket_close(source, i, n, level):
    close = ']' + ('=' * level) + ']'
    idx = source.find(close, i)
    if idx == -1:
        return n, n
    return idx, idx + len(close)

def extract_strings(source):
    found = []
    i = 0
    n = len(source)
    while i < n:
        if source[i] == '-' and i + 1 < n and source[i+1] == '-':
            bracket = match_long_bracket_open(source, i + 2, n)
            if bracket is not None:
                level, content_start = bracket
                if content_start < n and source[content_start] == '\n':
                    content_start += 1
                close_start, close_end = find_long_bracket_close(source, content_start, n, level)
                i = close_end
            else:
                while i < n and source[i] != '\n':
                    i += 1
            continue
        bracket = match_long_bracket_open(source, i, n)
        if bracket is not None:
            level, content_start = bracket
            start = i
            cs = content_start
            if cs < n and source[cs] == '\n':
                cs += 1
            close_start, close_end = find_long_bracket_close(source, cs, n, level)
            value = source[cs:close_start]
            found.append((start, close_end, value))
            i = close_end
            continue
        if source[i] in ('"', "'"):
            q = source[i]
            start = i
            i += 1
            s = []
            while i < n and source[i] != q:
                if source[i] == '\\' and i + 1 < n:
                    esc_map = {'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"',"'":"'",'0':'\0','a':'\a','b':'\b','f':'\f','v':'\v'}
                    i += 1
                    if source[i].isdigit():
                        j = i
                        while i < n and i - j < 3 and source[i].isdigit():
                            i += 1
                        s.append(chr(int(source[j:i])))
                        continue
                    s.append(esc_map.get(source[i], source[i]))
                    i += 1
                else:
                    s.append(source[i])
                    i += 1
            i += 1
            found.append((start, i, ''.join(s)))
            continue
        i += 1
    return found

def fold_strings(source, encode_fn, var_k, rng):
    strings = extract_strings(source)
    if not strings:
        return source
    result = []
    prev = 0
    for start, end, value in strings:
        result.append(source[prev:start])
        enc, cid = encode_fn(value)
        s0 = rng.randint(100000, 2**31 - 1)
        s2 = rng.randint(100000, 2**31 - 1)
        s3 = rng.randint(100000, 2**31 - 1)
        result.append(f'{var_k}("{enc}",1,{s0},{cid},{cid},{s2},{s3})')
        prev = end
    result.append(source[prev:])
    return ''.join(result)
    
