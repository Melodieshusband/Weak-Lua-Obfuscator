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

def encode_opcode_chain(op_list, proto_seed):
    state = proto_seed & 0xFF
    prev = proto_seed & 0xFF
    out = []
    for op in op_list:
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
        return bytes([TYPE_NUMBER]) + struct.pack('<d', float(val))
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
