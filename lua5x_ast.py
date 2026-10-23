def _normalize_ver(ver):
    if isinstance(ver, tuple):
        return ver
    if isinstance(ver, str):
        v = ver.lower()
        if v.startswith("lua"):
            v = v[3:]
        parts = v.split(".")
        if len(parts) >= 2:
            return (int(parts[0]), int(parts[1]))
        if len(parts) == 1 and parts[0].isdigit():
            if len(parts[0]) == 2:
                return (int(parts[0][0]), int(parts[0][1]))
            return (int(parts[0]), 0)
    return (5, 1)

BASE_KEYWORDS = {
    'and', 'break', 'do', 'else', 'elseif', 'end', 'false',
    'for', 'function', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat',
    'return', 'then', 'true', 'until', 'while',
}

BLOCK_END_KW = {'end', 'else', 'elseif', 'until'}

class Lua5xSyntaxError(Exception):
    pass

class Token:
    __slots__ = ('kind', 'value', 'raw')

    def __init__(self, kind, value, raw=None):
        self.kind = kind
        self.value = value
        self.raw = raw if raw is not None else value

    def __repr__(self):
        return f"Token({self.kind!r},{self.value!r})"

def tokenize(src, version="5.1"):
    ver = _normalize_ver(version)
    tokens = []
    i = 0
    n = len(src)

    def emit(kind, value, raw=None):
        tokens.append(Token(kind, value, raw))

    kw_set = set(BASE_KEYWORDS)
    if ver >= (5, 2):
        kw_set.add('goto')

    while i < n:
        c = src[i]

        if c in ' \t\r\n':
            i += 1
            continue

        if c == '-' and i + 1 < n and src[i+1] == '-':
            if i + 3 < n and src[i+2] == '[' and src[i+3] in ('[', '='):
                j = i + 2
                eqs = 0
                k = j + 1
                while k < n and src[k] == '=':
                    eqs += 1
                    k += 1
                if k < n and src[k] == '[':
                    close = ']' + ('=' * eqs) + ']'
                    pos = src.find(close, k + 1)
                    if pos == -1:
                        raise Lua5xSyntaxError("unfinished long comment")
                    i = pos + len(close)
                    continue
            while i < n and src[i] != '\n':
                i += 1
            continue

        if c == '[' and i + 1 < n and src[i+1] in ('[', '='):
            eqs = 0
            k = i + 1
            while k < n and src[k] == '=':
                eqs += 1
                k += 1
            if k < n and src[k] == '[':
                close = ']' + ('=' * eqs) + ']'
                start_content = k + 1
                if start_content < n and src[start_content] == '\n':
                    start_content += 1
                pos = src.find(close, start_content)
                if pos == -1:
                    raise Lua5xSyntaxError("unfinished long string")
                val = src[start_content:pos]
                raw = src[i:pos + len(close)]
                emit('STRING', val, raw)
                i = pos + len(close)
                continue

        if c in ('"', "'"):
            q = c
            j = i + 1
            buf = []
            while j < n and src[j] != q:
                ch = src[j]
                if ch == '\\':
                    j += 1
                    if j >= n:
                        raise Lua5xSyntaxError("unfinished string escape")
                    ec = src[j]
                    if ec in ('\n', '\r'):
                        if ec == '\r' and j + 1 < n and src[j+1] == '\n':
                            j += 1
                        buf.append('\n')
                        j += 1
                        continue
                    if ver >= (5, 2) and ec == 'z':
                        j += 1
                        while j < n and src[j] in ' \t\r\n':
                            j += 1
                        continue
                    if ver >= (5, 3) and ec == 'u' and j + 1 < n and src[j+1] == '{':
                        cb = src.find('}', j + 2)
                        if cb != -1 and cb - (j + 2) <= 8:
                            hs = src[j+2:cb]
                            if all(c in '0123456789abcdefABCDEF' for c in hs):
                                buf.append(chr(int(hs, 16)))
                                j = cb + 1
                                continue
                    if ver >= (5, 2) and ec in ('x', 'X') and j + 2 < n and all(c in '0123456789abcdefABCDEF' for c in src[j+1:j+3]):
                        buf.append(chr(int(src[j+1:j+3], 16)))
                        j += 3
                        continue
                    if ec.isdigit():
                        k = j
                        while k < n and k - j < 3 and src[k].isdigit():
                            k += 1
                        buf.append(chr(int(src[j:k])))
                        j = k
                        continue
                    esc_map = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n',
                               'r': '\r', 't': '\t', 'v': '\v', '\\': '\\',
                               '"': '"', "'": "'"}
                    buf.append(esc_map.get(ec, ec))
                    j += 1
                else:
                    if ch in ('\r', '\n'):
                        raise Lua5xSyntaxError("unfinished string literal")
                    buf.append(ch)
                    j += 1
            if j >= n:
                raise Lua5xSyntaxError("unterminated string")
            raw = src[i:j+1]
            emit('STRING', ''.join(buf), raw)
            i = j + 1
            continue

        if c.isdigit() or (c == '.' and i + 1 < n and src[i+1].isdigit()):
            j = i
            if src[i:i+2] in ('0x', '0X'):
                j += 2
                valid_hex = '0123456789abcdefABCDEF'
                if ver >= (5, 2):
                    while j < n and (src[j] in valid_hex or src[j] in '.pP'):
                        if src[j] in 'pP' and j + 1 < n and src[j+1] in '+-':
                            j += 2
                        else:
                            j += 1
                else:
                    while j < n and (src[j] in valid_hex):
                        j += 1
            else:
                while j < n and (src[j].isdigit() or src[j] == '.'):
                    j += 1
                if j < n and src[j] in 'eE':
                    j += 1
                    if j < n and src[j] in '+-':
                        j += 1
                    while j < n and src[j].isdigit():
                        j += 1
            val = src[i:j]
            emit('NUMBER', val, val)
            i = j
            continue

        if c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'):
                j += 1
            word = src[i:j]
            kind = 'KW' if word in kw_set else 'NAME'
            emit(kind, word, word)
            i = j
            continue

        if ver >= (5, 2):
            if src[i:i+2] == '::':
                emit('OP', '::', '::')
                i += 2
                continue

        if ver >= (5, 3):
            if src[i:i+2] in ('//', '<<', '>>'):
                emit('OP', src[i:i+2], src[i:i+2])
                i += 2
                continue

        three = src[i:i+3]
        if three == '...':
            emit('OP', '...', '...')
            i += 3
            continue

        two = src[i:i+2]
        if two in ('==', '~=', '<=', '>=', '..'):
            emit('OP', two, two)
            i += 2
            continue

        valid_single = '+-*/%^<>=.~#'
        if ver >= (5, 3):
            valid_single += '&|'
        if c in valid_single:
            emit('OP', c, c)
            i += 1
            continue

        single_map = {
            '(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACK', ']': 'RBRACK',
            '{': 'LBRACE', '}': 'RBRACE', ',': 'COMMA', ';': 'SEMI',
            ':': 'COLON',
        }
        if c in single_map:
            emit(single_map[c], c, c)
            i += 1
            continue

        raise Lua5xSyntaxError(f"unexpected character {c!r} at index {i}")

    tokens.append(Token('EOF', ''))
    return tokens

class Node(dict):
    pass

def N(type_, **kw):
    kw['type'] = type_
    return Node(kw)

class Parser:
    def __init__(self, toks, version="5.1"):
        self.toks = toks
        self.pos = 0
        self.ver = _normalize_ver(version)

    def peek(self, offset=0):
        p = self.pos + offset
        if p < len(self.toks):
            return self.toks[p]
        return self.toks[-1]

    def at(self, kind, value=None):
        t = self.peek()
        return t.kind == kind and (value is None or t.value == value)

    def advance(self):
        t = self.toks[self.pos]
        if self.pos < len(self.toks) - 1:
            self.pos += 1
        return t

    def expect(self, kind, value=None):
        t = self.peek()
        if t.kind != kind or (value is not None and t.value != value):
            raise Lua5xSyntaxError(f"expected {kind} {value!r}, got {t.kind} {t.value!r} at pos {self.pos}")
        return self.advance()

    def opt(self, kind, value=None):
        if self.at(kind, value):
            return self.advance()
        return None

    def parse_chunk(self):
        body = self.parse_block()
        self.expect('EOF')
        return N('Chunk', body=body)

    def parse_block(self):
        stmts = []
        while True:
            while self.opt('SEMI'):
                pass
            t = self.peek()
            if t.kind == 'EOF':
                break
            if t.kind == 'KW' and t.value in BLOCK_END_KW:
                break
            stmts.append(self.parse_stmt())
            if stmts and stmts[-1]['type'] == 'Return':
                break
        return stmts

    def parse_stmt(self):
        t = self.peek()

        if self.ver >= (5, 2) and t.kind == 'OP' and t.value == '::':
            self.advance()
            name = self.expect('NAME').value
            self.expect('OP', '::')
            return N('Label', name=name)

        if t.kind == 'KW':
            kw = t.value
            if self.ver >= (5, 2) and kw == 'goto':
                self.advance()
                name = self.expect('NAME').value
                return N('Goto', name=name)
            if kw == 'local':
                return self.parse_local()
            if kw == 'if':
                return self.parse_if()
            if kw == 'while':
                return self.parse_while()
            if kw == 'do':
                self.advance()
                body = self.parse_block()
                self.expect('KW', 'end')
                return N('Do', body=body)
            if kw == 'for':
                return self.parse_for()
            if kw == 'repeat':
                return self.parse_repeat()
            if kw == 'function':
                return self.parse_function_stmt()
            if kw == 'return':
                self.advance()
                vals = []
                nt = self.peek()
                if not (nt.kind == 'EOF' or (nt.kind == 'KW' and nt.value in BLOCK_END_KW) or nt.kind == 'SEMI'):
                    vals = self.parse_exprlist()
                return N('Return', values=vals)
            if kw == 'break':
                self.advance()
                return N('Break')

        return self.parse_expr_stmt()

    def parse_local(self):
        self.expect('KW', 'local')
        if self.at('KW', 'function'):
            self.advance()
            name = self.expect('NAME').value
            params, vararg = self.parse_params()
            body = self.parse_block()
            self.expect('KW', 'end')
            return N('LocalFunction', name=name, params=params, vararg=vararg, body=body)

        def parse_local_item():
            name = self.expect('NAME').value
            attrib = None
            if self.ver >= (5, 4) and self.at('OP', '<'):
                self.advance()
                attrib = self.expect('NAME').value
                self.expect('OP', '>')
            return name, attrib

        n, a = parse_local_item()
        names = [n]
        attribs = [a]
        while self.opt('COMMA'):
            n, a = parse_local_item()
            names.append(n)
            attribs.append(a)

        values = []
        if self.opt('OP', '='):
            values = self.parse_exprlist()
        return N('Local', names=names, attribs=attribs, values=values)

    def parse_function_stmt(self):
        self.expect('KW', 'function')
        path = [self.expect('NAME').value]
        is_method = False
        while self.opt('OP', '.'):
            path.append(self.expect('NAME').value)
        if self.opt('COLON'):
            path.append(self.expect('NAME').value)
            is_method = True
        params, vararg = self.parse_params()
        if is_method:
            params = ['self'] + params
        body = self.parse_block()
        self.expect('KW', 'end')
        return N('FunctionStmt', path=path, is_method=is_method, params=params, vararg=vararg, body=body)

    def parse_params(self):
        self.expect('LPAREN')
        params = []
        vararg = False
        if not self.at('RPAREN'):
            while True:
                if self.opt('OP', '...'):
                    vararg = True
                    break
                params.append(self.expect('NAME').value)
                if not self.opt('COMMA'):
                    break
        self.expect('RPAREN')
        return params, vararg

    def parse_if(self):
        self.expect('KW', 'if')
        cond = self.parse_expr()
        self.expect('KW', 'then')
        body = self.parse_block()
        elseifs = []
        orelse = None
        while self.at('KW', 'elseif'):
            self.advance()
            econd = self.parse_expr()
            self.expect('KW', 'then')
            ebody = self.parse_block()
            elseifs.append((econd, ebody))
        if self.opt('KW', 'else'):
            orelse = self.parse_block()
        self.expect('KW', 'end')
        return N('If', cond=cond, body=body, elseifs=elseifs, orelse=orelse)

    def parse_while(self):
        self.expect('KW', 'while')
        cond = self.parse_expr()
        self.expect('KW', 'do')
        body = self.parse_block()
        self.expect('KW', 'end')
        return N('While', cond=cond, body=body)

    def parse_repeat(self):
        self.expect('KW', 'repeat')
        body = self.parse_block()
        self.expect('KW', 'until')
        cond = self.parse_expr()
        return N('Repeat', body=body, cond=cond)

    def parse_for(self):
        self.expect('KW', 'for')
        name = self.expect('NAME').value
        if self.opt('OP', '='):
            start = self.parse_expr()
            self.expect('COMMA')
            limit = self.parse_expr()
            step = None
            if self.opt('COMMA'):
                step = self.parse_expr()
            self.expect('KW', 'do')
            body = self.parse_block()
            self.expect('KW', 'end')
            return N('NumericFor', var=name, start=start, limit=limit, step=step, body=body)
        else:
            names = [name]
            while self.opt('COMMA'):
                names.append(self.expect('NAME').value)
            self.expect('KW', 'in')
            iters = self.parse_exprlist()
            self.expect('KW', 'do')
            body = self.parse_block()
            self.expect('KW', 'end')
            return N('GenericFor', names=names, iters=iters, body=body)

    def parse_expr_stmt(self):
        expr = self.parse_suffixedexp()
        if self.at('OP', '=') or self.at('COMMA'):
            targets = [self.expr_to_target(expr)]
            while self.opt('COMMA'):
                targets.append(self.expr_to_target(self.parse_suffixedexp()))
            self.expect('OP', '=')
            values = self.parse_exprlist()
            return N('Assign', targets=targets, values=values, op='=')
        if expr['type'] in ('Call', 'MethodCall'):
            return N('ExprStat', expr=expr)
        raise Lua5xSyntaxError(f"syntax error: unexpected expression statement of type {expr['type']}")

    def expr_to_target(self, e):
        if e['type'] in ('Name', 'Index'):
            return e
        raise Lua5xSyntaxError(f"invalid assignment target: {e['type']}")

    def parse_exprlist(self):
        exprs = [self.parse_expr()]
        while self.opt('COMMA'):
            exprs.append(self.parse_expr())
        return exprs

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.at('KW', 'or'):
            self.advance()
            right = self.parse_and()
            left = N('Binop', op='or', left=left, right=right)
        return left

    def parse_and(self):
        left = self.parse_cmp()
        while self.at('KW', 'and'):
            self.advance()
            right = self.parse_cmp()
            left = N('Binop', op='and', left=left, right=right)
        return left

    def parse_cmp(self):
        left = self.parse_bor() if self.ver >= (5, 3) else self.parse_concat()
        while self.at('OP') and self.peek().value in ('<', '<=', '>', '>=', '==', '~='):
            op = self.advance().value
            right = self.parse_bor() if self.ver >= (5, 3) else self.parse_concat()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_bor(self):
        left = self.parse_bxor()
        while self.at('OP', '|'):
            op = self.advance().value
            right = self.parse_bxor()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_bxor(self):
        left = self.parse_band()
        while self.at('OP', '~'):
            op = self.advance().value
            right = self.parse_band()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_band(self):
        left = self.parse_shift()
        while self.at('OP', '&'):
            op = self.advance().value
            right = self.parse_shift()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_shift(self):
        left = self.parse_concat()
        while self.at('OP') and self.peek().value in ('<<', '>>'):
            op = self.advance().value
            right = self.parse_concat()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_concat(self):
        left = self.parse_add()
        if self.at('OP', '..'):
            self.advance()
            right = self.parse_concat()
            return N('Binop', op='..', left=left, right=right)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.at('OP') and self.peek().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_mul()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_mul(self):
        left = self.parse_unary()
        valid_ops = ('*', '/', '%', '//') if self.ver >= (5, 3) else ('*', '/', '%')
        while self.at('OP') and self.peek().value in valid_ops:
            op = self.advance().value
            right = self.parse_unary()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_unary(self):
        t = self.peek()
        unary_ops = ('-', '#', '~') if self.ver >= (5, 3) else ('-', '#')
        if (t.kind == 'KW' and t.value == 'not') or (t.kind == 'OP' and t.value in unary_ops):
            self.advance()
            operand = self.parse_unary()
            return N('Unop', op=t.value, operand=operand)
        return self.parse_pow()

    def parse_pow(self):
        left = self.parse_simple()
        if self.at('OP', '^'):
            self.advance()
            right = self.parse_unary()
            return N('Binop', op='^', left=left, right=right)
        return left

    def parse_simple(self):
        t = self.peek()
        if t.kind == 'NUMBER':
            self.advance()
            return N('Number', raw=t.raw)
        if t.kind == 'STRING':
            self.advance()
            return N('String', value=t.value, raw=t.raw)
        if t.kind == 'KW' and t.value == 'nil':
            self.advance()
            return N('Nil')
        if t.kind == 'KW' and t.value == 'true':
            self.advance()
            return N('True')
        if t.kind == 'KW' and t.value == 'false':
            self.advance()
            return N('False')
        if t.kind == 'OP' and t.value == '...':
            self.advance()
            return N('Vararg')
        if t.kind == 'KW' and t.value == 'function':
            self.advance()
            params, vararg = self.parse_params()
            body = self.parse_block()
            self.expect('KW', 'end')
            return N('FunctionExpr', params=params, vararg=vararg, body=body)
        if t.kind == 'LBRACE':
            return self.parse_table()
        return self.parse_suffixedexp()

    def parse_suffixedexp(self):
        expr = self.parse_primaryexp()
        while True:
            if self.opt('OP', '.'):
                name = self.expect('NAME').value
                expr = N('Index', obj=expr, key=N('String', value=name, raw=None), dot=True)
            elif self.opt('LBRACK'):
                key = self.parse_expr()
                self.expect('RBRACK')
                expr = N('Index', obj=expr, key=key, dot=False)
            elif self.opt('COLON'):
                method = self.expect('NAME').value
                args = self.parse_args()
                expr = N('MethodCall', obj=expr, method=method, args=args)
            elif self.at('LPAREN') or self.at('LBRACE') or self.at('STRING'):
                args = self.parse_args()
                expr = N('Call', fn=expr, args=args)
            else:
                break
        return expr

    def parse_primaryexp(self):
        t = self.peek()
        if t.kind == 'NAME':
            self.advance()
            return N('Name', name=t.value)
        if self.opt('LPAREN'):
            e = self.parse_expr()
            self.expect('RPAREN')
            return N('Paren', expr=e)
        raise Lua5xSyntaxError(f"unexpected symbol in primary expression: {t.kind} {t.value!r}")

    def parse_args(self):
        if self.opt('LPAREN'):
            args = []
            if not self.at('RPAREN'):
                args = self.parse_exprlist()
            self.expect('RPAREN')
            return args
        if self.at('LBRACE'):
            return [self.parse_table()]
        if self.at('STRING'):
            t = self.advance()
            return [N('String', value=t.value, raw=t.raw)]
        raise Lua5xSyntaxError(f"unexpected function call argument token: {self.peek()}")

    def parse_table(self):
        self.expect('LBRACE')
        fields = []
        while not self.at('RBRACE'):
            if self.opt('LBRACK'):
                k = self.parse_expr()
                self.expect('RBRACK')
                self.expect('OP', '=')
                v = self.parse_expr()
                fields.append(N('TField', key=k, value=v, kind='computed'))
            elif self.at('NAME') and self.peek(1).kind == 'OP' and self.peek(1).value == '=':
                name = self.advance().value
                self.advance()
                v = self.parse_expr()
                fields.append(N('TField', key=N('String', value=name, raw=None), value=v, kind='named'))
            else:
                v = self.parse_expr()
                fields.append(N('TField', key=None, value=v, kind='item'))
            if not (self.opt('COMMA') or self.opt('SEMI')):
                break
        self.expect('RBRACE')
        return N('Table', fields=fields)

def parse(src, version="5.1"):
    toks = tokenize(src, version=version)
    p = Parser(toks, version=version)
    return p.parse_chunk()
