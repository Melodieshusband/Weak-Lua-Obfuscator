from vm import Instruction

MELODIE_DECOY = "Melodie doesn't approve of skidding be a good boy"

def _build_melodie_trap(proto, opmap, reg_base=0):
    print_const = proto.add_const("print")
    decoy_const = proto.add_const(MELODIE_DECOY)
    r_fn = reg_base
    r_arg = reg_base + 1
    ins = [
        Instruction(opmap['LOAD_GLOBAL'], r_fn, print_const),
        Instruction(opmap['LOAD_CONST'], r_arg, decoy_const),
        Instruction(opmap['CALL'], r_fn, 1, 0),
    ]
    jump_idx = len(ins)
    ins.append(Instruction(opmap['JUMP'], 0))
    return ins, jump_idx

JUMP_A_OPS = {'JUMP'}
JUMP_B_OPS = {'JUMP_FALSE', 'JUMP_TRUE', 'JUMP_FALSE_NK', 'JUMP_TRUE_NK',
              'FOR_PREP', 'FOR_LOOP', 'TFOR_LOOP'}
TERMINATOR_OPS = {'JUMP', 'RETURN', 'RETURN_NONE'}

ARITY_AB2 = {
    'LOAD_CONST', 'LOAD_VAR', 'SET_VAR', 'LOAD_GLOBAL', 'SET_GLOBAL', 'CLOSURE',
    'LOAD_UPVAL', 'SET_UPVAL',
    'RETURN', 'VARARG',
    'JUMP_FALSE', 'JUMP_TRUE', 'JUMP_FALSE_NK', 'JUMP_TRUE_NK',
    'UNM', 'LEN', 'NOT', 'BNOT',
    'FOR_PREP', 'FOR_LOOP', 'TFOR_LOOP',
    'DUP', 'MOVE',
}
ARITY_AB2C = {
    'GET_TABLE', 'SET_TABLE', 'SET_LIST',
    'SET_LIST_MULTI',
    'GET_FIELD', 'SET_FIELD',
    'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW', 'CONCAT', 'IDIV', 'AND', 'OR',
    'BAND', 'BOR', 'BXOR', 'SHL', 'SHR',
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'CALL', 'CALL_METHOD',
    'TFOR_CALL',
}
ARITY_A2 = {'NEW_TABLE', 'RETURN_NONE', 'POP', 'JUMP', 'CLOSE_UPVAL'}

JUNK_SAFE_NAMES = {
    'MOVE', 'DUP', 'UNM', 'LEN', 'NOT', 'BNOT',
    'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW', 'CONCAT', 'IDIV',
    'AND', 'OR', 'BAND', 'BOR', 'BXOR', 'SHL', 'SHR',
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'NEW_TABLE',
}

def _is_jump_a(name):
    return name in JUMP_A_OPS

def _is_jump_b(name):
    return name in JUMP_B_OPS

def _make_junk_instruction(rng, opmap, junk_names):
    name = rng.choice(junk_names)
    op = opmap[name]
    reg = lambda: rng.randint(0, 15)
    if name in ARITY_AB2:
        return Instruction(op, reg(), reg())
    if name in ARITY_AB2C:
        return Instruction(op, reg(), reg(), reg())
    return Instruction(op, reg())

def _split_blocks(instructions, rev_opmap):
    n = len(instructions)
    leaders = {0}
    for i, ins in enumerate(instructions):
        name = rev_opmap[ins.op]
        if _is_jump_a(name):
            leaders.add(ins.a)
            if i + 1 < n:
                leaders.add(i + 1)
        elif _is_jump_b(name):
            leaders.add(ins.b)
            if i + 1 < n:
                leaders.add(i + 1)
        elif name in ('RETURN', 'RETURN_NONE'):
            if i + 1 < n:
                leaders.add(i + 1)
    leaders = sorted(x for x in leaders if 0 <= x <= n)
    blocks = []
    for idx, start in enumerate(leaders):
        end = leaders[idx + 1] if idx + 1 < len(leaders) else n
        if end > start:
            blocks.append((start, end))
    return blocks

def _falls_through(instructions, end, rev_opmap, n):
    if end >= n or end == 0:
        return False
    last = instructions[end - 1]
    return rev_opmap[last.op] not in TERMINATOR_OPS

def flatten_bytecode(proto, rng, opmap):
    rev_opmap = {v: k for k, v in opmap.items()}
    _flatten_proto(proto, rng, rev_opmap, opmap)

def _flatten_proto(proto, rng, rev_opmap, opmap):
    for child in proto.protos:
        _flatten_proto(child, rng, rev_opmap, opmap)

    instructions = proto.instructions
    n = len(instructions)
    if n < 4:
        return

    blocks = _split_blocks(instructions, rev_opmap)
    if len(blocks) < 3:
        return

    old_to_block = {}
    for bi, (s, e) in enumerate(blocks):
        for i in range(s, e):
            old_to_block[i] = bi

    fallthrough_target = {}
    for bi, (s, e) in enumerate(blocks):
        if _falls_through(instructions, e, rev_opmap, n):
            nb = old_to_block.get(e)
            if nb is not None:
                fallthrough_target[bi] = nb

    entry_block = old_to_block.get(0, 0)
    order = [bi for bi in range(len(blocks)) if bi != entry_block]
    rng.shuffle(order)
    order = [entry_block] + order
    pos_of_block = {bi: pos for pos, bi in enumerate(order)}

    n_real = len(blocks)
    n_junk = min(max(2, n_real // 2), n_real)
    junk_names = [name for name in JUNK_SAFE_NAMES if name in opmap]
    if not junk_names:
        junk_names = [rev_opmap[op] for op in opmap.values()]

    slots = list(range(1, n_real + 1))
    rng.shuffle(slots)
    junk_after_slot = set(slots[:n_junk])
    junk_lengths = {slot: rng.randint(1, 3) for slot in junk_after_slot}

    melodie_slot = None
    has_print = 'LOAD_GLOBAL' in opmap and 'CALL' in opmap and junk_after_slot
    if has_print:
        melodie_slot = rng.choice(list(junk_after_slot))
        junk_lengths[melodie_slot] = 4

    needs_fallthrough_jump = {}
    for bi in range(n_real):
        if bi not in fallthrough_target:
            continue
        pos = pos_of_block[bi]
        next_pos = pos + 1
        target_bi = fallthrough_target[bi]
        is_immediately_next = (
            next_pos < n_real and
            order[next_pos] == target_bi and
            next_pos not in junk_after_slot
        )
        if not is_immediately_next:
            needs_fallthrough_jump[bi] = target_bi

    new_start_of_block = {}
    pc = 0
    layout = []
    for pos in range(n_real + 1):
        if pos in junk_after_slot:
            is_melodie = has_print and pos == melodie_slot
            layout.append(('junk', junk_lengths[pos], pc, is_melodie))
            pc += junk_lengths[pos]
        if pos < n_real:
            bi = order[pos]
            s, e = blocks[bi]
            length = e - s
            new_start_of_block[bi] = pc
            layout.append(('real', bi, s, e, pc))
            pc += length
            if bi in needs_fallthrough_jump:
                layout.append(('fixjump', bi, pc))
                pc += 1

    def remap(old_index):
        bi = old_to_block.get(old_index)
        if bi is None:
            return old_index
        s, _ = blocks[bi]
        offset = old_index - s
        return new_start_of_block[bi] + offset

    new_instructions = [None] * pc

    for item in layout:
        if item[0] == 'real':
            _, bi, s, e, new_pc = item
            for k in range(s, e):
                ins = instructions[k]
                name = rev_opmap[ins.op]
                if _is_jump_a(name):
                    ins.a = remap(ins.a)
                elif _is_jump_b(name):
                    ins.b = remap(ins.b)
                new_instructions[new_pc + (k - s)] = ins
        elif item[0] == 'fixjump':
            _, bi, new_pc = item
            target_bi = needs_fallthrough_jump[bi]
            target_pc = new_start_of_block[target_bi]
            new_instructions[new_pc] = Instruction(opmap['JUMP'], target_pc)
        else:
            _, length, new_pc, is_melodie = item
            if is_melodie:
                mel_ins, jump_off = _build_melodie_trap(proto, opmap)
                mel_ins[jump_off].a = new_pc
                for off, ins in enumerate(mel_ins):
                    new_instructions[new_pc + off] = ins
            else:
                for off in range(length):
                    new_instructions[new_pc + off] = _make_junk_instruction(rng, opmap, junk_names)

    proto.instructions = new_instructions
