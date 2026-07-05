KEYWORDS = {
    'and', 'break', 'continue', 'do', 'else', 'elseif', 'end', 'false',
    'for', 'function', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat',
    'return', 'then', 'true', 'until', 'while',
}

BLOCK_END_KW = {'end', 'else', 'elseif', 'until'}


class LuauSyntaxError(Exception):
    pass


class Token:
    __slots__ = ('kind', 'value', 'raw')

    def __init__(self, kind, value, raw=None):
        self.kind = kind
        self.value = value
        self.raw = raw if raw is not None else value

    def __repr__(self):
        return f"Token({self.kind!r},{self.value!r})"


def tokenize(src):
    tokens = []
    i = 0
    n = len(src)

    def emit(kind, value, raw=None):
        tokens.append(Token(kind, value, raw))

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
                    end = src.find(close, k + 1)
                    i = (end + len(close)) if end != -1 else n
                    continue
            while i < n and src[i] != '\n':
                i += 1
            continue

        if c == '[' and i + 1 < n and src[i+1] in ('[', '='):
            j = i + 1
            eqs = 0
            while j < n and src[j] == '=':
                eqs += 1
                j += 1
            if j < n and src[j] == '[':
                start_content = j + 1
                if start_content < n and src[start_content] == '\n':
                    start_content += 1
                close = ']' + ('=' * eqs) + ']'
                end = src.find(close, j + 1)
                if end == -1:
                    raise LuauSyntaxError("unterminated long string")
                content = src[start_content:end]
                emit('STRING', content, src[i:end+len(close)])
                i = end + len(close)
                continue

        if c in ('"', "'"):
            q = c
            j = i + 1
            buf = []
            while j < n and src[j] != q:
                if src[j] == '\\' and j + 1 < n:
                    esc = src[j+1]
                    esc_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
                               '"': '"', "'": "'", '\n': '\n', 'a': '\a',
                               'b': '\b', 'f': '\f', 'v': '\v'}
                    if esc.isdigit():
                        k = j + 1
                        while k < n and k - (j+1) < 3 and src[k].isdigit():
                            k += 1
                        buf.append(chr(int(src[j+1:k])))
                        j = k
                        continue
                    elif esc == 'x' and j + 3 < n:
                        buf.append(chr(int(src[j+2:j+4], 16)))
                        j += 4
                        continue
                    elif esc == 'z':
                        j += 2
                        while j < n and src[j] in ' \t\r\n':
                            j += 1
                        continue
                    else:
                        buf.append(esc_map.get(esc, esc))
                        j += 2
                        continue
                buf.append(src[j])
                j += 1
            if j >= n:
                raise LuauSyntaxError("unterminated string")
            raw = src[i:j+1]
            emit('STRING', ''.join(buf), raw)
            i = j + 1
            continue

        if c == '`':
            j = i + 1
            depth = 0
            while j < n:
                if src[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if src[j] == '{':
                    depth += 1
                elif src[j] == '}':
                    depth -= 1
                elif src[j] == '`' and depth == 0:
                    break
                j += 1
            if j >= n:
                raise LuauSyntaxError("unterminated interpolated string")
            raw = src[i:j+1]
            emit('ISTRING', raw, raw)
            i = j + 1
            continue

        if c.isdigit() or (c == '.' and i + 1 < n and src[i+1].isdigit()):
            j = i
            if src[i:i+2] in ('0x', '0X'):
                j += 2
                while j < n and (src[j] in '0123456789abcdefABCDEF'):
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
            emit('NUMBER', src[i:j], src[i:j])
            i = j
            continue

        if c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'):
                j += 1
            word = src[i:j]
            kind = 'KW' if word in KEYWORDS else 'NAME'
            emit(kind, word, word)
            i = j
            continue

        three = src[i:i+3]
        if three in ('...', '..='):
            emit('OP', three, three)
            i += 3
            continue

        two = src[i:i+2]
        if two in ('==', '~=', '<=', '>=', '..', '//', '::', '+=', '-=',
                   '*=', '/=', '%=', '^='):
            emit('OP', two, two)
            i += 2
            continue

        if c in '+-*/%^<>=.~#':
            emit('OP', c, c)
            i += 1
            continue

        single_map = {
            '(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACK', ']': 'RBRACK',
            '{': 'LBRACE', '}': 'RBRACE', ',': 'COMMA', ';': 'SEMI',
        }
        if c in single_map:
            emit(single_map[c], c, c)
            i += 1
            continue

        if c == ':':
            emit('COLON', ':', ':')
            i += 1
            continue

        raise LuauSyntaxError(f"unexpected character {c!r} at {i}")

    tokens.append(Token('EOF', ''))
    return tokens


class Node(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

    def __setattr__(self, k, v):
        self[k] = v


def N(type_, **kw):
    kw['type'] = type_
    return Node(kw)


ASSIGN_OPS = {'=', '+=', '-=', '*=', '/=', '//=', '%=', '^=', '..='}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    def peek(self, off=0):
        p = self.pos + off
        return self.toks[p] if p < len(self.toks) else self.toks[-1]

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
            raise LuauSyntaxError(
                f"expected {kind} {value!r}, got {t.kind} {t.value!r} @ {self.pos}")
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

        if t.kind == 'OP' and t.value == '::':
            self.advance()
            name = self.expect('NAME').value
            self.expect('OP', '::')
            return N('Label', name=name)

        if t.kind == 'KW':
            kw = t.value
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
                if not (nt.kind == 'EOF' or (nt.kind == 'KW' and nt.value in BLOCK_END_KW)
                        or nt.kind == 'SEMI'):
                    vals = self.parse_exprlist()
                return N('Return', values=vals)
            if kw == 'break':
                self.advance()
                return N('Break')
            if kw == 'continue':
                self.advance()
                return N('Continue')

        return self.parse_expr_stmt()

    def parse_local(self):
        self.expect('KW', 'local')
        if self.at('KW', 'function'):
            self.advance()
            name = self.expect('NAME').value
            params, vararg = self.parse_params()
            body = self.parse_block()
            self.expect('KW', 'end')
            return N('LocalFunction', name=name, params=params,
                      vararg=vararg, body=body)
        names = [self.expect('NAME').value]
        attribs = [self.parse_attrib()]
        while self.opt('COMMA'):
            names.append(self.expect('NAME').value)
            attribs.append(self.parse_attrib())
        values = []
        if self.opt('OP', '='):
            values = self.parse_exprlist()
        return N('Local', names=names, attribs=attribs, values=values)

    def parse_attrib(self):
        if self.at('OP', '<'):
            self.advance()
            name = self.expect('NAME').value
            self.expect('OP', '>')
            return name
        return None

    def parse_if(self):
        self.expect('KW', 'if')
        cond = self.parse_expr()
        self.expect('KW', 'then')
        body = self.parse_block()
        clauses = []
        else_body = None
        while self.at('KW', 'elseif'):
            self.advance()
            c2 = self.parse_expr()
            self.expect('KW', 'then')
            b2 = self.parse_block()
            clauses.append((c2, b2))
        if self.opt('KW', 'else'):
            else_body = self.parse_block()
        self.expect('KW', 'end')
        return N('If', cond=cond, body=body, elseifs=clauses, orelse=else_body)

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
        first = self.expect('NAME').value
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
            return N('NumericFor', var=first, start=start, limit=limit,
                      step=step, body=body)
        names = [first]
        while self.opt('COMMA'):
            names.append(self.expect('NAME').value)
        self.expect('KW', 'in')
        iters = self.parse_exprlist()
        self.expect('KW', 'do')
        body = self.parse_block()
        self.expect('KW', 'end')
        return N('GenericFor', names=names, iters=iters, body=body)

    def parse_function_stmt(self):
        self.expect('KW', 'function')
        path = [self.expect('NAME').value]
        is_method = False
        while self.at('OP', '.'):
            self.advance()
            path.append(self.expect('NAME').value)
        if self.at('COLON'):
            self.advance()
            path.append(self.expect('NAME').value)
            is_method = True
        params, vararg = self.parse_params()
        if is_method:
            params = ['self'] + params
        body = self.parse_block()
        self.expect('KW', 'end')
        return N('FunctionStmt', path=path, is_method=is_method,
                  params=params, vararg=vararg, body=body)

    def parse_params(self):
        self.expect('LPAREN')
        params = []
        vararg = False
        if not self.at('RPAREN'):
            while True:
                if self.at('OP', '...'):
                    self.advance()
                    vararg = True
                    break
                params.append(self.expect('NAME').value)
                if not self.opt('COMMA'):
                    break
        self.expect('RPAREN')
        return params, vararg

    def parse_expr_stmt(self):
        expr = self.parse_suffixedexp()
        t = self.peek()
        if t.kind == 'COMMA' or (t.kind == 'OP' and t.value in ASSIGN_OPS):
            targets = [expr]
            while self.opt('COMMA'):
                targets.append(self.parse_suffixedexp())
            op = self.expect('OP').value
            if op not in ASSIGN_OPS:
                raise LuauSyntaxError(f"expected assignment operator, got {op!r}")
            values = self.parse_exprlist()
            return N('Assign', targets=targets, values=values, op=op)
        if expr['type'] not in ('Call', 'MethodCall'):
            raise LuauSyntaxError(f"syntax error, unexpected expression stmt {expr['type']}")
        return N('ExprStat', expr=expr)

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
        left = self.parse_concat()
        while self.at('OP') and self.peek().value in ('<', '<=', '>', '>=', '==', '~='):
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
        while self.at('OP') and self.peek().value in ('*', '/', '%', '//'):
            op = self.advance().value
            right = self.parse_unary()
            left = N('Binop', op=op, left=left, right=right)
        return left

    def parse_unary(self):
        t = self.peek()
        if (t.kind == 'KW' and t.value == 'not') or (t.kind == 'OP' and t.value in ('-', '#')):
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
        if t.kind == 'ISTRING':
            self.advance()
            return N('IString', raw=t.raw)
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

    def parse_primaryexp(self):
        t = self.peek()
        if t.kind == 'NAME':
            self.advance()
            return N('Name', name=t.value)
        if t.kind == 'LPAREN':
            self.advance()
            e = self.parse_expr()
            self.expect('RPAREN')
            return N('Paren', expr=e)
        raise LuauSyntaxError(f"unexpected token in expr {t.kind} {t.value!r}")

    def parse_suffixedexp(self):
        e = self.parse_primaryexp()
        while True:
            t = self.peek()
            if t.kind == 'OP' and t.value == '.':
                self.advance()
                name = self.expect('NAME').value
                e = N('Index', obj=e, key=N('String', value=name, raw=None), dot=True)
                continue
            if t.kind == 'LBRACK':
                self.advance()
                idx = self.parse_expr()
                self.expect('RBRACK')
                e = N('Index', obj=e, key=idx, dot=False)
                continue
            if t.kind == 'COLON':
                self.advance()
                name = self.expect('NAME').value
                args = self.parse_call_args()
                e = N('MethodCall', obj=e, method=name, args=args)
                continue
            if t.kind in ('LPAREN', 'STRING', 'LBRACE', 'ISTRING'):
                args = self.parse_call_args()
                e = N('Call', fn=e, args=args)
                continue
            break
        return e

    def parse_call_args(self):
        t = self.peek()
        if t.kind == 'STRING':
            self.advance()
            return [N('String', value=t.value, raw=t.raw)]
        if t.kind == 'ISTRING':
            self.advance()
            return [N('IString', raw=t.raw)]
        if t.kind == 'LBRACE':
            return [self.parse_table()]
        self.expect('LPAREN')
        args = []
        if not self.at('RPAREN'):
            args = self.parse_exprlist()
        self.expect('RPAREN')
        return args

    def parse_table(self):
        self.expect('LBRACE')
        fields = []
        while not self.at('RBRACE'):
            if self.at('LBRACK'):
                self.advance()
                k = self.parse_expr()
                self.expect('RBRACK')
                self.expect('OP', '=')
                v = self.parse_expr()
                fields.append(N('TField', key=k, value=v, kind='computed'))
            elif self.at('NAME') and self.peek(1).kind == 'OP' and self.peek(1).value == '=':
                name = self.advance().value
                self.advance()
                v = self.parse_expr()
                fields.append(N('TField', key=N('String', value=name, raw=None),
                                 value=v, kind='named'))
            else:
                v = self.parse_expr()
                fields.append(N('TField', key=None, value=v, kind='item'))
            if not (self.opt('COMMA') or self.opt('SEMI')):
                break
        self.expect('RBRACE')
        return N('Table', fields=fields)


def parse(src):
    toks = tokenize(src)
    p = Parser(toks)
    return p.parse_chunk()
