import struct
import secrets
from vm_opcodes import make_opmap, CANONICAL_OPS
import mltn

_DEFAULT_OPMAP = make_opmap()

def _get_op(name, opmap=None):
    m = opmap if opmap is not None else _DEFAULT_OPMAP
    return m[name]

OP_LOAD_CONST    = _DEFAULT_OPMAP['LOAD_CONST']
OP_LOAD_VAR      = _DEFAULT_OPMAP['LOAD_VAR']
OP_SET_VAR       = _DEFAULT_OPMAP['SET_VAR']
OP_LOAD_GLOBAL   = _DEFAULT_OPMAP['LOAD_GLOBAL']
OP_SET_GLOBAL    = _DEFAULT_OPMAP['SET_GLOBAL']
OP_LOAD_UPVAL    = _DEFAULT_OPMAP['LOAD_UPVAL']
OP_SET_UPVAL     = _DEFAULT_OPMAP['SET_UPVAL']
OP_GET_TABLE     = _DEFAULT_OPMAP['GET_TABLE']
OP_SET_TABLE     = _DEFAULT_OPMAP['SET_TABLE']
OP_NEW_TABLE     = _DEFAULT_OPMAP['NEW_TABLE']
OP_SET_LIST      = _DEFAULT_OPMAP['SET_LIST']
OP_SET_LIST_MULTI = _DEFAULT_OPMAP['SET_LIST_MULTI']
OP_GET_FIELD     = _DEFAULT_OPMAP['GET_FIELD']
OP_SET_FIELD     = _DEFAULT_OPMAP['SET_FIELD']
OP_ADD           = _DEFAULT_OPMAP['ADD']
OP_SUB           = _DEFAULT_OPMAP['SUB']
OP_MUL           = _DEFAULT_OPMAP['MUL']
OP_DIV           = _DEFAULT_OPMAP['DIV']
OP_MOD           = _DEFAULT_OPMAP['MOD']
OP_POW           = _DEFAULT_OPMAP['POW']
OP_CONCAT        = _DEFAULT_OPMAP['CONCAT']
OP_UNM           = _DEFAULT_OPMAP['UNM']
OP_LEN           = _DEFAULT_OPMAP['LEN']
OP_NOT           = _DEFAULT_OPMAP['NOT']
OP_AND           = _DEFAULT_OPMAP['AND']
OP_OR            = _DEFAULT_OPMAP['OR']
OP_IDIV          = _DEFAULT_OPMAP['IDIV']
OP_BAND          = _DEFAULT_OPMAP['BAND']
OP_BOR           = _DEFAULT_OPMAP['BOR']
OP_BXOR          = _DEFAULT_OPMAP['BXOR']
OP_BNOT          = _DEFAULT_OPMAP['BNOT']
OP_SHL           = _DEFAULT_OPMAP['SHL']
OP_SHR           = _DEFAULT_OPMAP['SHR']
OP_EQ            = _DEFAULT_OPMAP['EQ']
OP_NE            = _DEFAULT_OPMAP['NE']
OP_LT            = _DEFAULT_OPMAP['LT']
OP_LE            = _DEFAULT_OPMAP['LE']
OP_GT            = _DEFAULT_OPMAP['GT']
OP_GE            = _DEFAULT_OPMAP['GE']
OP_JUMP          = _DEFAULT_OPMAP['JUMP']
OP_JUMP_FALSE    = _DEFAULT_OPMAP['JUMP_FALSE']
OP_JUMP_TRUE     = _DEFAULT_OPMAP['JUMP_TRUE']
OP_JUMP_FALSE_NK = _DEFAULT_OPMAP['JUMP_FALSE_NK']
OP_JUMP_TRUE_NK  = _DEFAULT_OPMAP['JUMP_TRUE_NK']
OP_CALL          = _DEFAULT_OPMAP['CALL']
OP_CALL_METHOD   = _DEFAULT_OPMAP['CALL_METHOD']
OP_RETURN        = _DEFAULT_OPMAP['RETURN']
OP_RETURN_NONE   = _DEFAULT_OPMAP['RETURN_NONE']
OP_VARARG        = _DEFAULT_OPMAP['VARARG']
OP_CLOSURE       = _DEFAULT_OPMAP['CLOSURE']
OP_CLOSE_UPVAL   = _DEFAULT_OPMAP['CLOSE_UPVAL']
OP_FOR_PREP      = _DEFAULT_OPMAP['FOR_PREP']
OP_FOR_LOOP      = _DEFAULT_OPMAP['FOR_LOOP']
OP_TFOR_CALL     = _DEFAULT_OPMAP['TFOR_CALL']
OP_TFOR_LOOP     = _DEFAULT_OPMAP['TFOR_LOOP']
OP_POP           = _DEFAULT_OPMAP['POP']
OP_DUP           = _DEFAULT_OPMAP['DUP']
OP_MOVE          = _DEFAULT_OPMAP['MOVE']

TYPE_NIL    = mltn.TYPE_NIL
TYPE_BOOL   = mltn.TYPE_BOOL
TYPE_NUMBER = mltn.TYPE_NUMBER
TYPE_STRING = mltn.TYPE_STRING
TYPE_FUNC   = mltn.TYPE_FUNC

def encode_const(val):
    return mltn.encode_const_plain(val)

class Instruction:
    __slots__ = ('op', 'a', 'b', 'c')

    def __init__(self, op, a=None, b=None, c=None):
        self.op = op
        self.a = a
        self.b = b
        self.c = c

    def to_bytes(self, encoded_op=None):
        real_op = encoded_op if encoded_op is not None else self.op
        b = bytes([real_op & 0xFF])
        b += mltn.encode_instruction_fields(self.a, self.b, self.c)
        return b

def roll_lcg_step(state):
    return mltn.roll_lcg_step(state)

def encode_opcode_chain(op_list, proto_seed, marker=None):
    return mltn.encode_opcode_chain(op_list, proto_seed, marker)

REPEAT_MARKER = None
DICT_MARKER = None

def encode_stream_with_state(values, state, prev):
    out = []
    for v in values:
        state, mask = mltn.next_byte_mask(state, prev)
        enc = (v ^ mask) & 0xFF
        out.append(enc)
        prev = v & 0xFF
    return out, state, prev

UPVAL_FROM_LOCAL = 0
UPVAL_FROM_UPVAL = 1

class FuncProto:
    def __init__(self):
        self.consts = []
        self.const_map = {}
        self.instructions = []
        self.protos = []
        self.params = 0
        self.is_vararg = False
        self.upvals = []

    def add_const(self, val):
        if isinstance(val, bool):
            key = ('bool', val)
        else:
            key = (type(val).__name__, val)
        if key in self.const_map:
            return self.const_map[key]
        idx = len(self.consts)
        self.consts.append(val)
        self.const_map[key] = idx
        return idx

    def emit(self, op, a=None, b=None, c=None):
        self.instructions.append(Instruction(op, a, b, c))
        return len(self.instructions) - 1

    def patch(self, idx, a=None, b=None):
        ins = self.instructions[idx]
        if a is not None:
            ins.a = a
        if b is not None:
            ins.b = b

    def pc(self):
        return len(self.instructions)

    def add_upval(self, kind, index):
        for i, (k, idx) in enumerate(self.upvals):
            if k == kind and idx == index:
                return i
        self.upvals.append((kind, index))
        return len(self.upvals) - 1

    def collect_strings(self, acc):
        for c in self.consts:
            if isinstance(c, str):
                acc.append(c)
        for p in self.protos:
            p.collect_strings(acc)

    def serialize(self, string_index_map=None):
        data = bytes([int(self.is_vararg), self.params])
        data += mltn.write_uvarint(len(self.upvals))
        for kind, idx in self.upvals:
            data += bytes([kind])
            data += mltn.write_uvarint(idx)
        data += mltn.write_enc_uvarint(len(self.protos))
        for p in self.protos:
            s = p.serialize(string_index_map=string_index_map)
            data += mltn.write_enc_uvarint(len(s))
            data += s
        const_seed = mltn.gen_seed()
        const_block = mltn.encode_const_block(self.consts, const_seed, string_index_map=string_index_map)
        data += mltn.write_enc_uvarint(len(self.consts))
        data += bytes([const_seed])
        data += mltn.write_uvarint(len(const_block))
        data += const_block
        data += mltn.write_enc_uvarint(len(self.instructions))
        proto_seed = mltn.gen_seed()
        data += bytes([proto_seed])

        op_list = [ins.op for ins in self.instructions]
        marker, dict_marker = (
            (REPEAT_MARKER, DICT_MARKER)
            if REPEAT_MARKER is not None and DICT_MARKER is not None
            else mltn.pick_two_markers(op_list)
        )
        data += bytes([marker, dict_marker])

        rle_stream = mltn.rle_encode_ops(op_list, marker, dict_marker)
        atoms = mltn._split_atoms(rle_stream, marker)
        dictionary = mltn.build_dictionary(atoms)
        dict_encoded = mltn.dict_encode_atoms(atoms, dictionary, dict_marker)
        dict_body = mltn.serialize_dictionary(dictionary, marker)

        state = proto_seed & 0xFF
        prev = proto_seed & 0xFF
        enc_ops, state, prev = encode_stream_with_state(dict_encoded, state, prev)
        enc_dict, state, prev = encode_stream_with_state(list(dict_body), state, prev)

        data += mltn.write_uvarint(len(enc_ops))
        data += bytes(enc_ops)
        data += mltn.write_uvarint(len(enc_dict))
        data += bytes(enc_dict)

        for ins in self.instructions:
            data += mltn.encode_instruction_fields(ins.a, ins.b, ins.c)
        return data

    def serialize_legacy(self):
        # Pre-MLTN format: fixed-width u16 fields, plaintext strings/numbers,
        # only opcodes are LCG-encrypted. Not wired into the CLI - kept here
        # for size/behavior comparison against the MLTN-compressed format.
        def legacy_encode_const(val):
            if val is None:
                return bytes([0])
            if isinstance(val, bool):
                return bytes([1, 1 if val else 0])
            if isinstance(val, (int, float)):
                return bytes([2]) + struct.pack('<d', float(val))
            if isinstance(val, str):
                enc = val.encode('utf-8')
                return bytes([3]) + struct.pack('<H', len(enc)) + enc
            return bytes([0])

        def legacy_instruction_bytes(op, a, b, c):
            out = bytes([op & 0xFF])
            for v in (a, b, c):
                if v is not None:
                    out += struct.pack('<H', v & 0xFFFF)
            return out

        data = bytes([int(self.is_vararg), self.params])
        data += struct.pack('<H', len(self.upvals))
        for kind, idx in self.upvals:
            data += bytes([kind]) + struct.pack('<H', idx)
        data += struct.pack('<H', len(self.protos))
        for p in self.protos:
            s = p.serialize_legacy()
            data += struct.pack('<I', len(s)) + s
        data += struct.pack('<H', len(self.consts))
        for c in self.consts:
            data += legacy_encode_const(c)
        data += struct.pack('<H', len(self.instructions))
        proto_seed = mltn.gen_seed()
        data += bytes([proto_seed])
        encoded_ops = mltn.encode_opcode_chain(
            [ins.op for ins in self.instructions], proto_seed
        )
        for ins, enc_op in zip(self.instructions, encoded_ops):
            data += legacy_instruction_bytes(enc_op, ins.a, ins.b, ins.c)
        return data

class Scope:
    def __init__(self, parent=None, func_boundary=False):
        self.parent = parent
        self.locals = {}
        if parent and not func_boundary:
            self.reg_counter = parent.reg_counter
        else:
            self.reg_counter = [0]
        self.func_boundary = func_boundary

    def alloc(self, name):
        reg = self.reg_counter[0]
        self.reg_counter[0] += 1
        self.locals[name] = reg
        return reg

    def free_to(self, reg):
        self.reg_counter[0] = reg

    def resolve_local(self, name):
        s = self
        while s is not None:
            if name in s.locals:
                return s.locals[name]
            if s.func_boundary:
                return None
            s = s.parent
        return None

class Compiler:
    def __init__(self, parent=None):
        self.proto = FuncProto()
        self.scope = Scope(func_boundary=True)
        self.parent = parent
        self.break_patches = []
        self.continue_patches = []
        self.captured_regs = set()

    def child(self):
        c = Compiler(parent=self)
        return c

    def push_scope(self):
        self.scope = Scope(self.scope)
        return self.scope.reg_counter[0]

    def pop_scope(self, saved_reg):
        self.scope = self.scope.parent
        self.scope.reg_counter[0] = saved_reg

    def emit_close_upvals(self, from_reg):
        regs = sorted(r for r in self.captured_regs if r >= from_reg)
        for r in regs:
            self.emit(OP_CLOSE_UPVAL, r)
        self.captured_regs -= set(regs)

    def resolve(self, name):
        local_reg = self.scope.resolve_local(name)
        if local_reg is not None:
            return ('local', local_reg)
        if self.parent is None:
            return None
        pr = self.parent.resolve(name)
        if pr is None:
            return None
        if pr[0] == 'local':
            idx = self.proto.add_upval(UPVAL_FROM_LOCAL, pr[1])
            self.parent.captured_regs.add(pr[1])
            return ('upval', idx)
        if pr[0] == 'upval':
            idx = self.proto.add_upval(UPVAL_FROM_UPVAL, pr[1])
            return ('upval', idx)
        return None

    def alloc(self, name='_'):
        return self.scope.alloc(name)

    def free_to(self, reg):
        self.scope.free_to(reg)

    def K(self, val):
        return self.proto.add_const(val)

    def emit(self, *args, **kwargs):
        return self.proto.emit(*args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.proto.patch(*args, **kwargs)

    def pc(self):
        return self.proto.pc()

    def compile_expr_to(self, node, dst):
        self._expr(node, dst)

    def _expr(self, node, dst):
        t = node['type']

        if t == 'number':
            self.emit(OP_LOAD_CONST, dst, self.K(node['value']))
        elif t == 'string':
            self.emit(OP_LOAD_CONST, dst, self.K(node['value']))
        elif t == 'bool':
            self.emit(OP_LOAD_CONST, dst, self.K(node['value']))
        elif t == 'nil':
            self.emit(OP_LOAD_CONST, dst, self.K(None))
        elif t == 'vararg':
            self.emit(OP_VARARG, dst, 1)
        elif t == 'var':
            r = self.resolve(node['name'])
            if r is None:
                self.emit(OP_LOAD_GLOBAL, dst, self.K(node['name']))
            elif r[0] == 'local':
                if r[1] != dst:
                    self.emit(OP_MOVE, dst, r[1])
            elif r[0] == 'upval':
                self.emit(OP_LOAD_UPVAL, dst, r[1])
        elif t == 'index':
            tmp = self.scope.reg_counter[0]
            self.scope.reg_counter[0] += 2
            self._expr(node['obj'], tmp)
            self._expr(node['key'], tmp + 1)
            self.emit(OP_GET_TABLE, dst, tmp, tmp + 1)
            self.scope.reg_counter[0] = tmp
        elif t == 'field':
            tmp = self.scope.reg_counter[0]
            self.scope.reg_counter[0] += 1
            self._expr(node['obj'], tmp)
            self.emit(OP_GET_FIELD, dst, tmp, self.K(node['name']))
            self.scope.reg_counter[0] = tmp
        elif t == 'method_call':
            self._method_call(node, dst)
        elif t == 'call':
            self._call(node, dst, 1)
        elif t == 'binop':
            self._binop(node, dst)
        elif t == 'unop':
            self._unop(node, dst)
        elif t == 'table_constructor':
            self._table_ctor(node, dst)
        elif t == 'function':
            self._function_expr(node, dst)
        elif t == 'multi':
            self._expr(node['exprs'][0], dst)
        elif t == 'paren':
            inner = node['inner']
            if inner['type'] == 'call':
                self._call(inner, dst, 1)
            elif inner['type'] == 'method_call':
                self._method_call(inner, dst)
            elif inner['type'] == 'vararg':
                self.emit(OP_VARARG, dst, 1)
            else:
                self._expr(inner, dst)
        else:
            raise SyntaxError(f"Unknown expression node type: {t}")

    def _binop(self, node, dst):
        op = node['op']
        tmp = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 2
        left_r = tmp
        right_r = tmp + 1
        self._expr(node['left'], left_r)

        if op == 'and':
            jf = self.emit(OP_JUMP_FALSE_NK, left_r, 0)
            self._expr(node['right'], right_r)
            self.emit(OP_MOVE, dst, right_r)
            end = self.emit(OP_JUMP, 0)
            self.patch(jf, b=self.pc())
            self.emit(OP_MOVE, dst, left_r)
            self.patch(end, a=self.pc())
        elif op == 'or':
            jt = self.emit(OP_JUMP_TRUE_NK, left_r, 0)
            self._expr(node['right'], right_r)
            self.emit(OP_MOVE, dst, right_r)
            end = self.emit(OP_JUMP, 0)
            self.patch(jt, b=self.pc())
            self.emit(OP_MOVE, dst, left_r)
            self.patch(end, a=self.pc())
        else:
            self._expr(node['right'], right_r)
            op_map = {
                '+': OP_ADD, '-': OP_SUB, '*': OP_MUL, '/': OP_DIV,
                '//': OP_IDIV,
                '%': OP_MOD, '^': OP_POW, '..': OP_CONCAT,
                '==': OP_EQ, '~=': OP_NE,
                '<': OP_LT, '<=': OP_LE, '>': OP_GT, '>=': OP_GE,
                '&': OP_BAND, '|': OP_BOR, '~': OP_BXOR,
                '<<': OP_SHL, '>>': OP_SHR,
            }
            self.emit(op_map[op], dst, left_r, right_r)

        self.scope.reg_counter[0] = tmp

    def _unop(self, node, dst):
        tmp = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['operand'], tmp)
        op_map = {'-': OP_UNM, 'not': OP_NOT, '#': OP_LEN, '~': OP_BNOT}
        self.emit(op_map[node['op']], dst, tmp)
        self.scope.reg_counter[0] = tmp

    def _call(self, node, dst, nresults):
        base = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        fn_r = base

        fn = node['fn']
        self._expr(fn, fn_r)

        args = node['args']
        argc = len(args)
        for i, a in enumerate(args):
            ar = base + 1 + i
            self.scope.reg_counter[0] = ar + 1
            if i == argc - 1 and a.get('type') in ('call', 'method_call', 'vararg'):
                self._call_multiret(a, ar)
                argc = -1
            else:
                self._expr(a, ar)

        self.emit(OP_CALL, fn_r, argc if argc >= 0 else 255, nresults)
        if dst != fn_r:
            self.emit(OP_MOVE, dst, fn_r)
        self.scope.reg_counter[0] = base

    def _call_multiret(self, node, base_r):
        if node['type'] == 'call':
            self.scope.reg_counter[0] = base_r + 1
            fn = node['fn']
            self._expr(fn, base_r)
            args = node['args']
            argc = len(args)
            for i, a in enumerate(args):
                ar = base_r + 1 + i
                self.scope.reg_counter[0] = ar + 1
                if i == argc - 1 and a.get('type') in ('call', 'method_call', 'vararg'):
                    self._call_multiret(a, ar)
                    argc = -1
                else:
                    self._expr(a, ar)
            self.emit(OP_CALL, base_r, argc if argc >= 0 else 255, 255)
        elif node['type'] == 'method_call':
            self._method_call_multiret(node, base_r)
        elif node['type'] == 'vararg':
            self.emit(OP_VARARG, base_r, 255)

    def _method_call(self, node, dst):
        base = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        obj_r = base
        self._expr(node['obj'], obj_r)
        args = node['args']
        argc = len(args)
        for i, a in enumerate(args):
            ar = base + 1 + i
            self.scope.reg_counter[0] = ar + 1
            if i == argc - 1 and a.get('type') in ('call', 'method_call', 'vararg'):
                self._call_multiret(a, ar)
                argc = -1
            else:
                self._expr(a, ar)
        self.emit(OP_CALL_METHOD, obj_r, self.K(node['method']), argc if argc >= 0 else 255)
        if dst != obj_r:
            self.emit(OP_MOVE, dst, obj_r)
        self.scope.reg_counter[0] = base

    def _method_call_multiret(self, node, base_r):
        self.scope.reg_counter[0] = base_r + 1
        self._expr(node['obj'], base_r)
        args = node['args']
        argc = len(args)
        for i, a in enumerate(args):
            ar = base_r + 1 + i
            self.scope.reg_counter[0] = ar + 1
            if i == argc - 1 and a.get('type') in ('call', 'method_call', 'vararg'):
                self._call_multiret(a, ar)
                argc = -1
            else:
                self._expr(a, ar)
        self.emit(OP_CALL_METHOD, base_r, self.K(node['method']), (argc if argc >= 0 else 255) | 0x100)

    def _table_ctor(self, node, dst):
        self.emit(OP_NEW_TABLE, dst)
        array_idx = 1
        fields = node['fields']
        for fi, entry in enumerate(fields):
            tmp = self.scope.reg_counter[0]
            self.scope.reg_counter[0] += 2
            if entry['type'] == 'array_field':
                val_r = tmp
                is_last = (fi == len(fields) - 1)
                if is_last and entry['value'].get('type') in ('call', 'method_call', 'vararg'):
                    self._call_multiret(entry['value'], val_r)
                    self.emit(OP_SET_LIST_MULTI, dst, val_r, self.K(float(array_idx)))
                else:
                    self._expr(entry['value'], val_r)
                    ki = self.K(float(array_idx))
                    self.emit(OP_SET_LIST, dst, ki, val_r)
                    array_idx += 1
            elif entry['type'] == 'string_field':
                val_r = tmp
                self._expr(entry['value'], val_r)
                self.emit(OP_SET_FIELD, dst, self.K(entry['key']), val_r)
            elif entry['type'] == 'expr_field':
                key_r = tmp
                val_r = tmp + 1
                self._expr(entry['key'], key_r)
                self._expr(entry['value'], val_r)
                self.emit(OP_SET_TABLE, dst, key_r, val_r)
            self.scope.reg_counter[0] = tmp

    def _function_expr(self, node, dst):
        child = self.child()
        child.proto.params = len(node['params'])
        child.proto.is_vararg = node.get('is_vararg', False)
        for p in node['params']:
            child.scope.alloc(p)
        child._stmts(node['body'])
        if not child.proto.instructions or child.proto.instructions[-1].op not in (OP_RETURN, OP_RETURN_NONE):
            child.emit(OP_RETURN_NONE, 0)
        idx = len(self.proto.protos)
        self.proto.protos.append(child.proto)
        self.emit(OP_CLOSURE, dst, idx)

    def _stmts(self, stmts):
        for s in stmts:
            self._stmt(s)

    def _stmt(self, node):
        t = node['type']

        if t == 'local':
            names = node['names']
            exprs = node.get('values', [])
            regs = []
            for i, name in enumerate(names):
                reg = self.scope.reg_counter[0]
                self.scope.reg_counter[0] += 1
                regs.append(reg)
            nexprs = len(exprs)
            stretched = False
            for i, e in enumerate(exprs):
                reg = regs[i] if i < len(regs) else self.scope.reg_counter[0]
                if i == nexprs - 1 and e.get('type') in ('call', 'method_call', 'vararg'):
                    if i < len(names) - 1:
                        need = len(names) - i
                        tmp = self.scope.reg_counter[0]
                        self.scope.reg_counter[0] = tmp + need
                        self._call_multiret(e, tmp)
                        for k in range(need):
                            self.emit(OP_MOVE, regs[i + k], tmp + k)
                        self.scope.reg_counter[0] = tmp
                        stretched = True
                    else:
                        self._expr(e, reg)
                else:
                    if i < len(regs):
                        self._expr(e, reg)
                    else:
                        tmp = self.scope.reg_counter[0]
                        self.scope.reg_counter[0] = tmp + 1
                        self._expr(e, tmp)
                        self.scope.reg_counter[0] = tmp
            if not stretched:
                for i in range(nexprs, len(names)):
                    self.emit(OP_LOAD_CONST, regs[i], self.K(None))
            for i, name in enumerate(names):
                self.scope.locals[name] = regs[i]

        elif t == 'assign':
            targets = node['targets']
            values = node['values']
            tmp_base = self.scope.reg_counter[0]
            nvalues = len(values)
            ntargets = len(targets)
            tmps = []
            for i, v in enumerate(values):
                if i == nvalues - 1 and v.get('type') in ('call', 'method_call', 'vararg') and nvalues < ntargets:
                    need = ntargets - i
                    tr = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] = tr + need
                    self._call_multiret(v, tr)
                    for k in range(need):
                        tmps.append(tr + k)
                else:
                    tr = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] = tr + 1
                    if i == nvalues - 1 and v.get('type') in ('call', 'method_call', 'vararg'):
                        self._call_multiret(v, tr)
                    else:
                        self._expr(v, tr)
                    tmps.append(tr)

            val_base = self.scope.reg_counter[0]
            for i, tgt in enumerate(targets):
                src = tmps[i] if i < len(tmps) else None
                val_r = val_base + i
                if src is not None:
                    self.scope.reg_counter[0] = val_r + 1
                    self.emit(OP_MOVE, val_r, src)
                else:
                    self.scope.reg_counter[0] = val_r + 1
                    self.emit(OP_LOAD_CONST, val_r, self.K(None))

                tt = tgt['type']
                if tt == 'var':
                    r = self.resolve(tgt['name'])
                    if r is None:
                        self.emit(OP_SET_GLOBAL, self.K(tgt['name']), val_r)
                    elif r[0] == 'local':
                        self.emit(OP_MOVE, r[1], val_r)
                    elif r[0] == 'upval':
                        self.emit(OP_SET_UPVAL, r[1], val_r)
                elif tt == 'index':
                    tr2 = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] += 2
                    self._expr(tgt['obj'], tr2)
                    self._expr(tgt['key'], tr2 + 1)
                    self.emit(OP_SET_TABLE, tr2, tr2 + 1, val_r)
                    self.scope.reg_counter[0] = val_r + 1
                elif tt == 'field':
                    tr2 = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] += 1
                    self._expr(tgt['obj'], tr2)
                    self.emit(OP_SET_FIELD, tr2, self.K(tgt['name']), val_r)
                    self.scope.reg_counter[0] = val_r + 1

            self.scope.reg_counter[0] = tmp_base

        elif t == 'call_stmt':
            self._call(node, self.scope.reg_counter[0], 0)

        elif t == 'method_call_stmt':
            self._method_call(node, self.scope.reg_counter[0])

        elif t == 'return':
            exprs = node.get('values', [])
            if not exprs:
                self.emit(OP_RETURN_NONE, 0)
                return
            base = self.scope.reg_counter[0]
            argc = len(exprs)
            for i, e in enumerate(exprs):
                r = base + i
                self.scope.reg_counter[0] = r + 1
                if i == argc - 1 and e.get('type') in ('call', 'method_call', 'vararg'):
                    self._call_multiret(e, r)
                    argc = -1
                else:
                    self._expr(e, r)
            self.emit(OP_RETURN, base, argc if argc >= 0 else 255)
            self.scope.reg_counter[0] = base

        elif t == 'do':
            saved = self.push_scope()
            self._stmts(node['body'])
            self.pop_scope(saved)

        elif t == 'if':
            self._if(node)

        elif t == 'while':
            self._while(node)

        elif t == 'repeat':
            self._repeat(node)

        elif t == 'numeric_for':
            self._numeric_for(node)

        elif t == 'generic_for':
            self._generic_for(node)

        elif t == 'function_def':
            dst_info = self.resolve(node['target'][0]) if len(node['target']) == 1 else None
            fn_node = {'type': 'function', 'params': node['params'],
                       'body': node['body'], 'is_vararg': node.get('is_vararg', False)}
            if len(node['target']) == 1 and dst_info and dst_info[0] == 'local':
                self._function_expr(fn_node, dst_info[1])
            else:
                tmp = self.scope.reg_counter[0]
                self.scope.reg_counter[0] += 1
                self._function_expr(fn_node, tmp)
                if len(node['target']) == 1:
                    name = node['target'][0]
                    r = self.resolve(name)
                    if r is None:
                        self.emit(OP_SET_GLOBAL, self.K(name), tmp)
                    elif r[0] == 'local':
                        self.emit(OP_MOVE, r[1], tmp)
                    elif r[0] == 'upval':
                        self.emit(OP_SET_UPVAL, r[1], tmp)
                elif len(node['target']) > 1:
                    obj_r = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] += 1
                    r = self.resolve(node['target'][0])
                    if r and r[0] == 'local':
                        self.emit(OP_MOVE, obj_r, r[1])
                    elif r and r[0] == 'upval':
                        self.emit(OP_LOAD_UPVAL, obj_r, r[1])
                    else:
                        self.emit(OP_LOAD_GLOBAL, obj_r, self.K(node['target'][0]))
                    for part in node['target'][1:-1]:
                        self.emit(OP_GET_FIELD, obj_r, obj_r, self.K(part))
                    self.emit(OP_SET_FIELD, obj_r, self.K(node['target'][-1]), tmp)
                self.scope.reg_counter[0] = tmp

        elif t == 'local_function':
            reg = self.scope.alloc(node['name'])
            fn_node = {'type': 'function', 'params': node['params'],
                       'body': node['body'], 'is_vararg': node.get('is_vararg', False)}
            self._function_expr(fn_node, reg)

        elif t == 'break':
            j = self.emit(OP_JUMP, 0)
            self.break_patches.append(j)

        elif t == 'continue':
            j = self.emit(OP_JUMP, 0)
            self.continue_patches.append(j)

        else:
            raise SyntaxError(f"Unknown statement node type: {t}")

    def _if(self, node):
        end_jumps = []
        cond_r = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['cond'], cond_r)
        jf = self.emit(OP_JUMP_FALSE, cond_r, 0)
        self.scope.reg_counter[0] = cond_r
        saved = self.push_scope()
        self._stmts(node['body'])
        self.pop_scope(saved)
        if node.get('elseif') or node.get('else'):
            j = self.emit(OP_JUMP, 0)
            end_jumps.append(j)
        self.patch(jf, b=self.pc())
        for ei in node.get('elseif', []):
            cond_r2 = self.scope.reg_counter[0]
            self.scope.reg_counter[0] += 1
            self._expr(ei['cond'], cond_r2)
            jf2 = self.emit(OP_JUMP_FALSE, cond_r2, 0)
            self.scope.reg_counter[0] = cond_r2
            saved = self.push_scope()
            self._stmts(ei['body'])
            self.pop_scope(saved)
            j2 = self.emit(OP_JUMP, 0)
            end_jumps.append(j2)
            self.patch(jf2, b=self.pc())
        if node.get('else'):
            saved = self.push_scope()
            self._stmts(node['else'])
            self.pop_scope(saved)
        for j in end_jumps:
            self.patch(j, a=self.pc())

    def _while(self, node):
        loop_start = self.pc()
        cond_r = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['cond'], cond_r)
        jf = self.emit(OP_JUMP_FALSE, cond_r, 0)
        self.scope.reg_counter[0] = cond_r
        old_breaks = self.break_patches
        old_continues = self.continue_patches
        self.break_patches = []
        self.continue_patches = []
        saved = self.push_scope()
        self._stmts(node['body'])
        for cp in self.continue_patches:
            self.patch(cp, a=self.pc())
        self.emit_close_upvals(saved)
        self.pop_scope(saved)
        self.emit(OP_JUMP, loop_start)
        self.patch(jf, b=self.pc())
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.continue_patches = old_continues

    def _repeat(self, node):
        loop_start = self.pc()
        old_breaks = self.break_patches
        old_continues = self.continue_patches
        self.break_patches = []
        self.continue_patches = []
        saved = self.push_scope()
        self._stmts(node['body'])
        for cp in self.continue_patches:
            self.patch(cp, a=self.pc())
        cond_r = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['cond'], cond_r)
        self.scope.reg_counter[0] = cond_r
        self.emit_close_upvals(saved)
        self.emit(OP_JUMP_FALSE, cond_r, loop_start)
        self.pop_scope(saved)
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.continue_patches = old_continues

    def _numeric_for(self, node):
        saved_reg = self.scope.reg_counter[0]
        init_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        limit_r = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        step_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        var_r   = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        self._expr(node['start'], init_r)
        self._expr(node['limit'], limit_r)
        if node.get('step'):
            self._expr(node['step'], step_r)
        else:
            self.emit(OP_LOAD_CONST, step_r, self.K(1))
        fp = self.emit(OP_FOR_PREP, init_r, 0)
        loop_start = self.pc()
        self.push_scope()
        self.scope.locals[node['var']] = var_r
        old_breaks = self.break_patches
        old_continues = self.continue_patches
        self.break_patches = []
        self.continue_patches = []
        self._stmts(node['body'])
        cont_target = self.pc()
        for cp in self.continue_patches:
            self.patch(cp, a=cont_target)
        self.emit_close_upvals(var_r)
        self.pop_scope(saved_reg + 4)
        fl = self.emit(OP_FOR_LOOP, init_r, 0)
        self.patch(fp, b=self.pc())
        self.patch(fl, b=loop_start)
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.continue_patches = old_continues
        self.scope.reg_counter[0] = saved_reg

    def _generic_for(self, node):
        saved_reg = self.scope.reg_counter[0]
        iter_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        state_r = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        ctrl_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        exprs = node['iters']
        last_idx = len(exprs) - 1
        slots = [iter_r, state_r, ctrl_r]
        i = 0
        while i < 3:
            if i < len(exprs):
                e = exprs[i]
                if i == last_idx and e.get('type') in ('call', 'method_call', 'vararg'):
                    tmp = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] = tmp + 1
                    self._call_multiret(e, tmp)
                    remaining = 3 - i
                    for k in range(remaining):
                        self.emit(OP_MOVE, slots[i + k], tmp + k)
                    self.scope.reg_counter[0] = ctrl_r + 1
                    break
                else:
                    self._expr(e, slots[i])
            else:
                self.emit(OP_LOAD_CONST, slots[i], self.K(None))
            i += 1
        loop_start = self.pc()
        var_regs = []
        for vn in node['vars']:
            vr = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
            var_regs.append(vr)
        tf = self.emit(OP_TFOR_CALL, iter_r, 0, len(node['vars']))
        jf = self.emit(OP_TFOR_LOOP, var_regs[0] if var_regs else ctrl_r, 0)
        self.push_scope()
        for vn, vr in zip(node['vars'], var_regs):
            self.scope.locals[vn] = vr
        old_breaks = self.break_patches
        old_continues = self.continue_patches
        self.break_patches = []
        self.continue_patches = []
        self._stmts(node['body'])
        cont_target = self.pc()
        for cp in self.continue_patches:
            self.patch(cp, a=cont_target)
        self.emit_close_upvals(var_regs[0] if var_regs else ctrl_r + 1)
        self.pop_scope(saved_reg + 3 + len(node['vars']))
        self.emit(OP_JUMP, loop_start)
        self.patch(jf, b=self.pc())
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.continue_patches = old_continues
        self.scope.reg_counter[0] = saved_reg

    def compile_chunk(self, stmts, is_vararg=True):
        self.proto.is_vararg = is_vararg
        self._stmts(stmts)
        if not self.proto.instructions or self.proto.instructions[-1].op not in (OP_RETURN, OP_RETURN_NONE):
            self.emit(OP_RETURN_NONE, 0)

    def serialize(self):
        all_strings = []
        self.proto.collect_strings(all_strings)
        pool, string_index_map = mltn.build_string_pool(all_strings)
        pool_seed = mltn.gen_seed()
        pool_block = mltn.encode_string_pool_block(pool, pool_seed)

        body = self.proto.serialize(string_index_map=string_index_map)

        header = bytes([pool_seed])
        header += mltn.write_uvarint(len(pool_block))
        header += pool_block
        return header + body

    def serialize_legacy(self):
        # Pre-MLTN format, not wired into CLI. See FuncProto.serialize_legacy.
        return self.proto.serialize_legacy()


KEYWORDS = {
    'and','break','continue','do','else','elseif','end','false','for','function',
    'if','in','local','nil','not','or','repeat','return','then','true',
    'until','while',
}
def tokenize(src):
    tokens = []
    i = 0
    n = len(src)
    while i < n:
        if src[i] == '-' and i+1 < n and src[i+1] == '-':
            if i+3 < n and src[i+2] == '[' and src[i+3] == '[':
                i += 4
                while i < n and not (src[i] == ']' and i+1 < n and src[i+1] == ']'):
                    i += 1
                i += 2
            else:
                while i < n and src[i] != '\n':
                    i += 1
            continue
        if src[i] in ' \t\r\n':
            i += 1
            continue
        if src[i] == '[' and i+1 < n and src[i+1] == '[':
            i += 2
            s = []
            while i < n and not (src[i] == ']' and i+1 < n and src[i+1] == ']'):
                s.append(src[i])
                i += 1
            i += 2
            tokens.append(('STRING', ''.join(s)))
            continue
        if src[i] in ('"', "'"):
            q = src[i]
            i += 1
            s = []
            while i < n and src[i] != q:
                if src[i] == '\\':
                    i += 1
                    esc_map = {'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"',"'":"'",'0':'\0','a':'\a','b':'\b','f':'\f','v':'\v'}
                    if i < n:
                        if src[i].isdigit():
                            j = i
                            while i < n and i - j < 3 and src[i].isdigit():
                                i += 1
                            s.append(chr(int(src[j:i])))
                            continue
                        s.append(esc_map.get(src[i], src[i]))
                        i += 1
                else:
                    s.append(src[i])
                    i += 1
            i += 1
            tokens.append(('STRING', ''.join(s)))
            continue
        if src[i].isdigit() or (src[i] == '.' and i+1 < n and src[i+1].isdigit()):
            j = i
            if src[i:i+2] in ('0x', '0X'):
                i += 2
                while i < n and (src[i] in '0123456789abcdefABCDEF'):
                    i += 1
                tokens.append(('NUMBER', src[j:i]))
            else:
                while i < n and (src[i].isdigit() or src[i] in '.eE'):
                    if src[i] in 'eE' and i+1 < n and src[i+1] in '+-':
                        i += 2
                    else:
                        i += 1
                tokens.append(('NUMBER', src[j:i]))
            continue
        if src[i].isalpha() or src[i] == '_':
            j = i
            while i < n and (src[i].isalnum() or src[i] == '_'):
                i += 1
            word = src[j:i]
            tokens.append(('KW' if word in KEYWORDS else 'NAME', word))
            continue
        three = src[i:i+3]
        if three == '...':
            tokens.append(('OP', '...'))
            i += 3
            continue
        two = src[i:i+2]
        if two in ('==','~=','<=','>=','..','//','<<','>>'):
            tokens.append(('OP', two))
            i += 2
            continue
        if src[i] in '+-*/%^<>=.&|~':
            tokens.append(('OP', src[i]))
            i += 1
            continue
        if src[i] == '(':  tokens.append(('LPAREN', '(')); i += 1; continue
        if src[i] == ')':  tokens.append(('RPAREN', ')')); i += 1; continue
        if src[i] == '[':  tokens.append(('LBRACK', '[')); i += 1; continue
        if src[i] == ']':  tokens.append(('RBRACK', ']')); i += 1; continue
        if src[i] == '{':  tokens.append(('LBRACE', '{')); i += 1; continue
        if src[i] == '}':  tokens.append(('RBRACE', '}')); i += 1; continue
        if src[i] == ',':  tokens.append(('COMMA', ',')); i += 1; continue
        if src[i] == ';':  tokens.append(('SEMI', ';')); i += 1; continue
        if src[i] == ':':
            if i+1 < n and src[i+1] == ':':
                tokens.append(('OP', '::')); i += 2
            else:
                tokens.append(('COLON', ':')); i += 1
            continue
        if src[i] == '#':  tokens.append(('OP', '#')); i += 1; continue
        i += 1
    tokens.append(('EOF', ''))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return ('EOF', '')

    def consume(self, kind=None, val=None):
        tok = self.tokens[self.pos]
        if kind and tok[0] != kind:
            raise SyntaxError(f"Expected {kind} got {tok} at pos {self.pos}")
        if val and tok[1] != val:
            raise SyntaxError(f"Expected '{val}' got {tok} at pos {self.pos}")
        self.pos += 1
        return tok

    def match(self, kind, val=None):
        tok = self.peek()
        if tok[0] == kind and (val is None or tok[1] == val):
            self.pos += 1
            return tok
        return None

    def check(self, kind, val=None):
        tok = self.peek()
        return tok[0] == kind and (val is None or tok[1] == val)

    def parse(self):
        stmts = self.parse_block()
        self.consume('EOF')
        return stmts

    def parse_block(self):
        stmts = []
        while True:
            tok = self.peek()
            if tok[0] == 'EOF':
                break
            if tok[0] == 'KW' and tok[1] in ('end', 'else', 'elseif', 'until'):
                break
            s = self.parse_stmt()
            if s:
                stmts.append(s)
        return stmts

    def parse_stmt(self):
        tok = self.peek()

        if tok[0] == 'SEMI':
            self.consume()
            return None

        if tok[0] == 'KW':
            kw = tok[1]
            if kw == 'local':
                return self.parse_local()
            if kw == 'return':
                return self.parse_return()
            if kw == 'if':
                return self.parse_if()
            if kw == 'while':
                return self.parse_while()
            if kw == 'repeat':
                return self.parse_repeat()
            if kw == 'for':
                return self.parse_for()
            if kw == 'do':
                return self.parse_do()
            if kw == 'function':
                return self.parse_function_stmt()
            if kw == 'break':
                self.consume()
                return {'type': 'break'}
            if kw == 'continue':
                self.consume()
                return {'type': 'continue'}

        return self.parse_expr_stmt()

    def parse_local(self):
        self.consume('KW', 'local')
        if self.check('KW', 'function'):
            self.consume('KW', 'function')
            name = self.consume('NAME')[1]
            params, is_vararg = self.parse_params()
            body = self.parse_block()
            self.consume('KW', 'end')
            return {'type': 'local_function', 'name': name, 'params': params,
                    'body': body, 'is_vararg': is_vararg}
        names = [self.consume('NAME')[1]]
        while self.match('COMMA'):
            names.append(self.consume('NAME')[1])
        values = []
        if self.match('OP', '='):
            values = self.parse_expr_list()
        return {'type': 'local', 'names': names, 'values': values}

    def parse_return(self):
        self.consume('KW', 'return')
        values = []
        tok = self.peek()
        if not (tok[0] == 'EOF' or (tok[0] == 'KW' and tok[1] in ('end','else','elseif','until')) or tok[0] == 'SEMI'):
            values = self.parse_expr_list()
        self.match('SEMI')
        return {'type': 'return', 'values': values}

    def parse_if(self):
        self.consume('KW', 'if')
        cond = self.parse_expr()
        self.consume('KW', 'then')
        body = self.parse_block()
        elseifs = []
        else_body = None
        while self.check('KW', 'elseif'):
            self.consume()
            ec = self.parse_expr()
            self.consume('KW', 'then')
            eb = self.parse_block()
            elseifs.append({'cond': ec, 'body': eb})
        if self.match('KW', 'else'):
            else_body = self.parse_block()
        self.consume('KW', 'end')
        return {'type': 'if', 'cond': cond, 'body': body,
                'elseif': elseifs, 'else': else_body}

    def parse_while(self):
        self.consume('KW', 'while')
        cond = self.parse_expr()
        self.consume('KW', 'do')
        body = self.parse_block()
        self.consume('KW', 'end')
        return {'type': 'while', 'cond': cond, 'body': body}

    def parse_repeat(self):
        self.consume('KW', 'repeat')
        body = self.parse_block()
        self.consume('KW', 'until')
        cond = self.parse_expr()
        return {'type': 'repeat', 'body': body, 'cond': cond}

    def parse_for(self):
        self.consume('KW', 'for')
        name = self.consume('NAME')[1]
        if self.match('OP', '='):
            start = self.parse_expr()
            self.consume('COMMA')
            limit = self.parse_expr()
            step = None
            if self.match('COMMA'):
                step = self.parse_expr()
            self.consume('KW', 'do')
            body = self.parse_block()
            self.consume('KW', 'end')
            return {'type': 'numeric_for', 'var': name, 'start': start,
                    'limit': limit, 'step': step, 'body': body}
        else:
            vars_ = [name]
            while self.match('COMMA'):
                vars_.append(self.consume('NAME')[1])
            self.consume('KW', 'in')
            iters = self.parse_expr_list()
            self.consume('KW', 'do')
            body = self.parse_block()
            self.consume('KW', 'end')
            return {'type': 'generic_for', 'vars': vars_, 'iters': iters, 'body': body}

    def parse_do(self):
        self.consume('KW', 'do')
        body = self.parse_block()
        self.consume('KW', 'end')
        return {'type': 'do', 'body': body}

    def parse_function_stmt(self):
        self.consume('KW', 'function')
        target = [self.consume('NAME')[1]]
        is_method = False
        while self.check('OP', '.'):
            self.consume()
            target.append(self.consume('NAME')[1])
        if self.check('COLON', ':'):
            self.consume()
            target.append(self.consume('NAME')[1])
            is_method = True
        params, is_vararg = self.parse_params()
        if is_method:
            params = ['self'] + params
        body = self.parse_block()
        self.consume('KW', 'end')
        return {'type': 'function_def', 'target': target, 'params': params,
                'body': body, 'is_vararg': is_vararg}

    def parse_params(self):
        self.consume('LPAREN')
        params = []
        is_vararg = False
        if not self.check('RPAREN'):
            while True:
                if self.check('OP', '...'):
                    self.consume()
                    is_vararg = True
                    break
                params.append(self.consume('NAME')[1])
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN')
        return params, is_vararg

    def parse_expr_stmt(self):
        expr = self.parse_suffixed_expr()
        if self.check('OP', '=') or self.check('COMMA'):
            targets = [expr]
            while self.match('COMMA'):
                targets.append(self.parse_suffixed_expr())
            self.consume('OP', '=')
            values = self.parse_expr_list()
            return {'type': 'assign', 'targets': targets, 'values': values}
        t = expr.get('type')
        if t == 'call':
            return {'type': 'call_stmt', 'fn': expr['fn'], 'args': expr['args']}
        if t == 'method_call':
            return {'type': 'method_call_stmt', 'obj': expr['obj'],
                    'method': expr['method'], 'args': expr['args']}
        raise SyntaxError(f"Unexpected expression statement: {expr}")

    def parse_expr_list(self):
        exprs = [self.parse_expr()]
        while self.match('COMMA'):
            exprs.append(self.parse_expr())
        return exprs

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check('KW', 'or'):
            self.consume()
            right = self.parse_and()
            left = {'type': 'binop', 'op': 'or', 'left': left, 'right': right}
        return left

    def parse_and(self):
        left = self.parse_compare()
        while self.check('KW', 'and'):
            self.consume()
            right = self.parse_compare()
            left = {'type': 'binop', 'op': 'and', 'left': left, 'right': right}
        return left

    def parse_compare(self):
        left = self.parse_bor()
        while self.check('OP') and self.peek()[1] in ('<','<=','>','>=','==','~='):
            op = self.consume()[1]
            right = self.parse_bor()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_bor(self):
        left = self.parse_bxor()
        while self.check('OP', '|'):
            self.consume()
            right = self.parse_bxor()
            left = {'type': 'binop', 'op': '|', 'left': left, 'right': right}
        return left

    def parse_bxor(self):
        left = self.parse_band()
        while self.check('OP', '~'):
            self.consume()
            right = self.parse_band()
            left = {'type': 'binop', 'op': '~', 'left': left, 'right': right}
        return left

    def parse_band(self):
        left = self.parse_shift()
        while self.check('OP', '&'):
            self.consume()
            right = self.parse_shift()
            left = {'type': 'binop', 'op': '&', 'left': left, 'right': right}
        return left

    def parse_shift(self):
        left = self.parse_concat()
        while self.check('OP') and self.peek()[1] in ('<<', '>>'):
            op = self.consume()[1]
            right = self.parse_concat()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_concat(self):
        left = self.parse_add()
        if self.check('OP', '..'):
            self.consume()
            right = self.parse_concat()
            return {'type': 'binop', 'op': '..', 'left': left, 'right': right}
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.check('OP') and self.peek()[1] in ('+', '-'):
            op = self.consume()[1]
            right = self.parse_mul()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.check('OP') and self.peek()[1] in ('*', '/', '%', '//'):
            op = self.consume()[1]
            right = self.parse_unary()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_unary(self):
        if self.check('KW', 'not'):
            self.consume()
            return {'type': 'unop', 'op': 'not', 'operand': self.parse_unary()}
        if self.check('OP', '-'):
            self.consume()
            return {'type': 'unop', 'op': '-', 'operand': self.parse_unary()}
        if self.check('OP', '#'):
            self.consume()
            return {'type': 'unop', 'op': '#', 'operand': self.parse_unary()}
        if self.check('OP', '~'):
            self.consume()
            return {'type': 'unop', 'op': '~', 'operand': self.parse_unary()}
        return self.parse_power()

    def parse_power(self):
        base = self.parse_suffixed_expr()
        if self.check('OP', '^'):
            self.consume()
            exp = self.parse_unary()
            return {'type': 'binop', 'op': '^', 'left': base, 'right': exp}
        return base

    def parse_suffixed_expr(self):
        expr = self.parse_primary()
        while True:
            if self.check('OP', '.'):
                self.consume()
                name = self.consume('NAME')[1]
                expr = {'type': 'field', 'obj': expr, 'name': name}
            elif self.check('LBRACK'):
                self.consume()
                key = self.parse_expr()
                self.consume('RBRACK')
                expr = {'type': 'index', 'obj': expr, 'key': key}
            elif self.check('COLON'):
                self.consume()
                method = self.consume('NAME')[1]
                args = self.parse_call_args()
                expr = {'type': 'method_call', 'obj': expr, 'method': method, 'args': args}
            elif self.check('LPAREN') or self.check('LBRACE') or self.check('STRING'):
                args = self.parse_call_args()
                expr = {'type': 'call', 'fn': expr, 'args': args}
            else:
                break
        return expr

    def parse_call_args(self):
        if self.check('LPAREN'):
            self.consume('LPAREN')
            args = []
            if not self.check('RPAREN'):
                args = self.parse_expr_list()
            self.consume('RPAREN')
            return args
        if self.check('LBRACE'):
            return [self.parse_table_ctor()]
        if self.check('STRING'):
            tok = self.consume('STRING')
            return [{'type': 'string', 'value': tok[1]}]
        raise SyntaxError(f"Expected call args at {self.peek()}")

    def parse_primary(self):
        tok = self.peek()
        if tok[0] == 'NUMBER':
            self.consume()
            v = tok[1]
            if v.startswith('0x') or v.startswith('0X'):
                return {'type': 'number', 'value': int(v, 16)}
            return {'type': 'number', 'value': float(v) if '.' in v or 'e' in v.lower() else int(v)}
        if tok[0] == 'STRING':
            self.consume()
            return {'type': 'string', 'value': tok[1]}
        if tok[0] == 'KW' and tok[1] == 'true':
            self.consume()
            return {'type': 'bool', 'value': True}
        if tok[0] == 'KW' and tok[1] == 'false':
            self.consume()
            return {'type': 'bool', 'value': False}
        if tok[0] == 'KW' and tok[1] == 'nil':
            self.consume()
            return {'type': 'nil'}
        if tok[0] == 'OP' and tok[1] == '...':
            self.consume()
            return {'type': 'vararg'}
        if tok[0] == 'NAME':
            self.consume()
            return {'type': 'var', 'name': tok[1]}
        if tok[0] == 'LPAREN':
            self.consume()
            expr = self.parse_expr()
            self.consume('RPAREN')
            if expr.get('type') in ('call', 'method_call', 'vararg'):
                return {'type': 'paren', 'inner': expr}
            return expr
        if tok[0] == 'LBRACE':
            return self.parse_table_ctor()
        if tok[0] == 'KW' and tok[1] == 'function':
            self.consume()
            params, is_vararg = self.parse_params()
            body = self.parse_block()
            self.consume('KW', 'end')
            return {'type': 'function', 'params': params, 'body': body, 'is_vararg': is_vararg}
        raise SyntaxError(f"Unexpected token {tok} at pos {self.pos}")

    def parse_table_ctor(self):
        self.consume('LBRACE')
        fields = []
        while not self.check('RBRACE'):
            if self.check('LBRACK'):
                self.consume()
                key = self.parse_expr()
                self.consume('RBRACK')
                self.consume('OP', '=')
                val = self.parse_expr()
                fields.append({'type': 'expr_field', 'key': key, 'value': val})
            elif self.peek()[0] == 'NAME' and self.peek(1)[0] == 'OP' and self.peek(1)[1] == '=':
                key = self.consume('NAME')[1]
                self.consume('OP', '=')
                val = self.parse_expr()
                fields.append({'type': 'string_field', 'key': key, 'value': val})
            else:
                val = self.parse_expr()
                fields.append({'type': 'array_field', 'value': val})
            if not self.match('COMMA') and not self.match('SEMI'):
                break
        self.consume('RBRACE')
        return {'type': 'table_constructor', 'fields': fields}


class VMCompileError(Exception):
    pass


def try_compile_vm(source, rng=None, debug=False):
    try:
        opmap = make_opmap()
        _patch_global_ops(opmap)
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        compiler.compile_chunk(ast)
        if rng is not None:
            from bytecode_cff import flatten_bytecode
            flatten_bytecode(compiler.proto, rng, opmap)
        bytecode = compiler.serialize()
        return bytecode, opmap
    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc()
        return None


def _patch_global_ops(opmap):
    g = globals()
    for name, val in opmap.items():
        g['OP_' + name] = val
    marker, dict_marker = mltn.pick_two_markers(opmap.values())
    g['REPEAT_MARKER'] = marker
    g['DICT_MARKER'] = dict_marker


def bytecode_to_lua(bytecode, rng, gen_name_fn, opmap=None, data_expr=None, detect_var=None):
    N = gen_name_fn
    data_v    = N(); u16_v     = N(); u16s_v    = N(); ldc_v     = N()
    ldi_v     = N(); ldp_v     = N(); consts_v  = N()
    protos_v  = N(); env_v     = N(); mk_v      = N(); fn_v      = N()
    args_v    = N(); i_v       = N(); j_v       = N(); nargs_v   = N()
    exec_v    = N()
    ok_v      = N(); err_v     = N()
    ubox_v    = N(); upidx_v   = N()

    p_d = N(); p_i = N(); p_v = N(); p_t = N(); p_j = N(); p_s = N(); p_k = N()
    p_bytes = N(); p_sign = N(); p_exp = N(); p_mant = N(); p_n = N(); p_ln = N()
    p_f32b = N(); p_f32sign = N(); p_f32exp = N(); p_f32mant = N(); p_f32n = N()
    p_raw = N(); p_newstate = N(); p_mask = N(); p_op = N(); p_a = N(); p_b = N(); p_cc = N(); p_o = N()
    p_rstate = N(); p_rprev = N()
    p_isvararg = N(); p_params = N(); p_nupvals = N(); p_updescs = N(); p_kind = N(); p_idx = N()
    p_loopu = N(); p_loopp = N()
    p_nprotos = N(); p_protos = N(); p_sz = N(); p_p = N(); p_ni = N()
    p_nconsts = N(); p_consts = N(); p_ci = N(); p_cv = N()
    p_nins = N(); p_pseed = N(); p_ins = N(); p_ii = N(); p_iv = N(); p_ns = N(); p_np = N()
    p_ubox = N(); p_vr = N(); p_rb = N(); p_args = N(); p_nargs = N(); p_va = N(); p_van = N()
    p_x = N(); p_val = N(); p_r = N()
    p_pc = N(); p_rd = N(); p_op2 = N(); p_a2 = N(); p_b2 = N(); p_c2 = N()
    p_fnv = N(); p_nargs2 = N(); p_nret = N(); p_callargs = N(); p_ncallargs = N(); p_jj = N(); p_kk = N(); p_res = N()
    p_objv = N(); p_mkey = N(); p_rawc = N(); p_multi = N(); p_mfn = N()
    p_cp = N(); p_childubox = N(); p_ud = N(); p_itf = N(); p_stt = N(); p_ctl = N()
    p_rbb = N(); p_getreg = N(); p_setreg = N(); p_boxreg = N(); p_proto = N()
    p_vtop = N()
    p_lim = N(); p_st = N()
    p_regparam = N()
    p_tj1 = N(); p_tj2 = N(); p_tj3 = N()
    p_cblen = N(); p_cbb = N(); p_cbi = N(); p_pseed2 = N(); p_rstate2 = N(); p_rprev2 = N()
    p_smv = N()
    p_strref = N(); p_strpool = N(); p_poolseed = N(); p_poollen = N(); p_poolraw = N()
    p_poolcount = N(); p_poolidx = N(); p_poolslen = N(); p_poolstr = N(); p_poolst = N(); p_poolpv = N()
    p_bodystart = N(); p_pst = N(); p_ppv = N(); p_ns = N(); p_mk = N()
    dec_v = N()
    p_marker = N(); p_dmarker = N(); p_opslen = N(); p_dictlen = N()
    p_opsbytes = N(); p_dictbytes = N(); p_rst = N(); p_rpv = N()
    p_dictionary = N(); p_dn = N(); p_dplen = N(); p_dflat = N(); p_dfi = N(); p_dpat = N()
    p_flatstream = N(); p_fi = N(); p_ops = N(); p_didx = N(); p_dcount = N(); p_dk = N()
    p_rlei = N(); p_rop = N(); p_rcount = N(); p_rk = N()
    p_out = N()
    p_fi = N()
    p_rv = N()

    om = opmap if opmap is not None else _DEFAULT_OPMAP
    def O(name): return om[name]

    uv_v = N()
    euv_v = N()
    p_eseed = N(); p_estate = N(); p_eprev = N(); p_eres = N(); p_esh = N()
    p_eraw = N(); p_enewstate = N(); p_emask = N(); p_eb = N()

    AB2  = f"{p_a},{p_i}={uv_v}({p_d},{p_i}) {p_b},{p_i}={uv_v}({p_d},{p_i}) "
    AB2C = f"{p_a},{p_i}={uv_v}({p_d},{p_i}) {p_b},{p_i}={uv_v}({p_d},{p_i}) {p_cc},{p_i}={uv_v}({p_d},{p_i}) "
    A2   = f"{p_a},{p_i}={uv_v}({p_d},{p_i}) "

    def ldi_cases():
        groups_ab2 = [
            ('LOAD_CONST','LOAD_VAR','SET_VAR','LOAD_GLOBAL','SET_GLOBAL','CLOSURE'),
            ('LOAD_UPVAL','SET_UPVAL'),
            ('RETURN','VARARG'),
            ('JUMP_FALSE','JUMP_TRUE','JUMP_FALSE_NK','JUMP_TRUE_NK'),
            ('UNM','LEN','NOT','BNOT'),
            ('FOR_PREP','FOR_LOOP','TFOR_LOOP'),
            ('DUP','MOVE'),
        ]
        groups_ab2c = [
            ('GET_TABLE','SET_TABLE','SET_LIST'),
            ('SET_LIST_MULTI',),
            ('GET_FIELD','SET_FIELD'),
            ('ADD','SUB','MUL','DIV','MOD','POW','CONCAT','IDIV','AND','OR',
             'BAND','BOR','BXOR','SHL','SHR'),
            ('EQ','NE','LT','LE','GT','GE'),
            ('CALL','CALL_METHOD'),
            ('TFOR_CALL',),
        ]
        groups_a2 = [('NEW_TABLE',), ('RETURN_NONE',), ('POP',), ('JUMP',), ('CLOSE_UPVAL',)]

        lines = []
        first = True
        for grp in groups_ab2:
            cond = " or ".join(f"{p_o}=={O(n)}" for n in grp)
            kw = "if" if first else "elseif"
            lines.append(f"{kw} {cond} then {AB2}")
            first = False
        for grp in groups_ab2c:
            cond = " or ".join(f"{p_o}=={O(n)}" for n in grp)
            lines.append(f"elseif {cond} then {AB2C}")
        for grp in groups_a2:
            cond = " or ".join(f"{p_o}=={O(n)}" for n in grp)
            lines.append(f"elseif {cond} then {A2}")
        lines.append("end")
        return " ".join(lines)

    dexpr = data_expr if data_expr is not None else "{}"

    lua = (
        f"local {data_v}={dexpr} "
        f"local function {u16_v}({p_d},{p_i}) return {p_d}[{p_i}]+({p_d}[{p_i}+1]*256) end "
        f"local function {u16s_v}({p_d},{p_i}) local {p_v}={p_d}[{p_i}]+({p_d}[{p_i}+1]*256) if {p_v}>=32768 then {p_v}={p_v}-65536 end return {p_v} end "
        f"local function {uv_v}({p_d},{p_i}) "
        f"local {p_res}=0 local {p_st}=0 "
        f"while true do "
        f"local {p_x}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"{p_res}={p_res}+bit32.lshift(bit32.band({p_x},0x7F),{p_st}) "
        f"if bit32.band({p_x},0x80)==0 then break end "
        f"{p_st}={p_st}+7 "
        f"end "
        f"return {p_res},{p_i} end "
        f"local {p_strpool} "
        f"local {p_bodystart} "
        f"do "
        f"local {p_poolseed}={data_v}[1] "
        f"local {p_poollen},{p_poolst}={uv_v}({data_v},2) "
        f"local {p_poolraw}={{}} "
        f"local {p_pst}={p_poolseed} local {p_ppv}={p_poolseed} "
        f"for {p_j}=0,{p_poollen}-1 do "
        f"local {p_ns}=({p_pst}*1103515245+12345)%256 "
        f"local {p_mk}=bit32.bxor({p_ns},({p_ppv}*31)%256)%256 "
        f"{p_poolraw}[{p_j}+1]=bit32.bxor({data_v}[{p_poolst}+{p_j}],{p_mk})%256 "
        f"{p_pst}={p_ns} {p_ppv}={p_mk} "
        f"end "
        f"local {p_poolidx}=1 "
        f"local {p_poolcount} {p_poolcount},{p_poolidx}={uv_v}({p_poolraw},{p_poolidx}) "
        f"{p_strpool}={{}} "
        f"for {p_j}=1,{p_poolcount} do "
        f"local {p_poolslen},{p_ni}={uv_v}({p_poolraw},{p_poolidx}) "
        f"{p_poolidx}={p_ni} "
        f"local {p_poolstr}='' "
        f"for {p_k}=0,{p_poolslen}-1 do {p_poolstr}={p_poolstr}..string.char({p_poolraw}[{p_poolidx}+{p_k}]) end "
        f"{p_poolidx}={p_poolidx}+{p_poolslen} "
        f"{p_strpool}[{p_j}]={p_poolstr} "
        f"end "
        f"{p_bodystart}={p_poolst}+{p_poollen} "
        f"end "
        f"local function {euv_v}({p_d},{p_i}) "
        f"local {p_eseed}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_estate}={p_eseed} local {p_eprev}={p_eseed} "
        f"local {p_eres}=0 local {p_esh}=0 "
        f"while true do "
        f"local {p_eraw}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_enewstate}=({p_estate}*1103515245+12345)%256 "
        f"local {p_emask}=bit32.bxor({p_enewstate},({p_eprev}*31)%256)%256 "
        f"local {p_eb}=bit32.bxor({p_eraw},{p_emask})%256 "
        f"{p_estate}={p_enewstate} {p_eprev}={p_emask} "
        f"{p_eres}={p_eres}+bit32.lshift(bit32.band({p_eb},0x7F),{p_esh}) "
        f"if bit32.band({p_eb},0x80)==0 then break end "
        f"{p_esh}={p_esh}+7 "
        f"end "
        f"return {p_eres},{p_i} end "
        f"local function {ldc_v}({p_d},{p_i}) "
        f"local {p_t}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"if {p_t}==0 then return nil,{p_i} "
        f"elseif {p_t}==1 then return {p_d}[{p_i}]==1,{p_i}+1 "
        f"elseif {p_t}==2 then "
        f"local {p_bytes}={{}} for {p_j}=0,7 do {p_bytes}[{p_j}+1]={p_d}[{p_i}+{p_j}] end {p_i}={p_i}+8 "
        f"local {p_sign}={p_bytes}[8]>=128 and 1 or 0 "
        f"local {p_exp}=(({p_bytes}[8]%128)*16)+math.floor({p_bytes}[7]/16) "
        f"local {p_mant}={p_bytes}[7]%16 "
        f"for {p_j}=6,1,-1 do {p_mant}={p_mant}*256+{p_bytes}[{p_j}] end "
        f"if {p_exp}==2047 then "
        f"if {p_mant}==0 then return ({p_sign}==1 and -math.huge or math.huge),{p_i} "
        f"else return (0/0),{p_i} end end "
        f"local {p_n} "
        f"if {p_exp}==0 then {p_n}={p_mant}*(2^(-1074)) "
        f"else {p_n}=(1+{p_mant}*(2^(-52)))*(2^({p_exp}-1023)) end "
        f"return ({p_sign}==1 and -{p_n} or {p_n}),{p_i} "
        f"end "
        f"if {p_t}==5 then "
        f"local {p_smv}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"if {p_smv}>=128 then {p_smv}={p_smv}-256 end "
        f"return {p_smv},{p_i} "
        f"end "
        f"if {p_t}==7 then "
        f"local {p_strref},{p_i}={uv_v}({p_d},{p_i}) "
        f"return {p_strpool}[{p_strref}+1],{p_i} "
        f"end "
        f"if {p_t}==6 then "
        f"local {p_f32b}={{}} for {p_j}=0,3 do {p_f32b}[{p_j}+1]={p_d}[{p_i}+{p_j}] end {p_i}={p_i}+4 "
        f"local {p_f32sign}={p_f32b}[4]>=128 and 1 or 0 "
        f"local {p_f32exp}=(({p_f32b}[4]%128)*2)+math.floor({p_f32b}[3]/128) "
        f"local {p_f32mant}=(({p_f32b}[3]%128)*65536)+({p_f32b}[2]*256)+{p_f32b}[1] "
        f"if {p_f32exp}==255 then "
        f"if {p_f32mant}==0 then return ({p_f32sign}==1 and -math.huge or math.huge),{p_i} "
        f"else return (0/0),{p_i} end end "
        f"local {p_f32n} "
        f"if {p_f32exp}==0 then {p_f32n}={p_f32mant}*(2^(-149)) "
        f"else {p_f32n}=(1+{p_f32mant}*(2^(-23)))*(2^({p_f32exp}-127)) end "
        f"return ({p_f32sign}==1 and -{p_f32n} or {p_f32n}),{p_i} "
        f"end "
        f"local {p_ln},{p_i}={uv_v}({p_d},{p_i}) "
        f"local {p_s}='' for {p_j}=0,{p_ln}-1 do {p_s}={p_s}..string.char({p_d}[{p_i}+{p_j}]) end "
        f"return {p_s},{p_i}+{p_ln} end "
        f"local function {dec_v}({p_d},{p_i},{p_ln},{p_rst},{p_rpv}) "
        f"local {p_out}={{}} "
        f"for {p_j}=0,{p_ln}-1 do "
        f"local {p_raw}={p_d}[{p_i}+{p_j}] "
        f"local {p_newstate}=({p_rst}*1103515245+12345)%256 "
        f"local {p_mask}=bit32.bxor({p_newstate},({p_rpv}*31)%256)%256 "
        f"local {p_rv}=bit32.bxor({p_raw},{p_mask})%256 "
        f"{p_out}[{p_j}+1]={p_rv} "
        f"{p_rst}={p_newstate} {p_rpv}={p_rv} "
        f"end "
        f"return {p_out},{p_rst},{p_rpv} end "
        f"local function {ldi_v}({p_d},{p_i},{p_op}) "
        f"local {p_a},{p_b},{p_cc}=nil,nil,nil "
        f"local {p_o}={p_op} "
        f"{ldi_cases()} "
        f"return {{{p_op},{p_a},{p_b},{p_cc}}},{p_i} end "
        f"local function {ldp_v}({p_d},{p_i}) "
        f"local {p_isvararg}={p_d}[{p_i}]==1 local {p_params}={p_d}[{p_i}+1] {p_i}={p_i}+2 "
        f"local {p_nupvals} {p_nupvals},{p_i}={uv_v}({p_d},{p_i}) "
        f"local {p_updescs}={{}} "
        f"for {p_loopu}=1,{p_nupvals} do "
        f"local {p_kind}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_idx} {p_idx},{p_i}={uv_v}({p_d},{p_i}) "
        f"{p_updescs}[#{p_updescs}+1]={{kind={p_kind},idx={p_idx}}} "
        f"end "
        f"local {p_nprotos} {p_nprotos},{p_i}={euv_v}({p_d},{p_i}) "
        f"local {p_protos}={{}} "
        f"for {p_loopp}=1,{p_nprotos} do "
        f"local {p_sz} {p_sz},{p_i}={euv_v}({p_d},{p_i}) "
        f"local {p_p},{p_ni}={ldp_v}({p_d},{p_i}) {p_i}={p_ni} "
        f"{p_protos}[#{p_protos}+1]={p_p} "
        f"end "
        f"local {p_nconsts} {p_nconsts},{p_i}={euv_v}({p_d},{p_i}) "
        f"local {p_pseed}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_cblen} {p_cblen},{p_i}={uv_v}({p_d},{p_i}) "
        f"local {p_cbb}={{}} "
        f"local {p_rstate}={p_pseed} local {p_rprev}={p_pseed} "
        f"for {p_ci}=1,{p_cblen} do "
        f"local {p_newstate}=({p_rstate}*1103515245+12345)%256 "
        f"local {p_mask}=bit32.bxor({p_newstate},({p_rprev}*31)%256)%256 "
        f"local {p_rawc}=bit32.bxor({p_d}[{p_i}+{p_ci}-1],{p_mask})%256 "
        f"{p_cbb}[{p_ci}]={p_rawc} "
        f"{p_rstate}={p_newstate} {p_rprev}={p_mask} "
        f"end "
        f"{p_i}={p_i}+{p_cblen} "
        f"local {p_cbi}=1 "
        f"local {p_consts}={{}} "
        f"for {p_ci}=1,{p_nconsts} do local {p_cv},{p_ni}={ldc_v}({p_cbb},{p_cbi}) {p_consts}[{p_ci}]={p_cv} {p_cbi}={p_ni} end "
        f"local {p_nins} {p_nins},{p_i}={euv_v}({p_d},{p_i}) "
        f"local {p_pseed2}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_marker}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_dmarker}={p_d}[{p_i}] {p_i}={p_i}+1 "
        f"local {p_opslen} {p_opslen},{p_i}={uv_v}({p_d},{p_i}) "
        f"local {p_opsbytes},{p_rst},{p_rpv}={dec_v}({p_d},{p_i},{p_opslen},{p_pseed2},{p_pseed2}) "
        f"{p_i}={p_i}+{p_opslen} "
        f"local {p_dictlen} {p_dictlen},{p_i}={uv_v}({p_d},{p_i}) "
        f"local {p_dictbytes},{p_rst},{p_rpv}={dec_v}({p_d},{p_i},{p_dictlen},{p_rst},{p_rpv}) "
        f"{p_i}={p_i}+{p_dictlen} "
        f"local {p_dn} {p_dn},{p_dfi}={uv_v}({p_dictbytes},1) "
        f"local {p_dictionary}={{}} "
        f"for {p_dk}=1,{p_dn} do "
        f"local {p_dplen} {p_dplen},{p_dfi}={uv_v}({p_dictbytes},{p_dfi}) "
        f"local {p_dpat}={{}} "
        f"for {p_j}=1,{p_dplen} do {p_dpat}[{p_j}]={p_dictbytes}[{p_dfi}] {p_dfi}={p_dfi}+1 end "
        f"{p_dictionary}[{p_dk}]={p_dpat} "
        f"end "
        f"local {p_flatstream}={{}} "
        f"{p_fi}=1 "
        f"while {p_fi}<=#{p_opsbytes} do "
        f"local {p_v}={p_opsbytes}[{p_fi}] "
        f"if {p_v}=={p_dmarker} then "
        f"local {p_didx}={p_opsbytes}[{p_fi}+1] "
        f"local {p_dpat}={p_dictionary}[{p_didx}+1] "
        f"for {p_j}=1,#{p_dpat} do {p_flatstream}[#{p_flatstream}+1]={p_dpat}[{p_j}] end "
        f"{p_fi}={p_fi}+3 "
        f"else "
        f"{p_flatstream}[#{p_flatstream}+1]={p_v} "
        f"{p_fi}={p_fi}+1 "
        f"end "
        f"end "
        f"local {p_ops}={{}} "
        f"{p_rlei}=1 "
        f"while #{p_ops}<{p_nins} and {p_rlei}<=#{p_flatstream} do "
        f"local {p_v}={p_flatstream}[{p_rlei}] "
        f"if {p_v}=={p_marker} then "
        f"local {p_rop}={p_flatstream}[{p_rlei}+1] "
        f"local {p_rcount}={p_flatstream}[{p_rlei}+2] "
        f"for {p_rk}=1,{p_rcount} do if #{p_ops}>={p_nins} then break end {p_ops}[#{p_ops}+1]={p_rop} end "
        f"{p_rlei}={p_rlei}+3 "
        f"else "
        f"{p_ops}[#{p_ops}+1]={p_v} "
        f"{p_rlei}={p_rlei}+1 "
        f"end "
        f"end "
        f"local {p_ins}={{}} "
        f"for {p_ii}=1,{p_nins} do "
        f"local {p_iv},{p_ni}={ldi_v}({p_d},{p_i},{p_ops}[{p_ii}]) "
        f"{p_ins}[{p_ii}]={p_iv} {p_i}={p_ni} "
        f"end "
        f"return {{is_vararg={p_isvararg},params={p_params},updescs={p_updescs},protos={p_protos},consts={p_consts},ins={p_ins}}},{p_i} end "
        f"local {env_v}=(getfenv and getfenv(0)) or _ENV or _G or {{}} "

        f"local function {exec_v}({p_proto},{ubox_v},...) "
        f"local {p_vr}={{}} "
        f"local {p_rb}={{}} "
        f"local {p_vtop}=0 "
        f"local {args_v}={{...}} "
        f"local {nargs_v}=select('#',...) "
        f"local {p_va}={{}} "
        f"local {p_van}=0 "
        f"if {p_proto}.is_vararg then "
        f"for {i_v}={p_proto}.params+1,{nargs_v} do {p_va}[{i_v}-{p_proto}.params]={args_v}[{i_v}] end "
        f"{p_van}={nargs_v}-{p_proto}.params if {p_van}<0 then {p_van}=0 end "
        f"end "
        f"for {i_v}=1,{p_proto}.params do {p_vr}[{i_v}-1]={args_v}[{i_v}] end "
        f"local {consts_v}={p_proto}.consts "
        f"local {p_ins}={p_proto}.ins "
        f"local {protos_v}={p_proto}.protos "
        f"local function {p_getreg}({p_regparam}) local {p_x}={p_rb}[{p_regparam}] if {p_x}~=nil then return {p_x}.v end return {p_vr}[{p_regparam}] end "
        f"local function {p_setreg}({p_regparam},{p_val}) local {p_x}={p_rb}[{p_regparam}] if {p_x}~=nil then {p_x}.v={p_val} else {p_vr}[{p_regparam}]={p_val} end end "
        f"local function {p_boxreg}({p_regparam}) "
        f"local {p_x}={p_rb}[{p_regparam}] "
        f"if {p_x}==nil then {p_x}={{v={p_vr}[{p_regparam}]}} {p_rb}[{p_regparam}]={p_x} end "
        f"return {p_x} end "
        f"local {p_pc}=1 "
        f"while {p_pc}<=#{p_ins} do "
        + (
            f"if {detect_var} then "
            f"local {p_tj1}={rng.randint(1000,9999)} "
            f"local {p_tj2}={p_tj1}+{rng.randint(1000,9999)} "
            f"local {p_tj3}=true "
            f"while {p_tj3} do {p_tj2}={p_tj2}+1 end "
            f"end "
            if detect_var else ""
        ) +
        f"local {p_rd}={p_ins}[{p_pc}] "
        f"local {p_op2}={p_rd}[1] local {p_a2}={p_rd}[2] local {p_b2}={p_rd}[3] local {p_c2}={p_rd}[4] "
        f"{p_pc}={p_pc}+1 "
        f"if {p_op2}=={O('LOAD_CONST')} then {p_setreg}({p_a2},{consts_v}[{p_b2}+1]) "
        f"elseif {p_op2}=={O('LOAD_VAR')} then {p_setreg}({p_a2},{p_getreg}({p_b2})) "
        f"elseif {p_op2}=={O('SET_VAR')} then {p_setreg}({p_b2},{p_getreg}({p_a2})) "
        f"elseif {p_op2}=={O('LOAD_GLOBAL')} then {p_setreg}({p_a2},{env_v}[{consts_v}[{p_b2}+1]]) "
        f"elseif {p_op2}=={O('SET_GLOBAL')} then {env_v}[{consts_v}[{p_a2}+1]]={p_getreg}({p_b2}) "
        f"elseif {p_op2}=={O('LOAD_UPVAL')} then "
        f"local {p_x}={ubox_v}[{p_b2}] "
        f"if {p_x} then {p_setreg}({p_a2},{p_x}.v) else {p_setreg}({p_a2},nil) end "
        f"elseif {p_op2}=={O('SET_UPVAL')} then "
        f"local {p_x}={ubox_v}[{p_a2}] "
        f"if {p_x} then {p_x}.v={p_getreg}({p_b2}) end "
        f"{p_setreg}({p_a2},{p_getreg}({p_b2})) "
        f"elseif {p_op2}=={O('GET_TABLE')} then {p_setreg}({p_a2},{p_getreg}({p_b2})[{p_getreg}({p_c2})]) "
        f"elseif {p_op2}=={O('SET_TABLE')} then {p_getreg}({p_a2})[{p_getreg}({p_b2})]={p_getreg}({p_c2}) "
        f"elseif {p_op2}=={O('NEW_TABLE')} then {p_setreg}({p_a2},{{}}) "
        f"elseif {p_op2}=={O('SET_LIST')} then {p_getreg}({p_a2})[{consts_v}[{p_b2}+1]]={p_getreg}({p_c2}) "
        f"elseif {p_op2}=={O('SET_LIST_MULTI')} then "
        f"local {p_jj}={p_b2} local {p_kk}={consts_v}[{p_c2}+1] "
        f"local {p_t}={p_getreg}({p_a2}) "
        f"while {p_jj}<{p_vtop} do {p_t}[{p_kk}]={p_getreg}({p_jj}) {p_kk}={p_kk}+1 {p_jj}={p_jj}+1 end "
        f"elseif {p_op2}=={O('GET_FIELD')} then {p_setreg}({p_a2},{p_getreg}({p_b2})[{consts_v}[{p_c2}+1]]) "
        f"elseif {p_op2}=={O('SET_FIELD')} then {p_getreg}({p_a2})[{consts_v}[{p_b2}+1]]={p_getreg}({p_c2}) "
        f"elseif {p_op2}=={O('ADD')} then {p_setreg}({p_a2},{p_getreg}({p_b2})+{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('SUB')} then {p_setreg}({p_a2},{p_getreg}({p_b2})-{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('MUL')} then {p_setreg}({p_a2},{p_getreg}({p_b2})*{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('DIV')} then {p_setreg}({p_a2},{p_getreg}({p_b2})/{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('MOD')} then {p_setreg}({p_a2},{p_getreg}({p_b2})%{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('POW')} then {p_setreg}({p_a2},{p_getreg}({p_b2})^{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('CONCAT')} then {p_setreg}({p_a2},{p_getreg}({p_b2})..{p_getreg}({p_c2})) "
        f"elseif {p_op2}=={O('IDIV')} then {p_setreg}({p_a2},math.floor({p_getreg}({p_b2})/{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('BAND')} then {p_setreg}({p_a2},bit32.band({p_getreg}({p_b2}),{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('BOR')} then {p_setreg}({p_a2},bit32.bor({p_getreg}({p_b2}),{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('BXOR')} then {p_setreg}({p_a2},bit32.bxor({p_getreg}({p_b2}),{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('BNOT')} then {p_setreg}({p_a2},bit32.bnot({p_getreg}({p_b2}))) "
        f"elseif {p_op2}=={O('SHL')} then {p_setreg}({p_a2},bit32.lshift({p_getreg}({p_b2}),{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('SHR')} then {p_setreg}({p_a2},bit32.rshift({p_getreg}({p_b2}),{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('UNM')} then {p_setreg}({p_a2},-{p_getreg}({p_b2})) "
        f"elseif {p_op2}=={O('LEN')} then {p_setreg}({p_a2},#{p_getreg}({p_b2})) "
        f"elseif {p_op2}=={O('NOT')} then {p_setreg}({p_a2},not {p_getreg}({p_b2})) "
        f"elseif {p_op2}=={O('AND')} then "
        f"if not {p_getreg}({p_b2}) then {p_setreg}({p_a2},{p_getreg}({p_b2})) else {p_setreg}({p_a2},{p_getreg}({p_c2})) end "
        f"elseif {p_op2}=={O('OR')} then "
        f"if {p_getreg}({p_b2}) then {p_setreg}({p_a2},{p_getreg}({p_b2})) else {p_setreg}({p_a2},{p_getreg}({p_c2})) end "
        f"elseif {p_op2}=={O('EQ')} then {p_setreg}({p_a2},({p_getreg}({p_b2})=={p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('NE')} then {p_setreg}({p_a2},({p_getreg}({p_b2})~={p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('LT')} then {p_setreg}({p_a2},({p_getreg}({p_b2})<{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('LE')} then {p_setreg}({p_a2},({p_getreg}({p_b2})<={p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('GT')} then {p_setreg}({p_a2},({p_getreg}({p_b2})>{p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('GE')} then {p_setreg}({p_a2},({p_getreg}({p_b2})>={p_getreg}({p_c2}))) "
        f"elseif {p_op2}=={O('JUMP')} then {p_pc}={p_a2}+1 "
        f"elseif {p_op2}=={O('JUMP_FALSE')} then if not {p_getreg}({p_a2}) then {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('JUMP_TRUE')} then if {p_getreg}({p_a2}) then {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('JUMP_FALSE_NK')} then if not {p_getreg}({p_a2}) then {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('JUMP_TRUE_NK')} then if {p_getreg}({p_a2}) then {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('CALL')} then "
        f"local {p_fnv}={p_getreg}({p_a2}) local {p_nargs2}={p_b2} local {p_nret}={p_c2} "
        f"local {p_callargs}={{}} local {p_ncallargs}=0 "
        f"if {p_nargs2}==255 then "
        f"local {p_jj}={p_a2}+1 local {p_kk}=1 while {p_jj}<{p_vtop} do {p_callargs}[{p_kk}]={p_getreg}({p_jj}) {p_jj}={p_jj}+1 {p_kk}={p_kk}+1 end "
        f"{p_ncallargs}={p_kk}-1 "
        f"else for {p_jj}=1,{p_nargs2} do {p_callargs}[{p_jj}]={p_getreg}({p_a2}+{p_jj}) end {p_ncallargs}={p_nargs2} end "
        f"if type({p_fnv})=='function' then "
        f"local {p_res}=table.pack({p_fnv}(table.unpack({p_callargs},1,{p_ncallargs}))) "
        f"if {p_nret}==255 then "
        f"for {p_jj}=1,{p_res}.n do {p_setreg}({p_a2}+{p_jj}-1,{p_res}[{p_jj}]) end "
        f"{p_setreg}({p_a2}+{p_res}.n,nil) "
        f"{p_vtop}={p_a2}+{p_res}.n "
        f"elseif {p_nret}>0 then {p_setreg}({p_a2},{p_res}[1]) end "
        f"else error('attempt to call a '..type({p_fnv})..' value',0) end "
        f"elseif {p_op2}=={O('CALL_METHOD')} then "
        f"local {p_objv}={p_getreg}({p_a2}) local {p_mkey}={consts_v}[{p_b2}+1] "
        f"local {p_rawc}={p_c2} local {p_multi}=false "
        f"if {p_rawc}>=256 then {p_multi}=true {p_rawc}={p_rawc}-256 end "
        f"local {p_nargs2}={p_rawc} "
        f"local {p_mfn}={p_objv}[{p_mkey}] "
        f"local {p_callargs}={{{p_objv}}} local {p_ncallargs}=1 "
        f"if {p_nargs2}==255 then "
        f"local {p_jj}={p_a2}+1 local {p_kk}=2 while {p_jj}<{p_vtop} do {p_callargs}[{p_kk}]={p_getreg}({p_jj}) {p_jj}={p_jj}+1 {p_kk}={p_kk}+1 end "
        f"{p_ncallargs}={p_kk}-1 "
        f"else for {p_jj}=1,{p_nargs2} do {p_callargs}[{p_jj}+1]={p_getreg}({p_a2}+{p_jj}) end {p_ncallargs}=1+{p_nargs2} end "
        f"if type({p_mfn})=='function' then "
        f"local {p_res}=table.pack({p_mfn}(table.unpack({p_callargs},1,{p_ncallargs}))) "
        f"if {p_multi} then "
        f"for {p_jj}=1,{p_res}.n do {p_setreg}({p_a2}+{p_jj}-1,{p_res}[{p_jj}]) end "
        f"{p_setreg}({p_a2}+{p_res}.n,nil) "
        f"{p_vtop}={p_a2}+{p_res}.n "
        f"elseif {p_res}.n>=1 then {p_setreg}({p_a2},{p_res}[1]) end "
        f"else error('attempt to call a '..type({p_mfn})..' value',0) end "
        f"elseif {p_op2}=={O('RETURN')} then "
        f"local {p_rbb}={p_a2} local {p_nret}={p_b2} "
        f"if {p_nret}==1 then return {p_getreg}({p_rbb}) "
        f"elseif {p_nret}==0 then return "
        f"elseif {p_nret}==255 then "
        f"local {p_res}={{}} local {p_jj}=0 "
        f"while {p_rbb}+{p_jj}<{p_vtop} do {p_res}[{p_jj}+1]={p_getreg}({p_rbb}+{p_jj}) {p_jj}={p_jj}+1 end "
        f"return table.unpack({p_res}) "
        f"else local {p_res}={{}} for {p_jj}=0,{p_nret}-1 do {p_res}[{p_jj}+1]={p_getreg}({p_rbb}+{p_jj}) end return table.unpack({p_res}) end "
        f"elseif {p_op2}=={O('RETURN_NONE')} then return "
        f"elseif {p_op2}=={O('VARARG')} then "
        f"local {p_nret}={p_b2} "
        f"if {p_nret}==255 then for {p_jj}=1,{p_van} do {p_setreg}({p_a2}+{p_jj}-1,{p_va}[{p_jj}]) end "
        f"{p_setreg}({p_a2}+{p_van},nil) "
        f"{p_vtop}={p_a2}+{p_van} "
        f"elseif {p_nret}==1 then {p_setreg}({p_a2},{p_va}[1]) end "
        f"elseif {p_op2}=={O('CLOSURE')} then "
        f"local {p_cp}={protos_v}[{p_b2}+1] "
        f"local {p_childubox}={{}} "
        f"for {p_ii}=1,#{p_cp}.updescs do "
        f"local {p_ud}={p_cp}.updescs[{p_ii}] "
        f"if {p_ud}.kind==0 then {p_childubox}[{p_ii}-1]={p_boxreg}({p_ud}.idx) "
        f"else {p_childubox}[{p_ii}-1]={ubox_v}[{p_ud}.idx] end "
        f"end "
        f"{p_setreg}({p_a2},function(...) return {exec_v}({p_cp},{p_childubox},...) end) "
        f"elseif {p_op2}=={O('FOR_PREP')} then "
        f"local {p_iv}={p_getreg}({p_a2}) local {p_lim}={p_getreg}({p_a2}+1) local {p_st}={p_getreg}({p_a2}+2) "
        f"if not(({p_st}>0 and {p_iv}<={p_lim}) or ({p_st}<0 and {p_iv}>={p_lim})) then {p_pc}={p_b2}+1 "
        f"else {p_setreg}({p_a2}+3,{p_iv}) end "
        f"elseif {p_op2}=={O('FOR_LOOP')} then "
        f"local {p_iv}={p_getreg}({p_a2}+3)+{p_getreg}({p_a2}+2) "
        f"local {p_lim}={p_getreg}({p_a2}+1) local {p_st}={p_getreg}({p_a2}+2) "
        f"if ({p_st}>0 and {p_iv}<={p_lim}) or ({p_st}<0 and {p_iv}>={p_lim}) then {p_setreg}({p_a2}+3,{p_iv}) {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('TFOR_CALL')} then "
        f"local {p_itf}={p_getreg}({p_a2}) local {p_stt}={p_getreg}({p_a2}+1) local {p_ctl}={p_getreg}({p_a2}+2) "
        f"local {p_res}=table.pack({p_itf}({p_stt},{p_ctl})) "
        f"for {p_jj}=1,{p_c2} do {p_setreg}({p_a2}+2+{p_jj},{p_res}[{p_jj}]) end "
        f"{p_setreg}({p_a2}+2,{p_res}[1]) "
        f"elseif {p_op2}=={O('TFOR_LOOP')} then "
        f"if {p_getreg}({p_a2})==nil then {p_pc}={p_b2}+1 end "
        f"elseif {p_op2}=={O('CLOSE_UPVAL')} then "
        f"local {p_x}={p_rb}[{p_a2}] if {p_x}~=nil then {p_vr}[{p_a2}]={p_x}.v {p_rb}[{p_a2}]=nil end "
        f"elseif {p_op2}=={O('MOVE')} then {p_setreg}({p_a2},{p_getreg}({p_b2})) "
        f"end "
        f"end "
        f"end "

        f"local {fn_v} "
        f"do local {i_v},{j_v}={ldp_v}({data_v},{p_bodystart}) {fn_v}=function(...) return {exec_v}({i_v},{{}},...) end end "
        f"return {fn_v}(...) "
    )
    return lua
