import itertools

from luajit_ast import tokenize, Parser

_label_counter = itertools.count(1)


class Ctx:
    __slots__ = ('loop_labels',)

    def __init__(self):
        self.loop_labels = []


def _ctx(ctx):
    if ctx is None:
        return Ctx()
    return ctx


def _quote(s):
    out = ['"']
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\t':
            out.append('\\t')
        elif ch == '\r':
            out.append('\\r')
        else:
            out.append(ch)
    out.append('"')
    return ''.join(out)


_ISTRING_ESC_MAP = {
    'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
    '"': '"', "'": "'", 'a': '\a', 'b': '\b', 'f': '\f', 'v': '\v',
    '{': '{', '}': '}', '`': '`',
}


def _split_istring(raw):
    inner = raw[1:-1]
    parts = []
    buf = []
    i = 0
    n = len(inner)
    while i < n:
        c = inner[i]
        if c == '\\' and i + 1 < n:
            esc = inner[i + 1]
            if esc.isdigit():
                j = i + 1
                k = j
                while k < n and k - j < 3 and inner[k].isdigit():
                    k += 1
                buf.append(chr(int(inner[j:k])))
                i = k
                continue
            if esc == 'x' and i + 3 < n:
                buf.append(chr(int(inner[i + 2:i + 4], 16)))
                i += 4
                continue
            buf.append(_ISTRING_ESC_MAP.get(esc, esc))
            i += 2
            continue
        if c == '{':
            if buf:
                parts.append(('lit', ''.join(buf)))
                buf = []
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if inner[j] == '{':
                    depth += 1
                elif inner[j] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            parts.append(('expr', inner[i + 1:j]))
            i = j + 1
            continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(('lit', ''.join(buf)))
    return parts


def _desugar_istring(raw, ctx):
    parts = _split_istring(raw)
    pieces = []
    for kind, text in parts:
        if kind == 'lit':
            if text:
                pieces.append(_quote(text))
        else:
            sub_tokens = tokenize(text)
            sub_expr = Parser(sub_tokens).parse_expr()
            pieces.append('tostring(' + unparse_expr(sub_expr, ctx) + ')')
    if not pieces:
        return '""'
    return '(' + '..'.join(pieces) + ')'


def unparse_expr(e, ctx=None):
    ctx = _ctx(ctx)
    t = e['type']
    if t == 'Number':
        return e['raw']
    if t == 'String':
        return e['raw'] if e.get('raw') else _quote(e['value'])
    if t == 'IString':
        return _desugar_istring(e['raw'], ctx)
    if t == 'Nil':
        return 'nil'
    if t == 'True':
        return 'true'
    if t == 'False':
        return 'false'
    if t == 'Vararg':
        return '...'
    if t == 'Name':
        return e['name']
    if t == 'Paren':
        return '(' + unparse_expr(e['expr'], ctx) + ')'
    if t == 'Binop':
        op = e['op']
        if op == '//':
            return ('math.floor((' + unparse_expr(e['left'], ctx) + ')/(' +
                    unparse_expr(e['right'], ctx) + '))')
        return unparse_expr(e['left'], ctx) + ' ' + op + ' ' + unparse_expr(e['right'], ctx)
    if t == 'Unop':
        op = e['op']
        sp = ' ' if op in ('not', '-') else ''
        return op + sp + unparse_expr(e['operand'], ctx)
    if t == 'Index':
        if e['dot']:
            return unparse_expr(e['obj'], ctx) + '.' + e['key']['value']
        return unparse_expr(e['obj'], ctx) + '[' + unparse_expr(e['key'], ctx) + ']'
    if t == 'Call':
        return unparse_expr(e['fn'], ctx) + '(' + ','.join(unparse_expr(a, ctx) for a in e['args']) + ')'
    if t == 'MethodCall':
        return (unparse_expr(e['obj'], ctx) + ':' + e['method'] + '(' +
                ','.join(unparse_expr(a, ctx) for a in e['args']) + ')')
    if t == 'FunctionExpr':
        params = list(e['params'])
        if e['vararg']:
            params.append('...')
        return 'function(' + ','.join(params) + ') ' + unparse_block(e['body'], Ctx()) + ' end'
    if t == 'Table':
        parts = []
        for f in e['fields']:
            if f['kind'] == 'item':
                parts.append(unparse_expr(f['value'], ctx))
            elif f['kind'] == 'named':
                parts.append(f['key']['value'] + '=' + unparse_expr(f['value'], ctx))
            else:
                parts.append('[' + unparse_expr(f['key'], ctx) + ']=' + unparse_expr(f['value'], ctx))
        return '{' + ','.join(parts) + '}'
    raise ValueError(f"unknown expr node {t}")


def _emit_loop(ctx, head, body, tail):
    label = f"__cont_{next(_label_counter)}"
    ctx.loop_labels.append(label)
    try:
        inner = unparse_block(body, ctx)
    finally:
        ctx.loop_labels.pop()
    return head + inner + f" ::{label}:: " + tail


def unparse_stmt(s, ctx=None):
    ctx = _ctx(ctx)
    t = s['type']
    if t == 'Local':
        parts = list(s['names'])
        head = 'local ' + ','.join(parts)
        if s['values']:
            head += ' =' + ','.join(unparse_expr(v, ctx) for v in s['values'])
        return head + ' '
    if t == 'LocalFunction':
        params = list(s['params'])
        if s['vararg']:
            params.append('...')
        return (f"local function {s['name']}(" + ','.join(params) + ') ' +
                unparse_block(s['body'], Ctx()) + ' end ')
    if t == 'FunctionStmt':
        path = s['path']
        if s['is_method']:
            name = '.'.join(path[:-1]) + ':' + path[-1]
            params = s['params'][1:]
        else:
            name = '.'.join(path)
            params = s['params']
        if s['vararg']:
            params = list(params) + ['...']
        return (f"function {name}(" + ','.join(params) + ') ' +
                unparse_block(s['body'], Ctx()) + ' end ')
    if t == 'Assign':
        op = s['op']
        if op != '=':
            base_op = op[:-1]
            target_expr = unparse_expr(s['targets'][0], ctx)
            value_expr = unparse_expr(s['values'][0], ctx)
            if base_op == '//':
                rhs = f"math.floor(({target_expr})/({value_expr}))"
            else:
                rhs = f"({target_expr}){base_op}({value_expr})"
            return f"{target_expr}={rhs} "
        targets = ','.join(unparse_expr(x, ctx) for x in s['targets'])
        values = ','.join(unparse_expr(v, ctx) for v in s['values'])
        return f"{targets}{op}{values} "
    if t == 'ExprStat':
        return unparse_expr(s['expr'], ctx) + ' '
    if t == 'Return':
        if s['values']:
            return 'return ' + ','.join(unparse_expr(v, ctx) for v in s['values']) + ' '
        return 'return '
    if t == 'Break':
        return 'break '
    if t == 'Continue':
        if ctx.loop_labels:
            return f"goto {ctx.loop_labels[-1]} "
        return 'goto __cont_unreachable '
    if t == 'Goto':
        return f"goto {s['name']} "
    if t == 'Label':
        return f"::{s['name']}:: "
    if t == 'Do':
        return 'do ' + unparse_block(s['body'], ctx) + ' end '
    if t == 'While':
        head = f"while {unparse_expr(s['cond'], ctx)} do "
        return _emit_loop(ctx, head, s['body'], ' end ')
    if t == 'Repeat':
        label = f"__cont_{next(_label_counter)}"
        ctx.loop_labels.append(label)
        try:
            body_src = unparse_block(s['body'], ctx)
        finally:
            ctx.loop_labels.pop()
        tail = f" ::{label}:: until {unparse_expr(s['cond'], ctx)} "
        return 'repeat ' + body_src + tail
    if t == 'NumericFor':
        parts = [unparse_expr(s['start'], ctx), unparse_expr(s['limit'], ctx)]
        if s['step'] is not None:
            parts.append(unparse_expr(s['step'], ctx))
        head = f"for {s['var']}=" + ','.join(parts) + ' do '
        return _emit_loop(ctx, head, s['body'], ' end ')
    if t == 'GenericFor':
        names = ','.join(s['names'])
        iters = ','.join(unparse_expr(v, ctx) for v in s['iters'])
        head = f"for {names} in {iters} do "
        return _emit_loop(ctx, head, s['body'], ' end ')
    if t == 'If':
        out = [f"if {unparse_expr(s['cond'], ctx)} then ", unparse_block(s['body'], ctx)]
        for cond, body in s['elseifs']:
            out.append(f" elseif {unparse_expr(cond, ctx)} then ")
            out.append(unparse_block(body, ctx))
        if s['orelse'] is not None:
            out.append(' else ')
            out.append(unparse_block(s['orelse'], ctx))
        out.append(' end ')
        return ''.join(out)
    raise ValueError(f"unknown stmt node {t}")


def unparse_block(stmts, ctx=None):
    ctx = _ctx(ctx)
    return ''.join(unparse_stmt(s, ctx) for s in stmts)


def unparse_chunk(chunk, ctx=None):
    return unparse_block(chunk['body'], ctx)
