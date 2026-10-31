MASK32 = 0xFFFFFFFF

def joaat(s):
    h = 0
    for ch in s.lower():
        h = (h + ord(ch)) & MASK32
        h = (h + ((h << 10) & MASK32)) & MASK32
        h = (h ^ (h >> 6)) & MASK32
    h = (h + ((h << 3) & MASK32)) & MASK32
    h = (h ^ (h >> 11)) & MASK32
    h = (h + ((h << 15) & MASK32)) & MASK32
    if h >= 0x80000000:
        h -= 0x100000000
    return h

FIVEM_COMPOUND_OPS = {
    '+=': '+', '-=': '-', '*=': '*', '/=': '/',
    '^=': '^', '&=': '&', '|=': '|',
    '<<=': '<<', '>>=': '>>',
}
