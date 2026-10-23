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

def unparse_expr(e, version="5.1"):
    ver = _normalize_ver(version)
    t = e['type']
    if t == 'Number':
        return e['raw']
    if t == 'String':
        return e['raw'] if e.get('raw') else _quote(e['value'])
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
        return '(' + unparse_expr(e['expr'], version) + ')'
    if t == 'Binop':
        op = e['op']
        if op == '//' and ver < (5, 3):
            return 'math.floor((' + unparse_expr(e['left'], version) + ')/(' + unparse_expr(e['right'], version) + '))'
        return unparse_expr(e['left'], version) + ' ' + op + ' ' + unparse_expr(e['right'], version)
    if t == 'Unop':
        op = e['op']
        sp = ' ' if op in ('not', '-') else ''
        return op + sp + unparse_expr(e['operand'], version)
    if t == 'Index':
        if e['dot']:
            return unparse_expr(e['obj'], version) + '.' + e['key']['value']
        return unparse_expr(e['obj'], version) + '[' + unparse_expr(e['key'], version) + ']'
    if t == 'Call':
        return unparse_expr(e['fn'], version) + '(' + ','.join(unparse_expr(a, version) for a in e['args']) + ')'
    if t == 'MethodCall':
        return unparse_expr(e['obj'], version) + ':' + e['method'] + '(' + ','.join(unparse_expr(a, version) for a in e['args']) + ')'
    if t == 'FunctionExpr':
        params = list(e['params'])
        if e['vararg']:
            params.append('...')
        return 'function(' + ','.join(params) + ') ' + unparse_block(e['body'], version) + ' end'
    if t == 'Table':
        parts = []
        for f in e['fields']:
            if f['kind'] == 'item':
                parts.append(unparse_expr(f['value'], version))
            elif f['kind'] == 'named':
                parts.append(f['key']['value'] + '=' + unparse_expr(f['value'], version))
            else:
                parts.append('[' + unparse_expr(f['key'], version) + ']=' + unparse_expr(f['value'], version))
        return '{' + ','.join(parts) + '}'
    raise ValueError(f"unknown expr node {t}")

def unparse_stmt(s, version="5.1"):
    ver = _normalize_ver(version)
    t = s['type']
    if t == 'Local':
        names = s['names']
        attribs = s.get('attribs', [])
        parts = []
        for i, name in enumerate(names):
            if ver >= (5, 4) and i < len(attribs) and attribs[i]:
                parts.append(f"{name}<{attribs[i]}>")
            else:
                parts.append(name)
        head = 'local ' + ','.join(parts)
        if s['values']:
            head += ' =' + ','.join(unparse_expr(v, version) for v in s['values'])
        return head + ' '
    if t == 'LocalFunction':
        params = list(s['params'])
        if s['vararg']:
            params.append('...')
        return f"local function {s['name']}(" + ','.join(params) + ') ' + unparse_block(s['body'], version) + ' end '
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
        return f"function {name}(" + ','.join(params) + ') ' + unparse_block(s['body'], version) + ' end '
    if t == 'Assign':
        targets = ','.join(unparse_expr(x, version) for x in s['targets'])
        values = ','.join(unparse_expr(v, version) for v in s['values'])
        return f"{targets}{s['op']}{values} "
    if t == 'ExprStat':
        return unparse_expr(s['expr'], version) + ' '
    if t == 'Return':
        if s['values']:
            return 'return ' + ','.join(unparse_expr(v, version) for v in s['values']) + ' '
        return 'return '
    if t == 'Break':
        return 'break '
    if t == 'Goto':
        return f"goto {s['name']} "
    if t == 'Label':
        return f"::{s['name']}:: "
    if t == 'Do':
        return 'do ' + unparse_block(s['body'], version) + ' end '
    if t == 'While':
        return f"while {unparse_expr(s['cond'], version)} do " + unparse_block(s['body'], version) + ' end '
    if t == 'Repeat':
        return 'repeat ' + unparse_block(s['body'], version) + f" until {unparse_expr(s['cond'], version)} "
    if t == 'NumericFor':
        parts = [unparse_expr(s['start'], version), unparse_expr(s['limit'], version)]
        if s['step'] is not None:
            parts.append(unparse_expr(s['step'], version))
        return f"for {s['var']}=" + ','.join(parts) + ' do ' + unparse_block(s['body'], version) + ' end '
    if t == 'GenericFor':
        names = ','.join(s['names'])
        iters = ','.join(unparse_expr(v, version) for v in s['iters'])
        return f"for {names} in {iters} do " + unparse_block(s['body'], version) + ' end '
    if t == 'If':
        out = [f"if {unparse_expr(s['cond'], version)} then ", unparse_block(s['body'], version)]
        for cond, body in s['elseifs']:
            out.append(f" elseif {unparse_expr(cond, version)} then ")
            out.append(unparse_block(body, version))
        if s['orelse'] is not None:
            out.append(' else ')
            out.append(unparse_block(s['orelse'], version))
        out.append(' end ')
        return ''.join(out)
    raise ValueError(f"unknown stmt node {t}")

def unparse_block(stmts, version="5.1"):
    return ''.join(unparse_stmt(s, version) for s in stmts)

def unparse_chunk(chunk, version="5.1"):
    return unparse_block(chunk['body'], version)
