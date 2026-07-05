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


def unparse_expr(e):
    t = e['type']
    if t == 'Number':
        return e['raw']
    if t == 'String':
        return e['raw'] if e.get('raw') else _quote(e['value'])
    if t == 'IString':
        return e['raw']
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
        return '(' + unparse_expr(e['expr']) + ')'
    if t == 'Binop':
        op = e['op']
        if op in ('and', 'or'):
            return unparse_expr(e['left']) + ' ' + op + ' ' + unparse_expr(e['right'])
        return unparse_expr(e['left']) + op + unparse_expr(e['right'])
    if t == 'Unop':
        op = e['op']
        sp = ' ' if op == 'not' else ''
        return op + sp + unparse_expr(e['operand'])
    if t == 'Index':
        if e['dot']:
            return unparse_expr(e['obj']) + '.' + e['key']['value']
        return unparse_expr(e['obj']) + '[' + unparse_expr(e['key']) + ']'
    if t == 'Call':
        return unparse_expr(e['fn']) + '(' + ','.join(unparse_expr(a) for a in e['args']) + ')'
    if t == 'MethodCall':
        return unparse_expr(e['obj']) + ':' + e['method'] + '(' + ','.join(unparse_expr(a) for a in e['args']) + ')'
    if t == 'FunctionExpr':
        params = list(e['params'])
        if e['vararg']:
            params.append('...')
        return 'function(' + ','.join(params) + ') ' + unparse_block(e['body']) + ' end'
    if t == 'Table':
        parts = []
        for f in e['fields']:
            if f['kind'] == 'item':
                parts.append(unparse_expr(f['value']))
            elif f['kind'] == 'named':
                parts.append(f['key']['value'] + '=' + unparse_expr(f['value']))
            else:
                parts.append('[' + unparse_expr(f['key']) + ']=' + unparse_expr(f['value']))
        return '{' + ','.join(parts) + '}'
    raise ValueError(f"unknown expr node {t}")


def unparse_stmt(s):
    t = s['type']
    if t == 'Local':
        parts = []
        for name, attrib in zip(s['names'], s['attribs']):
            if attrib:
                parts.append(f"{name}<{attrib}>")
            else:
                parts.append(name)
        head = 'local ' + ','.join(parts)
        if s['values']:
            head += ' =' + ','.join(unparse_expr(v) for v in s['values'])
        return head + ' '
    if t == 'LocalFunction':
        params = list(s['params'])
        if s['vararg']:
            params.append('...')
        return (f"local function {s['name']}(" + ','.join(params) + ') ' +
                unparse_block(s['body']) + ' end ')
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
                unparse_block(s['body']) + ' end ')
    if t == 'Assign':
        targets = ','.join(unparse_expr(x) for x in s['targets'])
        values = ','.join(unparse_expr(v) for v in s['values'])
        return f"{targets}{s['op']}{values} "
    if t == 'ExprStat':
        return unparse_expr(s['expr']) + ' '
    if t == 'Return':
        if s['values']:
            return 'return ' + ','.join(unparse_expr(v) for v in s['values']) + ' '
        return 'return '
    if t == 'Break':
        return 'break '
    if t == 'Continue':
        return 'continue '
    if t == 'Label':
        return f"::{s['name']}:: "
    if t == 'Do':
        return 'do ' + unparse_block(s['body']) + ' end '
    if t == 'While':
        return f"while {unparse_expr(s['cond'])} do " + unparse_block(s['body']) + ' end '
    if t == 'Repeat':
        return 'repeat ' + unparse_block(s['body']) + f" until {unparse_expr(s['cond'])} "
    if t == 'NumericFor':
        parts = [unparse_expr(s['start']), unparse_expr(s['limit'])]
        if s['step'] is not None:
            parts.append(unparse_expr(s['step']))
        return (f"for {s['var']}=" + ','.join(parts) + ' do ' +
                unparse_block(s['body']) + ' end ')
    if t == 'GenericFor':
        names = ','.join(s['names'])
        iters = ','.join(unparse_expr(v) for v in s['iters'])
        return f"for {names} in {iters} do " + unparse_block(s['body']) + ' end '
    if t == 'If':
        out = [f"if {unparse_expr(s['cond'])} then ", unparse_block(s['body'])]
        for cond, body in s['elseifs']:
            out.append(f" elseif {unparse_expr(cond)} then ")
            out.append(unparse_block(body))
        if s['orelse'] is not None:
            out.append(' else ')
            out.append(unparse_block(s['orelse']))
        out.append(' end ')
        return ''.join(out)
    raise ValueError(f"unknown stmt node {t}")


def unparse_block(stmts):
    return ''.join(unparse_stmt(s) for s in stmts)


def unparse_chunk(chunk):
    return unparse_block(chunk['body'])
