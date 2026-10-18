import secrets
import zlib

MASK32 = 0xFFFFFFFF
CHACHA_ROUNDS = 20
CHACHA_CONST = (0x61707865, 0x3320646e, 0x79622d32, 0x6b206574)
DEFAULT_ROT = (16, 12, 8, 7)

def rotl32(x, n):
    x &= MASK32
    n &= 31
    if n == 0:
        return x
    return ((x << n) | (x >> (32 - n))) & MASK32

def quarter_round(s, a, b, c, d, rot=DEFAULT_ROT):
    r1, r2, r3, r4 = rot
    s[a] = (s[a] + s[b]) & MASK32
    s[d] ^= s[a]
    s[d] = rotl32(s[d], r1)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] ^= s[c]
    s[b] = rotl32(s[b], r2)
    s[a] = (s[a] + s[b]) & MASK32
    s[d] ^= s[a]
    s[d] = rotl32(s[d], r3)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] ^= s[c]
    s[b] = rotl32(s[b], r4)

def chacha_block(key, counter, nonce, const=CHACHA_CONST, rot=DEFAULT_ROT):
    state = list(const) + list(key) + [counter] + list(nonce)
    w = state[:]
    for _ in range(CHACHA_ROUNDS // 2):
        quarter_round(w, 0, 4, 8, 12, rot)
        quarter_round(w, 1, 5, 9, 13, rot)
        quarter_round(w, 2, 6, 10, 14, rot)
        quarter_round(w, 3, 7, 11, 15, rot)
        quarter_round(w, 0, 5, 10, 15, rot)
        quarter_round(w, 1, 6, 11, 12, rot)
        quarter_round(w, 2, 7, 8, 13, rot)
        quarter_round(w, 3, 4, 9, 14, rot)
    return [(w[i] + state[i]) & MASK32 for i in range(16)]

def keystream(key, nonce_lo, nonce_hi, n, const=CHACHA_CONST, rot=DEFAULT_ROT):
    out = bytearray()
    counter = 0
    while len(out) < n:
        words = chacha_block(key, counter, (0, nonce_lo, nonce_hi), const, rot)
        for wv in words:
            out += wv.to_bytes(4, "little")
        counter = (counter + 1) & MASK32
    return bytes(out[:n])

def random_rot(rng):
    pool = list(range(1, 32))
    rng.shuffle(pool)
    return tuple(pool[:4])

def make_seeds():
    key = tuple(secrets.randbits(32) for _ in range(8))
    rng = secrets.SystemRandom()
    return {
        "KEY": key,
        "NONCE_BASE": secrets.randbits(32),
        "MK": secrets.randbits(32),
        "CC": tuple(secrets.randbits(32) for _ in range(4)),
        "ROT": random_rot(rng),
    }

def build_alphabet(key, nonce_base, const=CHACHA_CONST, rot=DEFAULT_ROT):
    chars = [chr(i) for i in range(33, 127) if i not in (34, 39, 92)]
    nonce_lo, nonce_hi = derive_nonce(0xA5A5A5A5, key, nonce_base, const, rot)
    ks = keystream(key, nonce_lo, nonce_hi, len(chars) * 4, const, rot)
    for i in range(len(chars) - 1, 0, -1):
        v = int.from_bytes(ks[i * 4:i * 4 + 4], "little")
        j = v % (i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)

def derive_nonce(call_id, key, nonce_base, const=CHACHA_CONST, rot=DEFAULT_ROT):
    words = chacha_block(key, call_id & MASK32, (nonce_base, 0xC2B2AE35, 0x9E3779B9), const, rot)
    return words[0] & MASK32, words[1] & MASK32

def base91_encode(data, alphabet):
    b = 0
    nbits = 0
    out = []
    for byte in data:
        b |= byte << nbits
        nbits += 8
        if nbits > 13:
            v = b & 8191
            if v > 88:
                b >>= 13
                nbits -= 13
            else:
                v = b & 16383
                b >>= 14
                nbits -= 14
            out.append(alphabet[v % 91])
            out.append(alphabet[v // 91])
    if nbits:
        out.append(alphabet[b % 91])
        if nbits > 7 or b > 90:
            out.append(alphabet[b // 91])
    return "".join(out)

def base91_decode(encoded, ra):
    b = 0
    nbits = 0
    v = -1
    out = bytearray()
    for ch in encoded:
        c = ra.get(ch)
        if c is None:
            return None
        if v < 0:
            v = c
        else:
            v += c * 91
            b |= v << nbits
            nbits += 13 if (v & 8191) > 88 else 14
            while nbits >= 8:
                out.append(b & 255)
                b >>= 8
                nbits -= 8
            v = -1
    if v >= 0:
        out.append((b | (v << nbits)) & 255)
    return bytes(out)

def deflate_compress(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    return co.compress(data) + co.flush()

def deflate_decompress(data):
    do = zlib.decompressobj(-15)
    return do.decompress(data) + do.flush()

def pack_payload(raw, allow_compress=True):
    if allow_compress:
        compressed = deflate_compress(raw)
        if len(compressed) < len(raw):
            return b"\x01" + compressed
    return b"\x00" + raw

def unpack_payload(payload):
    if not payload:
        return b""
    flag = payload[0]
    body = payload[1:]
    if flag == 1:
        return deflate_decompress(body)
    return body

def encode_string(text, call_id, seeds, allow_compress=True):
    key = seeds["KEY"]
    const = seeds.get("CC", CHACHA_CONST)
    rot = seeds.get("ROT", DEFAULT_ROT)
    alphabet = build_alphabet(key, seeds["NONCE_BASE"], const, rot)
    if len(alphabet) != 91:
        return None
    payload = pack_payload(text.encode("utf-8"), allow_compress=allow_compress)
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"], const, rot)
    ks = keystream(key, nonce_lo, nonce_hi, len(payload), const, rot)
    encrypted = bytes(b ^ k for b, k in zip(payload, ks))
    return base91_encode(encrypted, alphabet)

def decode_string(encoded, call_id, seeds):
    key = seeds["KEY"]
    const = seeds.get("CC", CHACHA_CONST)
    rot = seeds.get("ROT", DEFAULT_ROT)
    alphabet = build_alphabet(key, seeds["NONCE_BASE"], const, rot)
    ra = {c: i for i, c in enumerate(alphabet)}
    encrypted = base91_decode(encoded, ra)
    if encrypted is None:
        return None
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"], const, rot)
    ks = keystream(key, nonce_lo, nonce_hi, len(encrypted), const, rot)
    payload = bytes(b ^ k for b, k in zip(encrypted, ks))
    data = unpack_payload(payload)
    return data.decode("utf-8", errors="surrogateescape")

def encrypt_bytes(data, call_id, seeds):
    key = seeds["KEY"]
    const = seeds.get("CC", CHACHA_CONST)
    rot = seeds.get("ROT", DEFAULT_ROT)
    nonce_lo, nonce_hi = derive_nonce(call_id, key, seeds["NONCE_BASE"], const, rot)
    ks = keystream(key, nonce_lo, nonce_hi, len(data), const, rot)
    return bytes(b ^ k for b, k in zip(data, ks))
    
