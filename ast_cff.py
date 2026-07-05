from luau_ast import parse, LuauSyntaxError, N
from luau_unparse import unparse_expr, unparse_stmt, unparse_block

LOOP_TYPES = {'While', 'Repeat', 'NumericFor', 'GenericFor'}
BLOCK_HOLDER_TYPES = {
    'Chunk', 'FunctionExpr', 'FunctionStmt', 'LocalFunction',
    'If', 'While', 'Repeat', 'NumericFor', 'GenericFor', 'Do',
}


class FlattenContext:
    def __init__(self, rng, gen_name_fn):
        self.rng = rng
        self.gen_name_fn = gen_name_fn

    def gen(self):
        return self.gen_name_fn(self.rng)

    def sid(self, used):
        while True:
            v = self.rng.randint(100000, 999999)
            if v not in used:
                used.add(v)
                return v


def contains_goto_or_label(stmts):
    for s in stmts:
        t = s['type']
        if t in ('Goto', 'Label'):
            return True
        for child in iter_child_blocks(s):
            if contains_goto_or_label(child):
                return True
    return False


def iter_child_blocks(stmt):
    t = stmt['type']
    if t == 'If':
        blocks = [stmt['body']]
        for _, b in stmt['elseifs']:
            blocks.append(b)
        if stmt['orelse'] is not None:
            blocks.append(stmt['orelse'])
        return blocks
    if t in ('While', 'Repeat', 'NumericFor', 'GenericFor', 'Do'):
        return [stmt['body']]
    if t in ('LocalFunction', 'FunctionStmt'):
        return [stmt['body']]
    if t == 'Local':
        blocks = []
        for v in stmt.get('values', []):
            blocks.extend(iter_expr_blocks(v))
        return blocks
    if t == 'Assign':
        blocks = []
        for v in stmt.get('values', []):
            blocks.extend(iter_expr_blocks(v))
        return blocks
    if t == 'ExprStat':
        return iter_expr_blocks(stmt['expr'])
    if t == 'Return':
        blocks = []
        for v in stmt.get('values', []):
            blocks.extend(iter_expr_blocks(v))
        return blocks
    return []


def iter_expr_blocks(expr):
    t = expr['type']
    if t == 'FunctionExpr':
        return [expr['body']]
    if t == 'Call':
        blocks = iter_expr_blocks(expr['fn'])
        for a in expr['args']:
            blocks.extend(iter_expr_blocks(a))
        return blocks
    if t == 'MethodCall':
        blocks = iter_expr_blocks(expr['obj'])
        for a in expr['args']:
            blocks.extend(iter_expr_blocks(a))
        return blocks
    if t == 'Binop':
        return iter_expr_blocks(expr['left']) + iter_expr_blocks(expr['right'])
    if t == 'Unop':
        return iter_expr_blocks(expr['operand'])
    if t == 'Paren':
        return iter_expr_blocks(expr['expr'])
    if t == 'Index':
        blocks = iter_expr_blocks(expr['obj'])
        if not expr['dot']:
            blocks.extend(iter_expr_blocks(expr['key']))
        return blocks
    if t == 'Table':
        blocks = []
        for f in expr['fields']:
            if f['key'] is not None and f['kind'] == 'computed':
                blocks.extend(iter_expr_blocks(f['key']))
            blocks.extend(iter_expr_blocks(f['value']))
        return blocks
    return []


def walk_and_flatten_expr(expr, ctx):
    t = expr['type']
    if t == 'FunctionExpr':
        expr['body'] = flatten_block(expr['body'], ctx, in_loop=False)
        return
    if t == 'Call':
        walk_and_flatten_expr(expr['fn'], ctx)
        for a in expr['args']:
            walk_and_flatten_expr(a, ctx)
        return
    if t == 'MethodCall':
        walk_and_flatten_expr(expr['obj'], ctx)
        for a in expr['args']:
            walk_and_flatten_expr(a, ctx)
        return
    if t == 'Binop':
        walk_and_flatten_expr(expr['left'], ctx)
        walk_and_flatten_expr(expr['right'], ctx)
        return
    if t == 'Unop':
        walk_and_flatten_expr(expr['operand'], ctx)
        return
    if t == 'Paren':
        walk_and_flatten_expr(expr['expr'], ctx)
        return
    if t == 'Index':
        walk_and_flatten_expr(expr['obj'], ctx)
        if not expr['dot']:
            walk_and_flatten_expr(expr['key'], ctx)
        return
    if t == 'Table':
        for f in expr['fields']:
            if f['key'] is not None and f['kind'] == 'computed':
                walk_and_flatten_expr(f['key'], ctx)
            walk_and_flatten_expr(f['value'], ctx)
        return


def descend_into_children_first(stmts, ctx):
    for s in stmts:
        t = s['type']
        if t == 'If':
            s['body'] = flatten_block(s['body'], ctx, in_loop=False)
            new_elseifs = []
            for cond, b in s['elseifs']:
                walk_and_flatten_expr(cond, ctx)
                new_elseifs.append((cond, flatten_block(b, ctx, in_loop=False)))
            s['elseifs'] = new_elseifs
            if s['orelse'] is not None:
                s['orelse'] = flatten_block(s['orelse'], ctx, in_loop=False)
            walk_and_flatten_expr(s['cond'], ctx)
        elif t == 'While':
            walk_and_flatten_expr(s['cond'], ctx)
            s['body'] = flatten_block(s['body'], ctx, in_loop=True)
        elif t == 'Repeat':
            s['body'] = flatten_block(s['body'], ctx, in_loop=True)
            walk_and_flatten_expr(s['cond'], ctx)
        elif t == 'NumericFor':
            walk_and_flatten_expr(s['start'], ctx)
            walk_and_flatten_expr(s['limit'], ctx)
            if s['step'] is not None:
                walk_and_flatten_expr(s['step'], ctx)
            s['body'] = flatten_block(s['body'], ctx, in_loop=True)
        elif t == 'GenericFor':
            for it in s['iters']:
                walk_and_flatten_expr(it, ctx)
            s['body'] = flatten_block(s['body'], ctx, in_loop=True)
        elif t == 'Do':
            s['body'] = flatten_block(s['body'], ctx, in_loop=False)
        elif t in ('LocalFunction', 'FunctionStmt'):
            s['body'] = flatten_block(s['body'], ctx, in_loop=False)
        elif t == 'Local':
            for v in s.get('values', []):
                walk_and_flatten_expr(v, ctx)
        elif t == 'Assign':
            for v in s.get('values', []):
                walk_and_flatten_expr(v, ctx)
            for tgt in s.get('targets', []):
                walk_and_flatten_expr(tgt, ctx)
        elif t == 'ExprStat':
            walk_and_flatten_expr(s['expr'], ctx)
        elif t == 'Return':
            for v in s.get('values', []):
                walk_and_flatten_expr(v, ctx)
    return stmts


def stmt_contains_own_break_or_continue(stmt):
    t = stmt['type']
    if t in ('Break', 'Continue'):
        return True
    if t in LOOP_TYPES or t == 'Do' or t in ('LocalFunction', 'FunctionStmt'):
        return False
    if t == 'If':
        if stmt_list_contains_own_break_or_continue(stmt['body']):
            return True
        for _, b in stmt['elseifs']:
            if stmt_list_contains_own_break_or_continue(b):
                return True
        if stmt['orelse'] is not None:
            if stmt_list_contains_own_break_or_continue(stmt['orelse']):
                return True
        return False
    return False


def stmt_list_contains_own_break_or_continue(stmts):
    return any(stmt_contains_own_break_or_continue(s) for s in stmts)


def rewrite_break_continue(stmts, flag_var, break_sid, cont_sid):
    out = []
    for s in stmts:
        t = s['type']
        if t == 'Break':
            out.append(N('Assign', targets=[N('Name', name=flag_var)],
                          values=[N('Number', raw=str(break_sid))], op='='))
            out.append(N('Break'))
        elif t == 'Continue':
            out.append(N('Assign', targets=[N('Name', name=flag_var)],
                          values=[N('Number', raw=str(cont_sid))], op='='))
            out.append(N('Break'))
        elif t == 'If':
            s = dict(s)
            s['body'] = rewrite_break_continue(s['body'], flag_var, break_sid, cont_sid)
            s['elseifs'] = [(c, rewrite_break_continue(b, flag_var, break_sid, cont_sid))
                             for c, b in s['elseifs']]
            if s['orelse'] is not None:
                s['orelse'] = rewrite_break_continue(s['orelse'], flag_var, break_sid, cont_sid)
            out.append(N('If', cond=s['cond'], body=s['body'],
                          elseifs=s['elseifs'], orelse=s['orelse']))
        else:
            out.append(s)
    return out


def is_unsafe_stmt_for_flatten(stmt):
    t = stmt['type']
    if t in ('Goto', 'Label'):
        return True
    for child in iter_child_blocks(stmt):
        if contains_goto_or_label(child):
            return True
    return False


def has_mid_block_return(stmts):
    for i, s in enumerate(stmts):
        if s['type'] == 'Return' and i != len(stmts) - 1:
            return True
    return False


def collect_local_names(stmt):
    t = stmt['type']
    if t == 'Local':
        return list(stmt['names'])
    if t == 'LocalFunction':
        return [stmt['name']]
    return []


def stmt_to_non_declaring(stmt):
    t = stmt['type']
    if t == 'Local':
        if not stmt['values']:
            return None
        return N('Assign', targets=[N('Name', name=n) for n in stmt['names']],
                  values=stmt['values'], op='=')
    if t == 'LocalFunction':
        params = list(stmt['params'])
        fexpr = N('FunctionExpr', params=params, vararg=stmt['vararg'], body=stmt['body'])
        return N('Assign', targets=[N('Name', name=stmt['name'])],
                  values=[fexpr], op='=')
    return stmt


MIN_JUNK = 4
MAX_JUNK_MULT = 2


def flatten_block(stmts, ctx, in_loop):
    if len(stmts) < 3:
        return descend_into_children_first(stmts, ctx)

    if contains_goto_or_label(stmts):
        return descend_into_children_first(stmts, ctx)

    if has_mid_block_return(stmts):
        return descend_into_children_first(stmts, ctx)

    has_own_bc = stmt_list_contains_own_break_or_continue(stmts)
    if has_own_bc and not in_loop:
        return descend_into_children_first(stmts, ctx)
    own_break_continue = has_own_bc and in_loop

    stmts = descend_into_children_first(stmts, ctx)

    n = len(stmts)
    if n < 3:
        return stmts

    used = set()
    rng = ctx.rng

    forward_names = []
    for s in stmts:
        forward_names.extend(collect_local_names(s))

    sm_var = ctx.gen()
    flag_var = ctx.gen() if own_break_continue else None

    state_ids = [ctx.sid(used) for _ in range(n)]
    exit_sid = ctx.sid(used)
    break_sid = ctx.sid(used) if own_break_continue else None
    cont_sid = ctx.sid(used) if own_break_continue else None

    case_blocks = []
    for s in stmts:
        nd = stmt_to_non_declaring(s)
        if nd is None:
            case_blocks.append([])
            continue
        if own_break_continue:
            case_blocks.append(rewrite_break_continue([nd], flag_var, break_sid, cont_sid))
        else:
            case_blocks.append([nd])

    sm_name = N('Name', name=sm_var)

    display_order = list(range(n))
    rng.shuffle(display_order)

    def next_state_after(idx):
        if idx + 1 < n:
            return state_ids[idx + 1]
        return exit_sid

    n_junk = max(MIN_JUNK, rng.randint(n, n * MAX_JUNK_MULT))
    junk_sids = [ctx.sid(used) for _ in range(n_junk)]
    junk_var = ctx.gen()

    all_target_sids = state_ids + [exit_sid]

    first_cond = None
    first_body = None
    elseifs = []
    for idx in display_order:
        sid = state_ids[idx]
        nxt = next_state_after(idx)
        blk = list(case_blocks[idx])
        ends_flow = bool(blk) and blk[-1]['type'] in ('Return', 'Break')
        if not ends_flow:
            blk.append(N('Assign', targets=[sm_name],
                          values=[N('Number', raw=str(nxt))], op='='))
        cond = N('Binop', op='==', left=sm_name, right=N('Number', raw=str(sid)))
        if first_cond is None:
            first_cond, first_body = cond, blk
        else:
            elseifs.append((cond, blk))

    for jsid in junk_sids:
        fake_next = rng.choice(all_target_sids)
        junk_val = rng.randint(0, 2**31 - 1)
        cond = N('Binop', op='==', left=sm_name, right=N('Number', raw=str(jsid)))
        blk = [
            N('Local', names=[f"{junk_var}{jsid}"], attribs=[None],
              values=[N('Number', raw=str(junk_val))]),
            N('Assign', targets=[sm_name], values=[N('Number', raw=str(fake_next))], op='='),
        ]
        elseifs.append((cond, blk))

    if_node = N('If', cond=first_cond, body=first_body, elseifs=elseifs, orelse=None)

    result = []
    if forward_names:
        seen = []
        for nm in forward_names:
            if nm not in seen:
                seen.append(nm)
        result.append(N('Local', names=seen, attribs=[None] * len(seen), values=[]))

    if own_break_continue:
        result.append(N('Local', names=[flag_var], attribs=[None], values=[]))

    result.append(N('Local', names=[sm_var], attribs=[None],
                    values=[N('Number', raw=str(state_ids[0]))]))

    while_cond = N('Binop', op='~=', left=sm_name, right=N('Number', raw=str(exit_sid)))
    result.append(N('While', cond=while_cond, body=[if_node]))

    if own_break_continue:
        brk_cond = N('Binop', op='==', left=N('Name', name=flag_var),
                      right=N('Number', raw=str(break_sid)))
        result.append(N('If', cond=brk_cond, body=[N('Break')], elseifs=[], orelse=None))

    return result


def flatten_source(source, rng, gen_name_fn):
    try:
        chunk = parse(source)
    except LuauSyntaxError:
        return None

    ctx = FlattenContext(rng, gen_name_fn)
    try:
        chunk['body'] = flatten_block(chunk['body'], ctx, in_loop=False)
    except Exception:
        return None

    try:
        out = unparse_block(chunk['body'])
    except Exception:
        return None

    return out
