import struct
from vm_opcodes import make_opmap, CANONICAL_OPS

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

TYPE_NIL    = 0
TYPE_BOOL   = 1
TYPE_NUMBER = 2
TYPE_STRING = 3
TYPE_FUNC   = 4

def encode_const(val):
    if val is None:
        return bytes([TYPE_NIL])
    if isinstance(val, bool):
        return bytes([TYPE_BOOL, 1 if val else 0])
    if isinstance(val, (int, float)):
        return bytes([TYPE_NUMBER]) + struct.pack('<d', float(val))
    if isinstance(val, str):
        enc = val.encode('utf-8')
        return bytes([TYPE_STRING]) + struct.pack('<H', len(enc)) + enc
    return bytes([TYPE_NIL])

class Instruction:
    __slots__ = ('op', 'a', 'b', 'c')

    def __init__(self, op, a=None, b=None, c=None):
        self.op = op
        self.a = a
        self.b = b
        self.c = c

    def to_bytes(self):
        b = bytes([self.op])
        for v in (self.a, self.b, self.c):
            if v is not None:
                b += struct.pack('<H', v & 0xFFFF)
        return b

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

    def serialize(self):
        data = bytes([int(self.is_vararg), self.params])
        data += struct.pack('<H', len(self.upvals))
        for kind, idx in self.upvals:
            data += bytes([kind])
            data += struct.pack('<H', idx)
        data += struct.pack('<H', len(self.protos))
        for p in self.protos:
            s = p.serialize()
            data += struct.pack('<I', len(s)) + s
        data += struct.pack('<H', len(self.consts))
        for c in self.consts:
            data += encode_const(c)
        data += struct.pack('<H', len(self.instructions))
        for ins in self.instructions:
            data += ins.to_bytes()
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
        return self.proto.serialize()


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


def try_compile_vm(source, debug=False):
    try:
        opmap = make_opmap()
        _patch_global_ops(opmap)
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        compiler.compile_chunk(ast)
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


def bytecode_to_lua(bytecode, rng, gen_name_fn, opmap=None, data_expr=None):
    N = gen_name_fn
    data_v    = N(); u16_v     = N(); u16s_v    = N(); ldc_v     = N()
    ldi_v     = N(); ldp_v     = N(); consts_v  = N()
    protos_v  = N(); env_v     = N(); mk_v      = N(); fn_v      = N()
    args_v    = N(); i_v       = N(); j_v       = N(); nargs_v   = N()
    exec_v    = N()
    ok_v      = N(); err_v     = N()
    ubox_v    = N(); upidx_v   = N()

    om = opmap if opmap is not None else _DEFAULT_OPMAP
    def O(name): return om[name]

    AB2  = f"a={u16_v}(d,i) i=i+2 b={u16_v}(d,i) i=i+2 "
    AB2C = f"a={u16_v}(d,i) i=i+2 b={u16_v}(d,i) i=i+2 cc={u16_v}(d,i) i=i+2 "
    A2   = f"a={u16_v}(d,i) i=i+2 "

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
            cond = " or ".join(f"o=={O(n)}" for n in grp)
            kw = "if" if first else "elseif"
            lines.append(f"{kw} {cond} then {AB2}")
            first = False
        for grp in groups_ab2c:
            cond = " or ".join(f"o=={O(n)}" for n in grp)
            lines.append(f"elseif {cond} then {AB2C}")
        for grp in groups_a2:
            cond = " or ".join(f"o=={O(n)}" for n in grp)
            lines.append(f"elseif {cond} then {A2}")
        lines.append("end")
        return " ".join(lines)

    dexpr = data_expr if data_expr is not None else "{}"

    lua = (
        f"local {data_v}={dexpr} "
        f"local function {u16_v}(d,i) return d[i]+(d[i+1]*256) end "
        f"local function {u16s_v}(d,i) local v=d[i]+(d[i+1]*256) if v>=32768 then v=v-65536 end return v end "
        f"local function {ldc_v}(d,i) "
        f"local t=d[i] i=i+1 "
        f"if t==0 then return nil,i "
        f"elseif t==1 then return d[i]==1,i+1 "
        f"elseif t==2 then "
        f"local bytes={{}} for j=0,7 do bytes[j+1]=d[i+j] end i=i+8 "
        f"local sign=bytes[8]>=128 and 1 or 0 "
        f"local exp=((bytes[8]%128)*16)+math.floor(bytes[7]/16) "
        f"local mant=bytes[7]%16 "
        f"for j=6,1,-1 do mant=mant*256+bytes[j] end "
        f"if exp==2047 then "
        f"if mant==0 then return (sign==1 and -math.huge or math.huge),i "
        f"else return (0/0),i end end "
        f"local n "
        f"if exp==0 then n=mant*(2^(-1074)) "
        f"else n=(1+mant*(2^(-52)))*(2^(exp-1023)) end "
        f"return (sign==1 and -n or n),i "
        f"end "
        f"local ln={u16_v}(d,i) i=i+2 "
        f"local s='' for j=0,ln-1 do s=s..string.char(d[i+j]) end "
        f"return s,i+ln end "
        f"local function {ldi_v}(d,i) "
        f"local op=d[i] i=i+1 "
        f"local a,b,cc=nil,nil,nil "
        f"local o=op "
        f"{ldi_cases()} "
        f"return {{op,a,b,cc}},i end "
        f"local function {ldp_v}(d,i) "
        f"local is_vararg=d[i]==1 local params=d[i+1] i=i+2 "
        f"local nupvals={u16_v}(d,i) i=i+2 "
        f"local updescs={{}} "
        f"for _=1,nupvals do "
        f"local kind=d[i] i=i+1 "
        f"local idx={u16_v}(d,i) i=i+2 "
        f"updescs[#updescs+1]={{kind=kind,idx=idx}} "
        f"end "
        f"local nprotos={u16_v}(d,i) i=i+2 "
        f"local protos={{}} "
        f"for _=1,nprotos do "
        f"local sz=d[i]+(d[i+1]*256)+(d[i+2]*65536)+(d[i+3]*16777216) i=i+4 "
        f"local p,ni={ldp_v}(d,i) i=ni "
        f"protos[#protos+1]=p "
        f"end "
        f"local nconsts={u16_v}(d,i) i=i+2 "
        f"local consts={{}} "
        f"for _ci=1,nconsts do local cv,ni={ldc_v}(d,i) consts[_ci]=cv i=ni end "
        f"local nins={u16_v}(d,i) i=i+2 "
        f"local ins={{}} "
        f"for _ii=1,nins do local iv,ni={ldi_v}(d,i) ins[_ii]=iv i=ni end "
        f"return {{is_vararg=is_vararg,params=params,updescs=updescs,protos=protos,consts=consts,ins=ins}},i end "
        f"local {env_v}=(getfenv and getfenv(0)) or _ENV or _G or {{}} "

        f"local function {exec_v}(proto,{ubox_v},...) "
        f"local vr={{}} "
        f"local rb={{}} "
        f"local {args_v}={{...}} "
        f"local {nargs_v}=select('#',...) "
        f"local va={{}} "
        f"if proto.is_vararg then "
        f"for {i_v}=proto.params+1,{nargs_v} do va[{i_v}-proto.params]={args_v}[{i_v}] end "
        f"end "
        f"for {i_v}=1,proto.params do vr[{i_v}-1]={args_v}[{i_v}] end "
        f"local {consts_v}=proto.consts "
        f"local ins=proto.ins "
        f"local {protos_v}=proto.protos "
        f"local function getreg(r) local x=rb[r] if x~=nil then return x.v end return vr[r] end "
        f"local function setreg(r,val) local x=rb[r] if x~=nil then x.v=val else vr[r]=val end end "
        f"local function boxreg(r) "
        f"local x=rb[r] "
        f"if x==nil then x={{v=vr[r]}} rb[r]=x end "
        f"return x end "
        f"local pc=1 "
        f"while pc<=#ins do "
        f"local rd=ins[pc] "
        f"local op=rd[1] local a=rd[2] local b=rd[3] local c=rd[4] "
        f"pc=pc+1 "
        f"if op=={O('LOAD_CONST')} then setreg(a,{consts_v}[b+1]) "
        f"elseif op=={O('LOAD_VAR')} then setreg(a,getreg(b)) "
        f"elseif op=={O('SET_VAR')} then setreg(b,getreg(a)) "
        f"elseif op=={O('LOAD_GLOBAL')} then setreg(a,{env_v}[{consts_v}[b+1]]) "
        f"elseif op=={O('SET_GLOBAL')} then {env_v}[{consts_v}[a+1]]=getreg(b) "
        f"elseif op=={O('LOAD_UPVAL')} then "
        f"local ub={ubox_v}[b] "
        f"if ub then setreg(a,ub.v) else setreg(a,nil) end "
        f"elseif op=={O('SET_UPVAL')} then "
        f"local ub={ubox_v}[a] "
        f"if ub then ub.v=getreg(b) end "
        f"setreg(a,getreg(b)) "
        f"elseif op=={O('GET_TABLE')} then setreg(a,getreg(b)[getreg(c)]) "
        f"elseif op=={O('SET_TABLE')} then getreg(a)[getreg(b)]=getreg(c) "
        f"elseif op=={O('NEW_TABLE')} then setreg(a,{{}}) "
        f"elseif op=={O('SET_LIST')} then getreg(a)[{consts_v}[b+1]]=getreg(c) "
        f"elseif op=={O('SET_LIST_MULTI')} then "
        f"local jj=b local ii={consts_v}[c+1] "
        f"local t=getreg(a) "
        f"while getreg(jj)~=nil do t[ii]=getreg(jj) ii=ii+1 jj=jj+1 end "
        f"elseif op=={O('GET_FIELD')} then setreg(a,getreg(b)[{consts_v}[c+1]]) "
        f"elseif op=={O('SET_FIELD')} then getreg(a)[{consts_v}[b+1]]=getreg(c) "
        f"elseif op=={O('ADD')} then setreg(a,getreg(b)+getreg(c)) "
        f"elseif op=={O('SUB')} then setreg(a,getreg(b)-getreg(c)) "
        f"elseif op=={O('MUL')} then setreg(a,getreg(b)*getreg(c)) "
        f"elseif op=={O('DIV')} then setreg(a,getreg(b)/getreg(c)) "
        f"elseif op=={O('MOD')} then setreg(a,getreg(b)%getreg(c)) "
        f"elseif op=={O('POW')} then setreg(a,getreg(b)^getreg(c)) "
        f"elseif op=={O('CONCAT')} then setreg(a,getreg(b)..getreg(c)) "
        f"elseif op=={O('IDIV')} then setreg(a,math.floor(getreg(b)/getreg(c))) "
        f"elseif op=={O('BAND')} then setreg(a,bit32.band(getreg(b),getreg(c))) "
        f"elseif op=={O('BOR')} then setreg(a,bit32.bor(getreg(b),getreg(c))) "
        f"elseif op=={O('BXOR')} then setreg(a,bit32.bxor(getreg(b),getreg(c))) "
        f"elseif op=={O('BNOT')} then setreg(a,bit32.bnot(getreg(b))) "
        f"elseif op=={O('SHL')} then setreg(a,bit32.lshift(getreg(b),getreg(c))) "
        f"elseif op=={O('SHR')} then setreg(a,bit32.rshift(getreg(b),getreg(c))) "
        f"elseif op=={O('UNM')} then setreg(a,-getreg(b)) "
        f"elseif op=={O('LEN')} then setreg(a,#getreg(b)) "
        f"elseif op=={O('NOT')} then setreg(a,not getreg(b)) "
        f"elseif op=={O('AND')} then "
        f"if not getreg(b) then setreg(a,getreg(b)) else setreg(a,getreg(c)) end "
        f"elseif op=={O('OR')} then "
        f"if getreg(b) then setreg(a,getreg(b)) else setreg(a,getreg(c)) end "
        f"elseif op=={O('EQ')} then setreg(a,(getreg(b)==getreg(c))) "
        f"elseif op=={O('NE')} then setreg(a,(getreg(b)~=getreg(c))) "
        f"elseif op=={O('LT')} then setreg(a,(getreg(b)<getreg(c))) "
        f"elseif op=={O('LE')} then setreg(a,(getreg(b)<=getreg(c))) "
        f"elseif op=={O('GT')} then setreg(a,(getreg(b)>getreg(c))) "
        f"elseif op=={O('GE')} then setreg(a,(getreg(b)>=getreg(c))) "
        f"elseif op=={O('JUMP')} then pc=a+1 "
        f"elseif op=={O('JUMP_FALSE')} then if not getreg(a) then pc=b+1 end "
        f"elseif op=={O('JUMP_TRUE')} then if getreg(a) then pc=b+1 end "
        f"elseif op=={O('JUMP_FALSE_NK')} then if not getreg(a) then pc=b+1 end "
        f"elseif op=={O('JUMP_TRUE_NK')} then if getreg(a) then pc=b+1 end "
        f"elseif op=={O('CALL')} then "
        f"local fnv=getreg(a) local nargs=b local nret=c "
        f"local callargs={{}} local ncallargs=0 "
        f"if nargs==255 then "
        f"local jj=a+1 local kk=1 while getreg(jj)~=nil do callargs[kk]=getreg(jj) jj=jj+1 kk=kk+1 end "
        f"ncallargs=kk-1 "
        f"else for jj=1,nargs do callargs[jj]=getreg(a+jj) end ncallargs=nargs end "
        f"if type(fnv)=='function' then "
        f"local res=table.pack(fnv(table.unpack(callargs,1,ncallargs))) "
        f"if nret==255 then "
        f"for jj=1,res.n do setreg(a+jj-1,res[jj]) end "
        f"setreg(a+res.n,nil) "
        f"elseif nret>0 then setreg(a,res[1]) end "
        f"else error('attempt to call a '..type(fnv)..' value',0) end "
        f"elseif op=={O('CALL_METHOD')} then "
        f"local objv=getreg(a) local mkey={consts_v}[b+1] "
        f"local rawc=c local multi=false "
        f"if rawc>=256 then multi=true rawc=rawc-256 end "
        f"local nargs=rawc "
        f"local mfn=objv[mkey] "
        f"local callargs={{objv}} local ncallargs=1 "
        f"if nargs==255 then "
        f"local jj=a+1 local kk=2 while getreg(jj)~=nil do callargs[kk]=getreg(jj) jj=jj+1 kk=kk+1 end "
        f"ncallargs=kk-1 "
        f"else for jj=1,nargs do callargs[jj+1]=getreg(a+jj) end ncallargs=1+nargs end "
        f"if type(mfn)=='function' then "
        f"local res=table.pack(mfn(table.unpack(callargs,1,ncallargs))) "
        f"if multi then "
        f"for jj=1,res.n do setreg(a+jj-1,res[jj]) end "
        f"setreg(a+res.n,nil) "
        f"elseif res.n>=1 then setreg(a,res[1]) end "
        f"else error('attempt to call a '..type(mfn)..' value',0) end "
        f"elseif op=={O('RETURN')} then "
        f"local rbb=a local nret=b "
        f"if nret==1 then return getreg(rbb) "
        f"elseif nret==0 then return "
        f"elseif nret==255 then "
        f"local res={{}} local jj=0 "
        f"while getreg(rbb+jj)~=nil do res[jj+1]=getreg(rbb+jj) jj=jj+1 end "
        f"return table.unpack(res) "
        f"else local res={{}} for jj=0,nret-1 do res[jj+1]=getreg(rbb+jj) end return table.unpack(res) end "
        f"elseif op=={O('RETURN_NONE')} then return "
        f"elseif op=={O('VARARG')} then "
        f"local nret=b "
        f"if nret==255 then for jj=1,#va do setreg(a+jj-1,va[jj]) end "
        f"elseif nret==1 then setreg(a,va[1]) end "
        f"elseif op=={O('CLOSURE')} then "
        f"local cp={protos_v}[b+1] "
        f"local child_ubox={{}} "
        f"for _ui=1,#cp.updescs do "
        f"local ud=cp.updescs[_ui] "
        f"if ud.kind==0 then child_ubox[_ui-1]=boxreg(ud.idx) "
        f"else child_ubox[_ui-1]={ubox_v}[ud.idx] end "
        f"end "
        f"setreg(a,function(...) return {exec_v}(cp,child_ubox,...) end) "
        f"elseif op=={O('FOR_PREP')} then "
        f"local iv=getreg(a) local lim=getreg(a+1) local st=getreg(a+2) "
        f"if not((st>0 and iv<=lim) or (st<0 and iv>=lim)) then pc=b+1 "
        f"else setreg(a+3,iv) end "
        f"elseif op=={O('FOR_LOOP')} then "
        f"local iv=getreg(a+3)+getreg(a+2) "
        f"local lim=getreg(a+1) local st=getreg(a+2) "
        f"if (st>0 and iv<=lim) or (st<0 and iv>=lim) then setreg(a+3,iv) pc=b+1 end "
        f"elseif op=={O('TFOR_CALL')} then "
        f"local itf=getreg(a) local stt=getreg(a+1) local ctl=getreg(a+2) "
        f"local res=table.pack(itf(stt,ctl)) "
        f"for jj=1,c do setreg(a+2+jj,res[jj]) end "
        f"setreg(a+2,res[1]) "
        f"elseif op=={O('TFOR_LOOP')} then "
        f"if getreg(a)==nil then pc=b+1 end "
        f"elseif op=={O('CLOSE_UPVAL')} then "
        f"local x=rb[a] if x~=nil then vr[a]=x.v rb[a]=nil end "
        f"elseif op=={O('MOVE')} then setreg(a,getreg(b)) "
        f"end "
        f"end "
        f"end "

        f"local {fn_v} "
        f"do local {i_v},{j_v}={ldp_v}({data_v},1) {fn_v}=function(...) return {exec_v}({i_v},{{}},...) end end "
        f"return {fn_v}(...) "
    )
    return lua
