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

    def serialize(self):
        data = bytes([int(self.is_vararg), self.params, len(self.upvals)])
        data += struct.pack('<H', len(self.upvals))
        for reg in self.upvals:
            data += struct.pack('<H', reg)
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
    def __init__(self, parent=None):
        self.parent = parent
        self.locals = {}
        self.reg_counter = parent.reg_counter if parent else [0]
        self.upval_refs = []

    def alloc(self, name):
        reg = self.reg_counter[0]
        self.reg_counter[0] += 1
        self.locals[name] = reg
        return reg

    def free_to(self, reg):
        self.reg_counter[0] = reg

    def resolve(self, name):
        if name in self.locals:
            return ('local', self.locals[name])
        if self.parent:
            return self.parent.resolve(name)
        return None

class Compiler:
    def __init__(self, parent=None):
        self.proto = FuncProto()
        self.scope = Scope()
        self.parent = parent
        self.break_patches = []
        self.continue_patches = []

    def child(self):
        c = Compiler(parent=self)
        return c

    def push_scope(self):
        self.scope = Scope(self.scope)
        return self.scope.reg_counter[0]

    def pop_scope(self, saved_reg):
        self.scope = self.scope.parent
        self.scope.reg_counter[0] = saved_reg

    def resolve(self, name):
        r = self.scope.resolve(name)
        if r is not None:
            return r
        if self.parent:
            pr = self.parent.resolve(name)
            if pr and pr[0] in ('local', 'upval'):
                return ('upval', pr[1])
            return pr
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
                idx = self._upval_idx(r[1])
                self.emit(OP_LOAD_UPVAL, dst, idx)
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

    def _upval_idx(self, reg):
        if reg not in self.proto.upvals:
            self.proto.upvals.append(reg)
        return self.proto.upvals.index(reg)

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
            }
            self.emit(op_map[op], dst, left_r, right_r)

        self.scope.reg_counter[0] = tmp

    def _unop(self, node, dst):
        tmp = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['operand'], tmp)
        op_map = {'-': OP_UNM, 'not': OP_NOT, '#': OP_LEN}
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
            fn = node['fn']
            tmp = self.scope.reg_counter[0]
            self.scope.reg_counter[0] = base_r + 1
            self._expr(fn, base_r)
            args = node['args']
            for i, a in enumerate(args):
                ar = base_r + 1 + i
                self.scope.reg_counter[0] = ar + 1
                self._expr(a, ar)
            self.emit(OP_CALL, base_r, len(args), 255)
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
        for i, a in enumerate(args):
            ar = base + 1 + i
            self.scope.reg_counter[0] = ar + 1
            self._expr(a, ar)
        self.emit(OP_CALL_METHOD, obj_r, self.K(node['method']), len(args))
        if dst != obj_r:
            self.emit(OP_MOVE, dst, obj_r)
        self.scope.reg_counter[0] = base

    def _method_call_multiret(self, node, base_r):
        self.scope.reg_counter[0] = base_r + 1
        self._expr(node['obj'], base_r)
        args = node['args']
        for i, a in enumerate(args):
            ar = base_r + 1 + i
            self.scope.reg_counter[0] = ar + 1
            self._expr(a, ar)
        self.emit(OP_CALL_METHOD, base_r, self.K(node['method']), len(args))

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
        saved = child.push_scope()
        for p in node['params']:
            child.scope.alloc(p)
        if node.get('is_vararg'):
            pass
        child._stmts(node['body'])
        if not child.proto.instructions or child.proto.instructions[-1].op not in (OP_RETURN, OP_RETURN_NONE):
            child.emit(OP_RETURN_NONE, 0)
        child.pop_scope(saved)
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
            saved = self.scope.reg_counter[0]
            for i, name in enumerate(names):
                reg = self.scope.reg_counter[0]
                self.scope.reg_counter[0] += 1
                regs.append(reg)
                self.scope.locals[name] = reg
            for i, name in enumerate(names):
                reg = regs[i]
                if i < len(exprs):
                    e = exprs[i]
                    if i == len(names) - 1 and e.get('type') in ('call', 'method_call', 'vararg'):
                        self._call_multiret(e, reg)
                    else:
                        self._expr(e, reg)
                else:
                    self.emit(OP_LOAD_CONST, reg, self.K(None))

        elif t == 'assign':
            targets = node['targets']
            values = node['values']
            tmp_base = self.scope.reg_counter[0]
            tmps = []
            for i, v in enumerate(values):
                tr = tmp_base + i
                self.scope.reg_counter[0] = tr + 1
                if i == len(values) - 1 and v.get('type') in ('call', 'method_call', 'vararg'):
                    self._call_multiret(v, tr)
                else:
                    self._expr(v, tr)
                tmps.append(tr)

            for i, tgt in enumerate(targets):
                src = tmps[i] if i < len(tmps) else None
                val_r = tmp_base + len(values) + i
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
                        idx = self._upval_idx(r[1])
                        self.emit(OP_SET_UPVAL, idx, val_r)
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
            for i, e in enumerate(exprs):
                r = base + i
                self.scope.reg_counter[0] = r + 1
                if i == len(exprs) - 1 and e.get('type') in ('call', 'method_call', 'vararg'):
                    self._call_multiret(e, r)
                else:
                    self._expr(e, r)
            self.emit(OP_RETURN, base, len(exprs))
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
                elif len(node['target']) > 1:
                    obj_r = self.scope.reg_counter[0]
                    self.scope.reg_counter[0] += 1
                    r = self.resolve(node['target'][0])
                    if r and r[0] == 'local':
                        self.emit(OP_MOVE, obj_r, r[1])
                    else:
                        self.emit(OP_LOAD_GLOBAL, obj_r, self.K(node['target'][0]))
                    for part in node['target'][1:-1]:
                        self.emit(OP_GET_FIELD, obj_r, obj_r, self.K(part))
                    self.emit(OP_SET_FIELD, obj_r, self.K(node['target'][-1]), tmp)
                    self.scope.reg_counter[0] = tmp
                self.scope.reg_counter[0] = tmp

        elif t == 'local_function':
            reg = self.scope.alloc(node['name'])
            fn_node = {'type': 'function', 'params': node['params'],
                       'body': node['body'], 'is_vararg': node.get('is_vararg', False)}
            self._function_expr(fn_node, reg)

        elif t == 'break':
            j = self.emit(OP_JUMP, 0)
            self.break_patches.append(j)

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
        self.break_patches = []
        saved = self.push_scope()
        self._stmts(node['body'])
        self.pop_scope(saved)
        self.emit(OP_JUMP, loop_start)
        self.patch(jf, b=self.pc())
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks

    def _repeat(self, node):
        loop_start = self.pc()
        old_breaks = self.break_patches
        self.break_patches = []
        saved = self.push_scope()
        self._stmts(node['body'])
        cond_r = self.scope.reg_counter[0]
        self.scope.reg_counter[0] += 1
        self._expr(node['cond'], cond_r)
        self.scope.reg_counter[0] = cond_r
        self.emit(OP_JUMP_FALSE, cond_r, loop_start)
        self.pop_scope(saved)
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks

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
        self.break_patches = []
        self._stmts(node['body'])
        self.pop_scope(saved_reg + 4)
        fl = self.emit(OP_FOR_LOOP, init_r, 0)
        self.patch(fp, b=self.pc())
        self.patch(fl, b=loop_start)
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.scope.reg_counter[0] = saved_reg

    def _generic_for(self, node):
        saved_reg = self.scope.reg_counter[0]
        iter_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        state_r = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        ctrl_r  = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
        exprs = node['iters']
        last_idx = len(exprs) - 1
        slots = [iter_r, state_r, ctrl_r]
        for i in range(3):
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
        loop_start = self.pc()
        var_regs = []
        for vn in node['vars']:
            vr = self.scope.reg_counter[0]; self.scope.reg_counter[0] += 1
            var_regs.append(vr)
        tf = self.emit(OP_TFOR_CALL, iter_r, len(node['vars']))
        jf = self.emit(OP_TFOR_LOOP, var_regs[0] if var_regs else ctrl_r, 0)
        self.push_scope()
        for vn, vr in zip(node['vars'], var_regs):
            self.scope.locals[vn] = vr
        old_breaks = self.break_patches
        self.break_patches = []
        self._stmts(node['body'])
        self.pop_scope(saved_reg + 3 + len(node['vars']))
        self.emit(OP_JUMP, loop_start)
        self.patch(jf, b=self.pc())
        for bp in self.break_patches:
            self.patch(bp, a=self.pc())
        self.break_patches = old_breaks
        self.scope.reg_counter[0] = saved_reg

    def compile_chunk(self, stmts, is_vararg=True):
        self.proto.is_vararg = is_vararg
        self._stmts(stmts)
        if not self.proto.instructions or self.proto.instructions[-1].op not in (OP_RETURN, OP_RETURN_NONE):
            self.emit(OP_RETURN_NONE, 0)

    def serialize(self):
        return self.proto.serialize()


KEYWORDS = {
    'and','break','do','else','elseif','end','false','for','function',
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
        if two in ('==','~=','<=','>=','..','//'):
            tokens.append(('OP', two))
            i += 2
            continue
        if src[i] in '+-*/%^<>=.':
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
        left = self.parse_concat()
        while self.check('OP') and self.peek()[1] in ('<','<=','>','>=','==','~='):
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


def try_compile_vm(source):
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
    except Exception:
        return None

def _patch_global_ops(opmap):
    g = globals()
    for name, val in opmap.items():
        g['OP_' + name] = val


def bytecode_to_lua(bytecode, rng, gen_name_fn, opmap=None):
    data = list(bytecode)
    encoded = ','.join(str(b) for b in data)

    N = gen_name_fn
    data_v    = N(); pc_v      = N(); stack_v   = N(); sp_v      = N()
    vars_v    = N(); op_v      = N(); a_v       = N(); b_v       = N()
    c_v       = N(); ins_v     = N(); rd_v      = N(); res_v     = N()
    upvals_v  = N(); u16_v     = N(); u16s_v    = N(); ldc_v     = N()
    ldi_v     = N(); ldp_v     = N(); exec_v    = N(); consts_v  = N()
    ci_v      = N(); protos_v  = N(); frame_v   = N(); frames_v  = N()
    env_v     = N(); genv_v    = N(); mk_v      = N(); fn_v      = N()
    args_v    = N(); r_v       = N(); i_v       = N(); j_v       = N()
    t_v       = N(); s_v       = N(); k_v       = N(); v_v       = N()
    iter_v    = N(); state_v   = N(); ctrl_v    = N(); tmp_v     = N()
    ok_v      = N(); err_v     = N(); retbase_v = N(); nret_v    = N()
    obj_v     = N(); mfn_v     = N(); vararg_v  = N(); nargs_v   = N()
    ubox_v    = N(); upidx_v   = N()

    om = opmap if opmap is not None else _DEFAULT_OPMAP
    def O(name): return om[name]

    AB2  = f"a={u16_v}(d,i) i=i+2 b={u16_v}(d,i) i=i+2 "
    AB2C = f"a={u16_v}(d,i) i=i+2 b={u16_v}(d,i) i=i+2 cc={u16_v}(d,i) i=i+2 "
    A2   = f"a={u16_v}(d,i) i=i+2 "

    def ldi_cases():
        groups_ab2 = [
            ('LOAD_CONST','LOAD_VAR','SET_VAR','LOAD_GLOBAL','SET_GLOBAL','CLOSURE','CLOSE_UPVAL'),
            ('LOAD_UPVAL','SET_UPVAL'),
            ('RETURN','VARARG'),
            ('JUMP_FALSE','JUMP_TRUE','JUMP_FALSE_NK','JUMP_TRUE_NK'),
            ('UNM','LEN','NOT'),
            ('FOR_PREP','FOR_LOOP','TFOR_CALL','TFOR_LOOP'),
            ('DUP','MOVE'),
        ]
        groups_ab2c = [
            ('GET_TABLE','SET_TABLE','SET_LIST'),
            ('SET_LIST_MULTI',),
            ('GET_FIELD','SET_FIELD'),
            ('ADD','SUB','MUL','DIV','MOD','POW','CONCAT','IDIV','AND','OR'),
            ('EQ','NE','LT','LE','GT','GE'),
            ('CALL','CALL_METHOD'),
        ]
        groups_a2 = [('NEW_TABLE',), ('RETURN_NONE',), ('POP',), ('JUMP',)]

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

    lua = (
        f"local {data_v}={{{encoded}}} "
        f"local function {u16_v}(d,i) return d[i]+(d[i+1]*256) end "
        f"local function {u16s_v}(d,i) local v=d[i]+(d[i+1]*256) if v>=32768 then v=v-65536 end return v end "
        f"local function {ldc_v}(d,i) "
        f"local t=d[i] i=i+1 "
        f"if t==0 then return nil,i "
        f"elseif t==1 then return d[i]==1,i+1 "
        f"elseif t==2 then "
        f"local bytes={{}} for j=0,7 do bytes[j+1]=d[i+j] end i=i+8 "
        f"local n=0 local sign=bytes[8]>=128 and 1 or 0 "
        f"local exp=((bytes[8]%128)*16)+math.floor(bytes[7]/16) "
        f"local mant=bytes[7]%16 "
        f"for j=6,1,-1 do mant=mant*256+bytes[j] end "
        f"if exp==2047 then return sign==1 and -math.huge or math.huge,i end "
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
        f"local is_vararg=d[i]==1 local params=d[i+1] local nupvals_hdr=d[i+2] i=i+3 "
        f"local nuregs={u16_v}(d,i) i=i+2 "
        f"local upval_regs={{}} "
        f"for _=1,nuregs do upval_regs[_]={u16_v}(d,i) i=i+2 end "
        f"local nprotos={u16_v}(d,i) i=i+2 "
        f"local protos={{}} "
        f"for _=1,nprotos do "
        f"local sz=d[i]+(d[i+1]*256)+(d[i+2]*65536)+(d[i+3]*16777216) i=i+4 "
        f"local p,ni={ldp_v}(d,i) i=ni "
        f"protos[#protos+1]=p "
        f"end "
        f"local nconsts={u16_v}(d,i) i=i+2 "
        f"local consts={{}} "
        f"for _=1,nconsts do local cv,ni={ldc_v}(d,i) consts[#consts+1]=cv i=ni end "
        f"local nins={u16_v}(d,i) i=i+2 "
        f"local ins={{}} "
        f"for _=1,nins do local iv,ni={ldi_v}(d,i) ins[#ins+1]=iv i=ni end "
        f"return {{is_vararg=is_vararg,params=params,nupvals=nuregs,upval_regs=upval_regs,protos=protos,consts=consts,ins=ins}},i end "
        f"local {genv_v}=(getfenv and getfenv(0)) or _ENV or _G or {{}} "

        f"local function {mk_v}(proto,parent_vars,upval_regs_in) "
        f"return function(...) "
        f"local {vars_v}={{}} "
        f"local {ubox_v}={{}} "
        f"local {vararg_v}={{...}} "
        f"local {args_v}={{...}} "
        f"for {i_v}=1,proto.params do {vars_v}[{i_v}-1]={args_v}[{i_v}] end "
        f"if upval_regs_in and parent_vars then "
        f"for {upidx_v}=1,#upval_regs_in do "
        f"local _ur=upval_regs_in[{upidx_v}] "
        f"if {ubox_v}[_ur]==nil then {ubox_v}[_ur]={{v=parent_vars[_ur]}} end "
        f"end "
        f"end "
        f"local {consts_v}=proto.consts "
        f"local {ins_v}=proto.ins "
        f"local {protos_v}=proto.protos "
        f"local {pc_v}=1 "
        f"while {pc_v}<=#{ ins_v} do "
        f"local {rd_v}={ins_v}[{pc_v}] "
        f"local {op_v}={rd_v}[1] "
        f"local {a_v}={rd_v}[2] "
        f"local {b_v}={rd_v}[3] "
        f"local {c_v}={rd_v}[4] "
        f"{pc_v}={pc_v}+1 "
        f"if {op_v}=={O('LOAD_CONST')} then {vars_v}[{a_v}]={consts_v}[{b_v}+1] "
        f"elseif {op_v}=={O('LOAD_VAR')} then {vars_v}[{a_v}]={vars_v}[{b_v}] "
        f"elseif {op_v}=={O('SET_VAR')} then {vars_v}[{b_v}]={vars_v}[{a_v}] "
        f"elseif {op_v}=={O('LOAD_GLOBAL')} then local {k_v}={consts_v}[{b_v}+1] {vars_v}[{a_v}]={genv_v}[{k_v}] "
        f"elseif {op_v}=={O('SET_GLOBAL')} then local {k_v}={consts_v}[{a_v}+1] {genv_v}[{k_v}]={vars_v}[{b_v}] "

        f"elseif {op_v}=={O('LOAD_UPVAL')} then "
        f"local _ub={ubox_v}[{b_v}] "
        f"if _ub then {vars_v}[{a_v}]=_ub.v else {vars_v}[{a_v}]=nil end "

        f"elseif {op_v}=={O('SET_UPVAL')} then "
        f"if {ubox_v}[{a_v}] then {ubox_v}[{a_v}].v={vars_v}[{b_v}] end "
        f"{vars_v}[{a_v}]={vars_v}[{b_v}] "

        f"elseif {op_v}=={O('GET_TABLE')} then {vars_v}[{a_v}]={vars_v}[{b_v}][{vars_v}[{c_v}]] "
        f"elseif {op_v}=={O('SET_TABLE')} then {vars_v}[{a_v}][{vars_v}[{b_v}]]={vars_v}[{c_v}] "
        f"elseif {op_v}=={O('NEW_TABLE')} then {vars_v}[{a_v}]={{}} "
        f"elseif {op_v}=={O('SET_LIST')} then {vars_v}[{a_v}][{consts_v}[{b_v}+1]]={vars_v}[{c_v}] "
        f"elseif {op_v}=={O('SET_LIST_MULTI')} then "
        f"local {j_v}={b_v} local {i_v}={consts_v}[{c_v}+1] "
        f"while {vars_v}[{j_v}]~=nil do {vars_v}[{a_v}][{i_v}]={vars_v}[{j_v}] {i_v}={i_v}+1 {j_v}={j_v}+1 end "
        f"elseif {op_v}=={O('GET_FIELD')} then {vars_v}[{a_v}]={vars_v}[{b_v}][{consts_v}[{c_v}+1]] "
        f"elseif {op_v}=={O('SET_FIELD')} then {vars_v}[{a_v}][{consts_v}[{b_v}+1]]={vars_v}[{c_v}] "
        f"elseif {op_v}=={O('ADD')} then {vars_v}[{a_v}]={vars_v}[{b_v}]+{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('SUB')} then {vars_v}[{a_v}]={vars_v}[{b_v}]-{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('MUL')} then {vars_v}[{a_v}]={vars_v}[{b_v}]*{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('DIV')} then {vars_v}[{a_v}]={vars_v}[{b_v}]/{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('MOD')} then {vars_v}[{a_v}]={vars_v}[{b_v}]%{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('POW')} then {vars_v}[{a_v}]={vars_v}[{b_v}]^{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('CONCAT')} then {vars_v}[{a_v}]={vars_v}[{b_v}]..{vars_v}[{c_v}] "
        f"elseif {op_v}=={O('IDIV')} then {vars_v}[{a_v}]=math.floor({vars_v}[{b_v}]/{vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('UNM')} then {vars_v}[{a_v}]=-{vars_v}[{b_v}] "
        f"elseif {op_v}=={O('LEN')} then {vars_v}[{a_v}]=#{vars_v}[{b_v}] "
        f"elseif {op_v}=={O('NOT')} then {vars_v}[{a_v}]=not {vars_v}[{b_v}] "
        f"elseif {op_v}=={O('AND')} then "
        f"if not {vars_v}[{b_v}] then {vars_v}[{a_v}]={vars_v}[{b_v}] else {vars_v}[{a_v}]={vars_v}[{c_v}] end "
        f"elseif {op_v}=={O('OR')} then "
        f"if {vars_v}[{b_v}] then {vars_v}[{a_v}]={vars_v}[{b_v}] else {vars_v}[{a_v}]={vars_v}[{c_v}] end "
        f"elseif {op_v}=={O('EQ')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]=={vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('NE')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]~={vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('LT')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]<{vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('LE')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]<={vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('GT')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]>{vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('GE')} then {vars_v}[{a_v}]=({vars_v}[{b_v}]>={vars_v}[{c_v}]) "
        f"elseif {op_v}=={O('JUMP')} then {pc_v}={a_v}+1 "
        f"elseif {op_v}=={O('JUMP_FALSE')} then if not {vars_v}[{a_v}] then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('JUMP_TRUE')} then if {vars_v}[{a_v}] then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('JUMP_FALSE_NK')} then if not {vars_v}[{a_v}] then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('JUMP_TRUE_NK')} then if {vars_v}[{a_v}] then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('CALL')} then "
        f"local {fn_v}={vars_v}[{a_v}] local {nargs_v}={b_v} local {nret_v}={c_v} "
        f"local {args_v}={{}} "
        f"if {nargs_v}==255 then local {j_v}={a_v}+1 while {vars_v}[{j_v}]~=nil do {args_v}[#{args_v}+1]={vars_v}[{j_v}] {j_v}={j_v}+1 end "
        f"else for {j_v}=1,{nargs_v} do {args_v}[{j_v}]={vars_v}[{a_v}+{j_v}] end end "
        f"if type({fn_v})=='function' then "
        f"local {res_v}=table.pack({fn_v}(table.unpack({args_v}))) "
        f"if {nret_v}==255 then "
        f"local {j_v}=1 while {j_v}<={res_v}.n or {vars_v}[{a_v}+{j_v}-1]~=nil do "
        f"{vars_v}[{a_v}+{j_v}-1]={res_v}[{j_v}] {j_v}={j_v}+1 end "
        f"elseif {nret_v}>0 then {vars_v}[{a_v}]={res_v}[1] end end "
        f"elseif {op_v}=={O('CALL_METHOD')} then "
        f"local {obj_v}={vars_v}[{a_v}] local {k_v}={consts_v}[{b_v}+1] local {nargs_v}={c_v} "
        f"local {mfn_v}={obj_v}[{k_v}] "
        f"local {args_v}={{{obj_v}}} "
        f"for {j_v}=1,{nargs_v} do {args_v}[#{args_v}+1]={vars_v}[{a_v}+{j_v}] end "
        f"if type({mfn_v})=='function' then "
        f"local {res_v}=table.pack({mfn_v}(table.unpack({args_v}))) "
        f"if {res_v}.n>=1 then {vars_v}[{a_v}]={res_v}[1] end end "
        f"elseif {op_v}=={O('RETURN')} then "
        f"local {retbase_v}={a_v} local {nret_v}={b_v} "
        f"if {nret_v}==1 then return {vars_v}[{retbase_v}] "
        f"elseif {nret_v}==0 then return "
        f"else local {res_v}={{}} for {j_v}=0,{nret_v}-1 do {res_v}[{j_v}+1]={vars_v}[{retbase_v}+{j_v}] end return table.unpack({res_v}) end "
        f"elseif {op_v}=={O('RETURN_NONE')} then return "
        f"elseif {op_v}=={O('VARARG')} then "
        f"local {nret_v}={b_v} "
        f"if {nret_v}==255 then for {j_v}=1,#{vararg_v} do {vars_v}[{a_v}+{j_v}-1]={vararg_v}[{j_v}] end "
        f"elseif {nret_v}==1 then {vars_v}[{a_v}]={vararg_v}[1] end "

        f"elseif {op_v}=={O('CLOSURE')} then "
        f"local _cp={protos_v}[{b_v}+1] "
        f"local _cur_vars={vars_v} "
        f"local _cur_ubox={ubox_v} "
        f"local _child_uregs=_cp.upval_regs "
        f"if _child_uregs and #_child_uregs>0 then "
        f"for _ui=1,#_child_uregs do "
        f"local _ur=_child_uregs[_ui] "
        f"if _cur_ubox[_ur]==nil then "
        f"_cur_ubox[_ur]={{v=_cur_vars[_ur]}} "
        f"end "
        f"end "
        f"end "
        f"local _child_ubox={{}} "
        f"if _child_uregs then "
        f"for _ui=1,#_child_uregs do "
        f"local _ur=_child_uregs[_ui] "
        f"_child_ubox[_ur]=_cur_ubox[_ur] "
        f"end "
        f"end "
        f"local _mk2={mk_v} "
        f"{vars_v}[{a_v}]=function(...) "
        f"local _cv={{}} "
        f"local _ca={{...}} "
        f"for _pi=1,_cp.params do _cv[_pi-1]=_ca[_pi] end "
        f"local _ubox2=_child_ubox "
        f"local _cst=_cp.consts local _ins=_cp.ins local _prt=_cp.protos "
        f"local _pc=1 local _varg={{...}} "
        f"while _pc<=#_ins do "
        f"local _rd=_ins[_pc] local _op=_rd[1] local _a=_rd[2] local _b=_rd[3] local _c=_rd[4] _pc=_pc+1 "
        f"if _op=={O('LOAD_CONST')} then _cv[_a]=_cst[_b+1] "
        f"elseif _op=={O('LOAD_VAR')} then _cv[_a]=_cv[_b] "
        f"elseif _op=={O('SET_VAR')} then _cv[_b]=_cv[_a] "
        f"elseif _op=={O('LOAD_GLOBAL')} then _cv[_a]={genv_v}[_cst[_b+1]] "
        f"elseif _op=={O('SET_GLOBAL')} then {genv_v}[_cst[_a+1]]=_cv[_b] "
        f"elseif _op=={O('LOAD_UPVAL')} then local _ub=_ubox2[_b] if _ub then _cv[_a]=_ub.v else _cv[_a]=nil end "
        f"elseif _op=={O('SET_UPVAL')} then if _ubox2[_a] then _ubox2[_a].v=_cv[_b] end _cv[_a]=_cv[_b] "
        f"elseif _op=={O('GET_TABLE')} then _cv[_a]=_cv[_b][_cv[_c]] "
        f"elseif _op=={O('SET_TABLE')} then _cv[_a][_cv[_b]]=_cv[_c] "
        f"elseif _op=={O('NEW_TABLE')} then _cv[_a]={{}} "
        f"elseif _op=={O('SET_LIST')} then _cv[_a][_cst[_b+1]]=_cv[_c] "
        f"elseif _op=={O('SET_LIST_MULTI')} then "
        f"local _ji=_b local _ii=_cst[_c+1] "
        f"while _cv[_ji]~=nil do _cv[_a][_ii]=_cv[_ji] _ii=_ii+1 _ji=_ji+1 end "
        f"elseif _op=={O('GET_FIELD')} then _cv[_a]=_cv[_b][_cst[_c+1]] "
        f"elseif _op=={O('SET_FIELD')} then _cv[_a][_cst[_b+1]]=_cv[_c] "
        f"elseif _op=={O('ADD')} then _cv[_a]=_cv[_b]+_cv[_c] "
        f"elseif _op=={O('SUB')} then _cv[_a]=_cv[_b]-_cv[_c] "
        f"elseif _op=={O('MUL')} then _cv[_a]=_cv[_b]*_cv[_c] "
        f"elseif _op=={O('DIV')} then _cv[_a]=_cv[_b]/_cv[_c] "
        f"elseif _op=={O('MOD')} then _cv[_a]=_cv[_b]%_cv[_c] "
        f"elseif _op=={O('POW')} then _cv[_a]=_cv[_b]^_cv[_c] "
        f"elseif _op=={O('CONCAT')} then _cv[_a]=_cv[_b].._cv[_c] "
        f"elseif _op=={O('IDIV')} then _cv[_a]=math.floor(_cv[_b]/_cv[_c]) "
        f"elseif _op=={O('UNM')} then _cv[_a]=-_cv[_b] "
        f"elseif _op=={O('LEN')} then _cv[_a]=#_cv[_b] "
        f"elseif _op=={O('NOT')} then _cv[_a]=not _cv[_b] "
        f"elseif _op=={O('AND')} then if not _cv[_b] then _cv[_a]=_cv[_b] else _cv[_a]=_cv[_c] end "
        f"elseif _op=={O('OR')} then if _cv[_b] then _cv[_a]=_cv[_b] else _cv[_a]=_cv[_c] end "
        f"elseif _op=={O('EQ')} then _cv[_a]=(_cv[_b]==_cv[_c]) "
        f"elseif _op=={O('NE')} then _cv[_a]=(_cv[_b]~=_cv[_c]) "
        f"elseif _op=={O('LT')} then _cv[_a]=(_cv[_b]<_cv[_c]) "
        f"elseif _op=={O('LE')} then _cv[_a]=(_cv[_b]<=_cv[_c]) "
        f"elseif _op=={O('GT')} then _cv[_a]=(_cv[_b]>_cv[_c]) "
        f"elseif _op=={O('GE')} then _cv[_a]=(_cv[_b]>=_cv[_c]) "
        f"elseif _op=={O('JUMP')} then _pc=_a+1 "
        f"elseif _op=={O('JUMP_FALSE')} then if not _cv[_a] then _pc=_b+1 end "
        f"elseif _op=={O('JUMP_TRUE')} then if _cv[_a] then _pc=_b+1 end "
        f"elseif _op=={O('JUMP_FALSE_NK')} then if not _cv[_a] then _pc=_b+1 end "
        f"elseif _op=={O('JUMP_TRUE_NK')} then if _cv[_a] then _pc=_b+1 end "
        f"elseif _op=={O('CALL')} then "
        f"local _fn=_cv[_a] local _na=_b local _nr=_c local _as={{}} "
        f"if _na==255 then local _ji=_a+1 while _cv[_ji]~=nil do _as[#_as+1]=_cv[_ji] _ji=_ji+1 end "
        f"else for _ji=1,_na do _as[_ji]=_cv[_a+_ji] end end "
        f"if type(_fn)=='function' then local _rs=table.pack(_fn(table.unpack(_as))) "
        f"if _nr==255 then "
        f"local _ji=1 while _ji<=_rs.n or _cv[_a+_ji-1]~=nil do "
        f"_cv[_a+_ji-1]=_rs[_ji] _ji=_ji+1 end "
        f"elseif _nr>0 then _cv[_a]=_rs[1] end end "
        f"elseif _op=={O('CALL_METHOD')} then "
        f"local _ob=_cv[_a] local _mk=_cst[_b+1] local _na=_c local _mf=_ob[_mk] "
        f"local _as={{_ob}} for _ji=1,_na do _as[#_as+1]=_cv[_a+_ji] end "
        f"if type(_mf)=='function' then local _rs=table.pack(_mf(table.unpack(_as))) "
        f"if _rs.n>=1 then _cv[_a]=_rs[1] end end "
        f"elseif _op=={O('RETURN')} then "
        f"local _rb=_a local _nr=_b "
        f"if _nr==1 then return _cv[_rb] "
        f"elseif _nr==0 then return "
        f"else local _rs={{}} for _ji=0,_nr-1 do _rs[_ji+1]=_cv[_rb+_ji] end return table.unpack(_rs) end "
        f"elseif _op=={O('RETURN_NONE')} then return "
        f"elseif _op=={O('VARARG')} then "
        f"if _b==255 then for _ji=1,#_varg do _cv[_a+_ji-1]=_varg[_ji] end "
        f"elseif _b==1 then _cv[_a]=_varg[1] end "
        f"elseif _op=={O('CLOSURE')} then "
        f"local _cp2=_prt[_b+1] local _cv2=_cv local _ub2=_ubox2 "
        f"local _ur2=_cp2.upval_regs "
        f"if _ur2 and #_ur2>0 then for _ui=1,#_ur2 do local _ur=_ur2[_ui] "
        f"if _ub2[_ur]==nil then _ub2[_ur]={{v=_cv2[_ur]}} end end end "
        f"local _cub2={{}} if _ur2 then for _ui=1,#_ur2 do local _ur=_ur2[_ui] _cub2[_ur]=_ub2[_ur] end end "
        f"_cv[_a]={mk_v}(_cp2,_cv2,_ur2) "
        f"elseif _op=={O('FOR_PREP')} then "
        f"_cv[_a]=_cv[_a]-_cv[_a+2] if not((_cv[_a+2]>0 and (_cv[_a]+_cv[_a+2])<=_cv[_a+1]) or (_cv[_a+2]<0 and (_cv[_a]+_cv[_a+2])>=_cv[_a+1])) then _pc=_b+1 end "
        f"elseif _op=={O('FOR_LOOP')} then "
        f"_cv[_a]=_cv[_a]+_cv[_a+2] "
        f"if (_cv[_a+2]>0 and _cv[_a]<=_cv[_a+1]) or (_cv[_a+2]<0 and _cv[_a]>=_cv[_a+1]) then _cv[_a+3]=_cv[_a] _pc=_b+1 end "
        f"elseif _op=={O('TFOR_CALL')} then "
        f"local _it=_cv[_a] local _st=_cv[_a+1] local _ct=_cv[_a+2] "
        f"local _rs=table.pack(_it(_st,_ct)) "
        f"if _rs[1]==nil then _pc=_b+1 "
        f"else for _ji=1,_rs.n do _cv[_a+2+_ji]=_rs[_ji] end _cv[_a+2]=_rs[1] end "
        f"elseif _op=={O('TFOR_LOOP')} then if _cv[_a]==nil then _pc=_b+1 end "
        f"elseif _op=={O('MOVE')} then _cv[_a]=_cv[_b] "
        f"end end end "

        f"elseif {op_v}=={O('FOR_PREP')} then "
        f"{vars_v}[{a_v}]={vars_v}[{a_v}]-{vars_v}[{a_v}+2] if not(({vars_v}[{a_v}+2]>0 and ({vars_v}[{a_v}]+{vars_v}[{a_v}+2])<={vars_v}[{a_v}+1]) or ({vars_v}[{a_v}+2]<0 and ({vars_v}[{a_v}]+{vars_v}[{a_v}+2])>={vars_v}[{a_v}+1])) then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('FOR_LOOP')} then "
        f"{vars_v}[{a_v}]={vars_v}[{a_v}]+{vars_v}[{a_v}+2] "
        f"if ({vars_v}[{a_v}+2]>0 and {vars_v}[{a_v}]<={vars_v}[{a_v}+1]) or ({vars_v}[{a_v}+2]<0 and {vars_v}[{a_v}]>={vars_v}[{a_v}+1]) then {vars_v}[{a_v}+3]={vars_v}[{a_v}] {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('TFOR_CALL')} then "
        f"local {iter_v}={vars_v}[{a_v}] local {state_v}={vars_v}[{a_v}+1] local {ctrl_v}={vars_v}[{a_v}+2] "
        f"local {res_v}=table.pack({iter_v}({state_v},{ctrl_v})) "
        f"if {res_v}[1]==nil then {pc_v}={b_v}+1 "
        f"else for {j_v}=1,{res_v}.n do {vars_v}[{a_v}+2+{j_v}]={res_v}[{j_v}] end {vars_v}[{a_v}+2]={res_v}[1] end "
        f"elseif {op_v}=={O('TFOR_LOOP')} then "
        f"if {vars_v}[{a_v}]==nil then {pc_v}={b_v}+1 end "
        f"elseif {op_v}=={O('MOVE')} then {vars_v}[{a_v}]={vars_v}[{b_v}] "
        f"end end end end "
        f"local {fn_v} "
        f"do local {tmp_v},{ci_v}={ldp_v}({data_v},1) {fn_v}={mk_v}({tmp_v},nil,nil) end "
        f"return {fn_v}(...) "
    )
    return lua
