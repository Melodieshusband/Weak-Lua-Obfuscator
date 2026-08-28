import mltn

MLD_MAGIC = b'MLD1'

FIELD_DICT_MIN_OCCURRENCES = 3
FIELD_DICT_MAX_ENTRIES = 63


def build_full_atoms(instructions):
    atoms = []
    for ins in instructions:
        fields = tuple(v & 0xFFFFFFFF for v in (ins.a, ins.b, ins.c) if v is not None)
        atoms.append((ins.op, fields))
    return atoms


def build_field_dictionary(atoms):
    from collections import Counter
    counts = Counter(atoms)
    candidates = [(a, cnt) for a, cnt in counts.items() if cnt >= FIELD_DICT_MIN_OCCURRENCES]
    def score(item):
        (op, fields), cnt = item
        return (len(fields) - 1) * cnt if len(fields) > 0 else 0
    candidates.sort(key=score, reverse=True)
    dictionary = [a for a, cnt in candidates[:FIELD_DICT_MAX_ENTRIES] if score((a, cnt)) > 0]
    return dictionary


def pick_field_dict_marker(used_op_bytes):
    used = set(used_op_bytes)
    for candidate in range(256):
        if candidate not in used:
            return candidate
    raise ValueError("no free byte value available for MLD field-dict marker")


def encode_instructions_with_field_dict(instructions, existing_op_values, field_dict_marker):
    atoms = build_full_atoms(instructions)
    dictionary = build_field_dictionary(atoms)
    dict_index = {a: idx for idx, a in enumerate(dictionary)}

    op_stream = []
    field_bytes = bytearray()
    for op, fields in atoms:
        idx = dict_index.get((op, fields))
        if idx is not None:
            op_stream.append(field_dict_marker)
            op_stream.append(idx)
        else:
            op_stream.append(op)
            for v in fields:
                field_bytes += mltn.write_uvarint(v)

    dict_body = bytearray()
    dict_body += mltn.write_uvarint(len(dictionary))
    for op, fields in dictionary:
        dict_body.append(op)
        dict_body.append(len(fields))
        for v in fields:
            dict_body += mltn.write_uvarint(v)

    return op_stream, bytes(field_bytes), bytes(dict_body)


def decode_dict_body(data, i=0):
    ndict, i = mltn.read_uvarint(data, i)
    dictionary = []
    for _ in range(ndict):
        op = data[i]; i += 1
        flen = data[i]; i += 1
        fields = []
        for _ in range(flen):
            v, i = mltn.read_uvarint(data, i)
            fields.append(v)
        dictionary.append((op, tuple(fields)))
    return dictionary, i
