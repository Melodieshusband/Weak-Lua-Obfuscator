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


FULL_COND_JUMPS = {'JUMP_FALSE', 'JUMP_TRUE', 'JUMP_FALSE_NK', 'JUMP_TRUE_NK'}
FULL_LOOP_BRANCHES = {'FOR_PREP', 'FOR_LOOP', 'TFOR_LOOP'}
FULL_RETURNS = {'RETURN', 'RETURN_NONE'}
FULL_TERMINATORS = {'JUMP'} | FULL_COND_JUMPS | FULL_LOOP_BRANCHES | FULL_RETURNS

FULL_JUNK_BINOPS = ('ADD', 'SUB', 'MUL', 'BAND', 'BOR', 'BXOR')


def flatten_bytecode_full(proto, rng, opmap):
    rev_opmap = {v: k for k, v in opmap.items()}
    _flatten_proto_full(proto, rng, rev_opmap, opmap)


def _split_blocks_full(instructions, rev_opmap):
    n = len(instructions)
    if n == 0:
        return []
    leaders = {0}
    for i, ins in enumerate(instructions):
        name = rev_opmap.get(ins.op)
        if name == 'JUMP':
            if ins.a is not None and 0 <= ins.a < n:
                leaders.add(ins.a)
            if i + 1 < n:
                leaders.add(i + 1)
        elif name in FULL_COND_JUMPS or name in FULL_LOOP_BRANCHES:
            if ins.b is not None and 0 <= ins.b < n:
                leaders.add(ins.b)
            if i + 1 < n:
                leaders.add(i + 1)
        elif name in FULL_RETURNS:
            if i + 1 < n:
                leaders.add(i + 1)
    ordered = sorted(x for x in leaders if 0 <= x < n)
    blocks = []
    for idx, start in enumerate(ordered):
        end = ordered[idx + 1] if idx + 1 < len(ordered) else n
        if end > start:
            blocks.append((start, end))
    return blocks


def _flatten_proto_full(proto, rng, rev_opmap, opmap):
    for child in proto.protos:
        _flatten_proto_full(child, rng, rev_opmap, opmap)

    instructions = proto.instructions
    n = len(instructions)
    if n < 4:
        return

    blocks = _split_blocks_full(instructions, rev_opmap)
    if len(blocks) < 2:
        return

    old_to_block = {}
    for bi, (s, e) in enumerate(blocks):
        for i in range(s, e):
            old_to_block[i] = bi

    used_ids = set()

    def new_sid():
        while True:
            sid = rng.randint(0x100000, 0x7FFFFFFE)
            if sid not in used_ids:
                used_ids.add(sid)
                return sid

    block_sids = [new_sid() for _ in blocks]
    exit_sid = new_sid()
    entry_sid = block_sids[old_to_block[0]]
    melodie_sid = new_sid()
    check_sid = new_sid()

    n_real = len(blocks)
    n_junk = min(max(2, n_real // 2), 6)
    junk_sids = [new_sid() for _ in range(n_junk)]

    slot_base = 0x20000000 + rng.randint(0, 0x00100000) * 8
    state_reg = slot_base
    table_reg = slot_base + 1
    tmp_reg = slot_base + 2
    junk_a = slot_base + 3
    junk_b = slot_base + 4
    check_r0 = slot_base + 10
    check_r1 = slot_base + 11
    check_r2 = slot_base + 12
    check_r3 = slot_base + 13
    check_r4 = slot_base + 14
    xor_key = rng.randint(0x100000, 0x3FFFFFFF)

    def k(value):
        return proto.add_const(value)

    out = []
    patches = []
    pc_patches = []
    labels = {}

    def emit(name, a=None, b=None, c=None):
        out.append(Instruction(opmap[name], a, b, c))
        return len(out) - 1

    def mark(name):
        labels[name] = len(out)

    def patch_field(idx, field, label):
        patches.append((idx, field, label))

    def set_state(sid):
        emit('LOAD_CONST', state_reg, k(sid))

    def to_dispatch():
        idx = emit('JUMP', 0)
        patch_field(idx, 'a', 'dispatch')

    def branch_to(name, a, label):
        idx = emit(name, a, 0)
        patch_field(idx, 'b', label)

    def add_scratch_junk(count):
        for _ in range(count):
            name = rng.choice(FULL_JUNK_BINOPS)
            emit(name, junk_a, junk_a, junk_b)

    def block_label(bi):
        return 'B%d' % bi

    def junk_label(ji):
        return 'J%d' % ji

    def sid_for_pc(pc):
        if pc is None or pc < 0 or pc >= n:
            return exit_sid
        bi = old_to_block.get(pc)
        if bi is None:
            return exit_sid
        return block_sids[bi]

    mark('entry')
    emit('NEW_TABLE', table_reg)

    table_units = [('B', bi) for bi in range(n_real)] + [('J', ji) for ji in range(n_junk)] + [('M', 0), ('K', 0)]
    rng.shuffle(table_units)
    for kind, idx in table_units:
        if kind == 'B':
            sid = block_sids[idx]
            label = block_label(idx)
        elif kind == 'J':
            sid = junk_sids[idx]
            label = junk_label(idx)
        elif kind == 'M':
            sid = melodie_sid
            label = 'melodie'
        else:
            sid = check_sid
            label = 'anti_tamper_check'
        pc_idx = emit('LOAD_CONST', tmp_reg, 0)
        pc_patches.append((pc_idx, label))
        emit('SET_FIELD', table_reg, k(sid), tmp_reg)
    exit_pc_idx = emit('LOAD_CONST', tmp_reg, 0)
    pc_patches.append((exit_pc_idx, 'exit'))
    emit('SET_FIELD', table_reg, k(exit_sid), tmp_reg)

    emit('LOAD_CONST', state_reg, k(check_sid))
    emit('LOAD_CONST', tmp_reg, k(xor_key))
    to_dispatch()

    mark('dispatch')
    emit('GET_TABLE', state_reg, table_reg, state_reg)
    emit('BXOR', state_reg, state_reg, tmp_reg)
    emit('JUMP_REG', state_reg)

    layout = [('B', bi) for bi in range(n_real)] + [('J', ji) for ji in range(n_junk)]
    rng.shuffle(layout)

    for kind, idx in layout:
        if kind == 'J':
            mark(junk_label(idx))
            emit('LOAD_CONST', junk_a, k(rng.randint(1, 0xFFFF)))
            emit('LOAD_CONST', junk_b, k(rng.randint(1, 0xFFFF)))
            add_scratch_junk(rng.randint(3, 6))
            target_sid = rng.choice(block_sids + [exit_sid])
            set_state(target_sid)
            to_dispatch()
            continue

        bi = idx
        mark(block_label(bi))
        start, end = blocks[bi]
        last = instructions[end - 1]
        last_name = rev_opmap.get(last.op)
        body_end = end - 1 if last_name in FULL_TERMINATORS else end

        if rng.random() < 0.3:
            emit('LOAD_CONST', junk_a, k(rng.randint(1, 0xFFFF)))
            emit('LOAD_CONST', junk_b, k(rng.randint(1, 0xFFFF)))
            add_scratch_junk(rng.randint(1, 2))

        for i in range(start, body_end):
            out.append(instructions[i])

        if last_name in FULL_RETURNS:
            out.append(last)
            continue

        if last_name == 'JUMP':
            set_state(sid_for_pc(last.a))
            to_dispatch()
            continue

        if last_name in FULL_COND_JUMPS or last_name in FULL_LOOP_BRANCHES:
            alt_label = 'A%d' % bi
            branch_to(last_name, last.a, alt_label)
            set_state(sid_for_pc(end))
            to_dispatch()
            mark(alt_label)
            set_state(sid_for_pc(last.b))
            to_dispatch()
            continue

        set_state(sid_for_pc(end))
        to_dispatch()

    mark('anti_tamper_check')
    emit('LOAD_GLOBAL', check_r0, k('debug'))
    branch_to('JUMP_FALSE', check_r0, 'check_pass')
    emit('GET_FIELD', check_r1, check_r0, k('getinfo'))
    branch_to('JUMP_FALSE', check_r1, 'check_pass')
    emit('LOAD_GLOBAL', check_r1 + 1, k('print'))
    emit('CALL', check_r1, 1, 1)
    branch_to('JUMP_FALSE', check_r1, 'check_pass')
    emit('GET_FIELD', check_r3, check_r1, k('what'))
    emit('LOAD_CONST', check_r4, k('C'))
    emit('EQ', check_r3, check_r3, check_r4)
    branch_to('JUMP_FALSE', check_r3, 'melodie')

    mark('check_pass')
    set_state(entry_sid)
    to_dispatch()

    mark('melodie')
    emit('LOAD_GLOBAL', check_r0, k('print'))
    emit('LOAD_CONST', check_r0 + 1, k(MELODIE_DECOY))
    emit('CALL', check_r0, 1, 0)
    set_state(melodie_sid)
    to_dispatch()

    mark('exit')
    emit('RETURN_NONE', 0)

    for idx, field, label in patches:
        setattr(out[idx], field, labels[label])
    for idx, label in pc_patches:
        out[idx].b = k(labels[label] ^ xor_key)

    proto.instructions = out
