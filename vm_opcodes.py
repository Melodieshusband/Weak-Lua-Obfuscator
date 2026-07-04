import secrets

CANONICAL_OPS = {
    'LOAD_CONST':   0x01,
    'LOAD_VAR':     0x02,
    'SET_VAR':      0x03,
    'LOAD_GLOBAL':  0x04,
    'SET_GLOBAL':   0x05,
    'LOAD_UPVAL':   0x06,
    'SET_UPVAL':    0x07,
    'GET_TABLE':    0x08,
    'SET_TABLE':    0x09,
    'NEW_TABLE':    0x0A,
    'SET_LIST':     0x0B,
    'SET_LIST_MULTI': 0x0E,
    'GET_FIELD':    0x0C,
    'SET_FIELD':    0x0D,
    'ADD':          0x10,
    'SUB':          0x11,
    'MUL':          0x12,
    'DIV':          0x13,
    'MOD':          0x14,
    'POW':          0x15,
    'CONCAT':       0x16,
    'UNM':          0x17,
    'LEN':          0x18,
    'NOT':          0x19,
    'AND':          0x1A,
    'OR':           0x1B,
    'IDIV':         0x1C,
    'BAND':         0x1D,
    'BOR':          0x1E,
    'BXOR':         0x1F,
    'BNOT':         0x26,
    'SHL':          0x27,
    'SHR':          0x28,
    'EQ':           0x20,
    'NE':           0x21,
    'LT':           0x22,
    'LE':           0x23,
    'GT':           0x24,
    'GE':           0x25,
    'JUMP':         0x30,
    'JUMP_FALSE':   0x31,
    'JUMP_TRUE':    0x32,
    'JUMP_FALSE_NK':0x33,
    'JUMP_TRUE_NK': 0x34,
    'CALL':         0x40,
    'CALL_METHOD':  0x41,
    'RETURN':       0x42,
    'RETURN_NONE':  0x43,
    'VARARG':       0x44,
    'CLOSURE':      0x50,
    'CLOSE_UPVAL':  0x51,
    'FOR_PREP':     0x60,
    'FOR_LOOP':     0x61,
    'TFOR_CALL':    0x62,
    'TFOR_LOOP':    0x63,
    'POP':          0x70,
    'DUP':          0x71,
    'MOVE':         0x72,
}

def make_opmap():
    used = set()
    opmap = {}
    for name in CANONICAL_OPS:
        while True:
            v = secrets.randbelow(240) + 1
            if v not in used:
                used.add(v)
                opmap[name] = v
                break
    return opmap
    
