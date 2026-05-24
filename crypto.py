import random
import secrets

LCG_MOD = 2147483647

def make_seeds():
    def rs():
        v = secrets.randbelow(LCG_MOD - 1) + 1
        return v
    return {
        "P":  rs(),
        "Q":  rs(),
        "R":  rs(),
        "S":  rs(),
        "T":  rs(),
        "U":  rs(),
        "BK": rs(),
        "A1": secrets.randbelow(65534) + 48271,
        "A2": secrets.randbelow(65534) + 48271,
    }

def lcg_next(s, a):
    return (s * a) % LCG_MOD

def build_alphabet(seed, a1):
    chars = [chr(i) for i in range(33, 127) if i not in (34, 39, 92)]
    v = seed
    for i in range(len(chars), 1, -1):
        v = lcg_next(v, a1)
        j = v % i
        chars[i - 1], chars[j] = chars[j], chars[i - 1]
    return "".join(chars)

def encode_string(text, call_id, seeds, alphabet_seed):
    a1 = seeds["A1"]
    a2 = seeds["A2"]
    alphabet = build_alphabet(alphabet_seed, a1)
    N = len(alphabet)
    data = [ord(c) for c in text]
    s0 = (seeds["T"] + call_id + seeds["P"]) % LCG_MOD
    s1 = (seeds["U"] + call_id + seeds["BK"] + seeds["Q"]) % LCG_MOD
    m3 = seeds["R"] % 256
    m4 = seeds["S"] % 256
    if s0 == 0: s0 = 1
    if s1 == 0: s1 = 1
    encrypted = []
    for i, byte in enumerate(data, 1):
        s0 = lcg_next(s0, a1)
        s1 = lcg_next(s1, a2)
        k = (s0 + s1 + m3 + m4 * i) % 256
        enc = (byte + k) % 256
        encrypted.append(enc)
        s0 = (s0 + enc) % LCG_MOD
    result = []
    for b in encrypted:
        hi = b // N
        lo = b % N
        if hi >= N or lo >= N:
            return None
        result.append(alphabet[hi])
        result.append(alphabet[lo])
    return "".join(result)

def decode_string(encoded, call_id, seeds, alphabet_seed):
    a1 = seeds["A1"]
    a2 = seeds["A2"]
    alphabet = build_alphabet(alphabet_seed, a1)
    N = len(alphabet)
    ra = {ord(c): i + 1 for i, c in enumerate(alphabet)}
    pairs = []
    for i in range(0, len(encoded), 2):
        h = ra.get(ord(encoded[i]))
        l = ra.get(ord(encoded[i + 1]))
        if h is None or l is None:
            return None
        pairs.append((h - 1) * N + (l - 1))
    s0 = (seeds["T"] + call_id + seeds["P"]) % LCG_MOD
    s1 = (seeds["U"] + call_id + seeds["BK"] + seeds["Q"]) % LCG_MOD
    m3 = seeds["R"] % 256
    m4 = seeds["S"] % 256
    if s0 == 0: s0 = 1
    if s1 == 0: s1 = 1
    result = []
    for i, enc in enumerate(pairs, 1):
        s0 = lcg_next(s0, a1)
        s1 = lcg_next(s1, a2)
        k = (s0 + s1 + m3 + m4 * i) % 256
        result.append(chr((enc - k) % 256))
        s0 = (s0 + enc) % LCG_MOD
    return "".join(result)
