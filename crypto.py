import secrets

MASK32 = 0xFFFFFFFF
CHACHA_ROUNDS = 20
CHACHA_CONST = (0x61707865, 0x3320646e, 0x79622d32, 0x6b206574)

def rotl32(x, n):
    x &= MASK32
    return ((x << n) | (x >> (32 - n))) & MASK32

def quarter_round(s, a, b, c, d):
    s[a] = (s[a] + s[b]) & MASK32
    s[d] ^= s[a]
    s[d] = rotl32(s[d], 16)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] ^= s[c]
    s[b] = rotl32(s[b], 12)
    s[a] = (s[a] + s[b]) & MASK32
    s[d] ^= s[a]
    s[d] = rotl32(s[d], 8)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] ^= s[c]
    s[b] = rotl32(s[b], 7)

def chacha_block(key, counter, nonce):
    state = list(CHACHA_CONST) + list(key) + [counter] + list(nonce)
    w = state[:]
    for _ in range(CHACHA_ROUNDS // 2):
        quarter_round(w, 0, 4, 8, 12)
        quarter_round(w, 1, 5, 9, 13)
        quarter_round(w, 2, 6, 10, 14)
        quarter_round(w, 3, 7, 11, 15)
        quarter_round(w, 0, 5, 10, 15)
        quarter_round(w, 1, 6, 11, 12)
        quarter_round(w, 2, 7, 8, 13)
        quarter_round(w, 3, 4, 9, 14)
    return [(w[i] + state[i]) & MASK32 for i in range(16)]

def keystream(key, nonce_lo, nonce_hi, n):
    out = bytearray()
    counter = 0
    while len(out) < n:
        words = chacha_block(key, counter, (0, nonce_lo, nonce_hi))
        for wv in words:
            out += wv.to_bytes(4, "little")
        counter = (counter + 1) & MASK32
    return bytes(out[:n])

def make_seeds():
    key = tuple(secrets.randbits(32) for _ in range(8))
    return {
        "KEY": key,
        "NONCE_BASE": secrets.randbits(32),
        "MK": secrets.randbits(32),
    }

def build_alphabet(key, nonce_base):
    chars = [chr(i) for i in range(33, 127) if i not in (34, 39, 92)]
    nonce_lo, nonce_hi = derive_nonce(0xA5A5A5A5, key, nonce_base)
    ks = keystream(key, nonce_lo, nonce_hi, len(chars) * 4)
    for i in range(len(chars) - 1, 0, -1):
        v = int.from_bytes(ks[i * 4:i * 4 + 4], "little")
        j = v % (i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)

def derive_nonce(call_id, key, nonce_base):
    words = chacha_block(key, call_id & MASK32, (nonce_base, 0xC2B2AE35, 0x9E3779B9))
    return words[0] & MASK32, words[1] & MASK32

def encode_string(text, call_id, seeds):
    key = seeds["KEY"]
    alphabet = build_alphabet(key, seeds["NONCE_BASE"])
    N = len(alphabet)
    data = bytes(ord(c) & 0xFF for c in text)
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"])
    ks = keystream(key, nonce_lo, nonce_hi, len(data))
    encrypted = bytes(b ^ k for b, k in zip(data, ks))
    result = []
    for b in encrypted:
        hi = b // N
        lo = b % N
        if hi >= N or lo >= N:
            return None
        result.append(alphabet[hi])
        result.append(alphabet[lo])
    return "".join(result)

def decode_string(encoded, call_id, seeds):
    key = seeds["KEY"]
    alphabet = build_alphabet(key, seeds["NONCE_BASE"])
    N = len(alphabet)
    ra = {c: i for i, c in enumerate(alphabet)}
    encrypted = bytearray()
    for i in range(0, len(encoded), 2):
        h = ra.get(encoded[i])
        l = ra.get(encoded[i + 1])
        if h is None or l is None:
            return None
        encrypted.append(h * N + l)
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"])
    ks = keystream(key, nonce_lo, nonce_hi, len(encrypted))
    data = bytes(b ^ k for b, k in zip(encrypted, ks))
    return "".join(chr(b) for b in data)

def encrypt_bytes(data, call_id, seeds):
    key = seeds["KEY"]
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"])
    ks = keystream(key, nonce_lo, nonce_hi, len(data))
    return bytes(b ^ k for b, k in zip(data, ks))
    
