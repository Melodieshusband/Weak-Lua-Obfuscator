import struct
import secrets

MLTN_MAGIC = b'MLTN'
MLTN_VERSION = 1

TYPE_NIL      = 0
TYPE_BOOL     = 1
TYPE_NUMBER   = 2
TYPE_STRING   = 3
TYPE_FUNC     = 4
TYPE_SMALLINT = 5
TYPE_FLOAT32  = 6

def write_uvarint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def read_uvarint(data, i):
    shift = 0
    result = 0
    while True:
        b = data[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, i

def roll_lcg_step(state):
    return (state * 1103515245 + 12345) & 0xFF

def next_byte_mask(state, prev):
    new_state = roll_lcg_step(state)
    mask = (new_state ^ ((prev * 31) & 0xFF)) & 0xFF
    return new_state, mask

class MltnCipherStream:
    def __init__(self, seed):
        self.state = seed & 0xFF
        self.prev = seed & 0xFF

    def next_mask(self):
        self.state, mask = next_byte_mask(self.state, self.prev)
        self.prev = mask
        return mask

    def process(self, data):
        out = bytearray(len(data))
        for i, byte in enumerate(data):
            out[i] = byte ^ self.next_mask()
        return bytes(out)

RLE_MIN_RUN = 4
RLE_MAX_RUN = 255

def pick_repeat_marker(used_values):
    used = set(used_values)
    for v in range(256):
        if v not in used:
            return v
    raise ValueError("no free byte value available for RLE marker")

def pick_two_markers(used_values):
    used = set(used_values)
    found = []
    for v in range(256):
        if v not in used:
            found.append(v)
            if len(found) == 2:
                return found[0], found[1]
    raise ValueError("not enough free byte values for RLE+DICT markers")

def rle_encode_ops(op_list, marker, dict_marker=None):
    out = []
    i = 0
    n = len(op_list)
    while i < n:
        op = op_list[i]
        run = 1
        while i + run < n and op_list[i + run] == op and run < RLE_MAX_RUN:
            run += 1
        if dict_marker is not None and run == dict_marker:
            run -= 1
        if run >= RLE_MIN_RUN and op != marker:
            out.append(marker)
            out.append(op)
            out.append(run)
            i += run
        else:
            if op == marker:
                out.append(marker)
                out.append(op)
                out.append(1)
                i += 1
            else:
                out.append(op)
                i += 1
    return out

def rle_decode_ops(stream, marker):
    out = []
    i = 0
    n = len(stream)
    while i < n:
        v = stream[i]
        if v == marker:
            op = stream[i + 1]
            run = stream[i + 2]
            out.extend([op] * run)
            i += 3
        else:
            out.append(v)
            i += 1
    return out

def _split_atoms(stream, marker):
    atoms = []
    i = 0
    n = len(stream)
    while i < n:
        if stream[i] == marker:
            atoms.append(tuple(stream[i:i + 3]))
            i += 3
        else:
            atoms.append((stream[i],))
            i += 1
    return atoms

def _atoms_to_stream(atoms):
    out = []
    for a in atoms:
        out.extend(a)
    return out

DICT_MIN_PATTERN = 2
DICT_MAX_PATTERN = 4
DICT_MIN_OCCURRENCES = 3
DICT_MAX_ENTRIES = 63

def build_dictionary(atoms):
    from collections import Counter
    counts = Counter()
    n = len(atoms)
    for plen in range(DICT_MIN_PATTERN, DICT_MAX_PATTERN + 1):
        for i in range(n - plen + 1):
            pat = tuple(atoms[i:i + plen])
            counts[pat] += 1

    def score(item):
        pat, cnt = item
        elem_count = sum(len(a) for a in pat)
        saved = (elem_count - 1) * cnt
        return saved

    candidates = [item for item in counts.items() if item[1] >= DICT_MIN_OCCURRENCES]
    candidates.sort(key=score, reverse=True)

    chosen = []
    for pat, cnt in candidates:
        if len(chosen) >= DICT_MAX_ENTRIES:
            break
        overlaps = False
        for other, _ in chosen:
            if pat == other:
                overlaps = True
                break
        if not overlaps:
            chosen.append((pat, cnt))
    return [pat for pat, _ in chosen]

def dict_encode_atoms(atoms, dictionary, dict_marker):
    if not dictionary:
        return _atoms_to_stream(atoms)
    index_of = {pat: idx for idx, pat in enumerate(dictionary)}
    max_plen = max(len(p) for p in dictionary)
    out = []
    i = 0
    n = len(atoms)
    while i < n:
        matched = False
        for plen in range(min(max_plen, n - i), DICT_MIN_PATTERN - 1, -1):
            window = tuple(atoms[i:i + plen])
            if window in index_of:
                out.append(dict_marker)
                out.append(index_of[window])
                out.append(plen)
                i += plen
                matched = True
                break
        if not matched:
            out.extend(atoms[i])
            i += 1
    return out

def dict_decode_stream(stream, dict_marker, dictionary):
    out = []
    i = 0
    n = len(stream)
    while i < n:
        v = stream[i]
        if v == dict_marker:
            idx = stream[i + 1]
            plen = stream[i + 2]
            pat = dictionary[idx]
            for atom in pat:
                out.extend(atom)
            i += 3
        else:
            out.append(v)
            i += 1
    return out

def serialize_dictionary(dictionary, marker):
    body = bytearray()
    body += write_uvarint(len(dictionary))
    for pat in dictionary:
        flat = _atoms_to_stream(pat)
        body += write_uvarint(len(flat))
        body += bytes(flat)
    return bytes(body)

def encode_opcode_chain(op_list, proto_seed, marker=None, dict_marker=None, dictionary=None):
    if marker is None:
        stream = op_list
    else:
        rle_stream = rle_encode_ops(op_list, marker, dict_marker)
        if dict_marker is not None and dictionary:
            atoms = _split_atoms(rle_stream, marker)
            stream = dict_encode_atoms(atoms, dictionary, dict_marker)
        else:
            stream = rle_stream
    state = proto_seed & 0xFF
    prev = proto_seed & 0xFF
    out = []
    for op in stream:
        state, mask = next_byte_mask(state, prev)
        enc = (op ^ mask) & 0xFF
        out.append(enc)
        prev = op & 0xFF
    return out

def encode_const_plain(val):
    if val is None:
        return bytes([TYPE_NIL])
    if isinstance(val, bool):
        return bytes([TYPE_BOOL, 1 if val else 0])
    if isinstance(val, int) and -128 <= val <= 127:
        return bytes([TYPE_SMALLINT, val & 0xFF])
    if isinstance(val, (int, float)):
        fval = float(val)
        try:
            f32_roundtrip = struct.unpack('<f', struct.pack('<f', fval))[0]
        except OverflowError:
            f32_roundtrip = None
        if f32_roundtrip == fval and fval == fval:
            return bytes([TYPE_FLOAT32]) + struct.pack('<f', fval)
        return bytes([TYPE_NUMBER]) + struct.pack('<d', fval)
    if isinstance(val, str):
        enc = val.encode('utf-8')
        return bytes([TYPE_STRING]) + write_uvarint(len(enc)) + enc
    return bytes([TYPE_NIL])

def encode_const_block(consts, const_seed):
    body = bytearray()
    for c in consts:
        body += encode_const_plain(c)
    cipher = MltnCipherStream(const_seed)
    return cipher.process(bytes(body))

def encode_instruction_fields(a=None, b=None, c=None):
    out = bytearray()
    for v in (a, b, c):
        if v is not None:
            out += write_uvarint(v & 0xFFFFFFFF)
    return bytes(out)

def gen_seed():
    return secrets.randbelow(256)

def write_enc_uvarint(n, seed=None):
    if seed is None:
        seed = gen_seed()
    plain = write_uvarint(n)
    cipher = MltnCipherStream(seed)
    enc = cipher.process(plain)
    return bytes([seed]) + enc

def read_enc_uvarint(data, i):
    seed = data[i]
    i += 1
    state = seed & 0xFF
    prev = seed & 0xFF
    result = 0
    shift = 0
    while True:
        raw = data[i]
        i += 1
        state, mask = next_byte_mask(state, prev)
        b = raw ^ mask
        prev = mask & 0xFF
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, i
