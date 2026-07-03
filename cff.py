BLOCK_OPENERS = {'if', 'while', 'for', 'function', 'do'}
BLOCK_CLOSERS = {'end'}


STMT_START_WORDS = {'if', 'while', 'for', 'function', 'do', 'local',
                     'return', 'break', 'repeat', 'goto'}

BLOCK_OPEN_WORDS = {'if', 'while', 'for', 'function', 'do', 'repeat'}
HEADER_AWAITS_DO = {'for', 'while'}


def split_statements_simple(source):
    n = len(source)
    i = 0
    depth = 0
    paren_depth = 0
    seg_start = 0
    out = []
    seg_has_content = False
    pending_do = 0

    def is_ident_char(ch):
        return ch.isalnum() or ch == '_'

    def peek_word_at(pos):
        j = pos
        while j < n and is_ident_char(source[j]):
            j += 1
        return source[pos:j]

    def flush_before(pos):
        nonlocal seg_start, seg_has_content
        if source[seg_start:pos].strip():
            out.append(source[seg_start:pos])
        seg_start = pos
        seg_has_content = False

    while i < n:
        c = source[i]

        if c == '\n':
            i += 1
            if depth == 0 and paren_depth == 0 and seg_has_content:
                j = i
                while j < n and source[j] in ' \t\r\n':
                    j += 1
                if j < n and source[j] not in ')}]' and not (
                    source[j] == '.' or source[j] == ':' or
                    (j < n and source[j:j+2] in ('..',))
                ):
                    prev_nonspace = source[seg_start:i].rstrip()
                    if not prev_nonspace.endswith((',', '+', '-', '*', '/', '=', 'and', 'or', 'not',
                                                    '(', '{', '[', '..', '<', '>', '~')):
                        flush_before(i)
            continue

        if c in ' \t\r':
            i += 1
            continue

        if c == '-' and i + 1 < n and source[i+1] == '-':
            if i + 3 < n and source[i+2] == '[' and source[i+3] == '[':
                i += 4
                while i < n and not (source[i] == ']' and i+1 < n and source[i+1] == ']'):
                    i += 1
                i += 2
            else:
                while i < n and source[i] != '\n':
                    i += 1
            continue

        if c == '[' and i + 1 < n and source[i+1] in ('[', '='):
            j = i + 1
            eqs = 0
            while j < n and source[j] == '=':
                eqs += 1
                j += 1
            if j < n and source[j] == '[':
                close = ']' + ('=' * eqs) + ']'
                end = source.find(close, j + 1)
                i = (end + len(close)) if end != -1 else n
                seg_has_content = True
                continue

        if c in ('"', "'"):
            q = c
            i += 1
            while i < n and source[i] != q:
                if source[i] == '\\' and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            seg_has_content = True
            continue

        if c in '([{':
            paren_depth += 1
            i += 1
            seg_has_content = True
            continue

        if c in ')]}':
            paren_depth -= 1
            i += 1
            seg_has_content = True
            continue

        if is_ident_char(c) and not c.isdigit():
            word = peek_word_at(i)

            if word in HEADER_AWAITS_DO:
                depth += 1
                pending_do += 1
            elif word == 'do':
                if pending_do > 0:
                    pending_do -= 1
                else:
                    depth += 1
            elif word in ('if', 'function', 'repeat'):
                depth += 1
            elif word == 'until':
                depth -= 1
            elif word == 'end':
                depth -= 1

            i += len(word)
            seg_has_content = True

            if depth == 0 and paren_depth == 0 and word in ('end', 'until'):
                j = i
                if word == 'until':
                    pd = 0
                    while j < n:
                        ch = source[j]
                        if ch == '(':
                            pd += 1
                        elif ch == ')':
                            pd -= 1
                        elif ch == ';' and pd <= 0:
                            j += 1
                            break
                        elif ch == '\n' and pd <= 0:
                            break
                        j += 1
                flush_before(j)
                i = j
            continue

        if c == ';':
            i += 1
            if depth == 0 and paren_depth == 0:
                flush_before(i)
            else:
                seg_has_content = True
            continue

        i += 1
        seg_has_content = True

    if seg_start < n:
        tail = source[seg_start:]
        if tail.strip():
            out.append(tail)

    return [s for s in out if s.strip()]


import re

_NAME_RE = r'[A-Za-z_][A-Za-z0-9_]*'
_LOCAL_DECL_RE = re.compile(
    r'^\s*local\s+(' + _NAME_RE + r'(?:\s*,\s*' + _NAME_RE + r')*)\s*(=)?'
)
_LOCAL_FUNCTION_RE = re.compile(r'^\s*local\s+function\s+' + _NAME_RE)


_LEADING_COMMENT_RE = re.compile(
    r'^(\s*(?:--\[\[.*?\]\]|--[^\n]*\n?))*', re.DOTALL
)


def _strip_leading_comments(stmt):
    m = _LEADING_COMMENT_RE.match(stmt)
    return stmt[m.end():] if m else stmt


def _is_unsafe_statement(stmt):
    stripped = _strip_leading_comments(stmt).strip()
    if stripped.startswith('goto'):
        return True
    if '::' in stripped:
        return True
    return False


def _is_function_statement(stmt):
    stripped = _strip_leading_comments(stmt).strip()
    if _LOCAL_FUNCTION_RE.match(stripped):
        return True
    if stripped.startswith('function'):
        return True
    return False


def _extract_function_name(stmt):
    stripped = _strip_leading_comments(stmt).strip()
    m = _LOCAL_FUNCTION_RE.match(stripped)
    if m:
        m2 = re.match(r'^\s*local\s+function\s+(' + _NAME_RE + r')', stripped)
        return m2.group(1) if m2 else None
    if stripped.startswith('function'):
        m2 = re.match(r'^\s*function\s+(' + _NAME_RE + r')', stripped)
        return m2.group(1) if m2 else None
    return None


def _extract_local_names(stmt):
    stripped = _strip_leading_comments(stmt).strip()
    m = _LOCAL_DECL_RE.match(stripped)
    if not m:
        return None
    names = [x.strip() for x in m.group(1).split(',')]
    return names


def _rewrite_local_function_to_assign(stmt):
    prefix_len = len(stmt) - len(_strip_leading_comments(stmt))
    comment_part = stmt[:prefix_len]
    rest = stmt[prefix_len:]
    m = re.match(r'^(\s*)local(\s+)function(\s+)(' + _NAME_RE + r')', rest)
    if not m:
        return stmt
    name = m.group(4)
    before = rest[:m.start()]
    after_name_end = m.end()
    rewritten = (before + m.group(1) +
                 (' ' * (len('local') + len(m.group(2)) + len('function') + len(m.group(3)))) +
                 name + ' = function' + rest[after_name_end:])
    return comment_part + rewritten


def _rewrite_local_to_assign(stmt):
    prefix_len = len(stmt) - len(_strip_leading_comments(stmt))
    comment_part = stmt[:prefix_len]
    rest = stmt[prefix_len:]
    m = _LOCAL_DECL_RE.match(rest)
    if not m:
        return stmt
    has_eq = m.group(2) is not None
    local_pos = rest.index('local', m.start(), m.end())
    if has_eq:
        rewritten = (rest[:local_pos] + (' ' * 5) +
                     rest[local_pos + 5:m.end()] + rest[m.end():])
        return comment_part + rewritten
    return comment_part


def can_flatten(source):
    stmts = split_statements_simple(source)
    if len(stmts) < 3:
        return False
    if ''.join(stmts) != source:
        return False
    for s in stmts:
        if _is_unsafe_statement(s):
            return False
    return True


def flatten_top_level(source, rng, gen_name_fn):
    if not can_flatten(source):
        return source

    raw_stmts = [s for s in split_statements_simple(source) if s.strip()]
    n_stmts = len(raw_stmts)

    forward_names = []
    stmts = []
    has_top_return = False
    for s in raw_stmts:
        stripped = s.strip()
        if stripped.startswith('return'):
            has_top_return = True
        stripped_nc = _strip_leading_comments(s).strip()
        if _LOCAL_FUNCTION_RE.match(stripped_nc):
            fname = _extract_function_name(s)
            if fname is not None:
                forward_names.append(fname)
                stmts.append(_rewrite_local_function_to_assign(s))
            else:
                stmts.append(s)
            continue
        names = _extract_local_names(s)
        if names is not None:
            forward_names.extend(names)
            stmts.append(_rewrite_local_to_assign(s))
        else:
            stmts.append(s)

    if has_top_return:
        return source

    order = list(range(n_stmts))

    used = set()

    def new_sid():
        while True:
            sid = rng.randint(100000, 999999)
            if sid not in used:
                used.add(sid)
                return sid

    state_ids = {idx: new_sid() for idx in range(n_stmts)}
    exit_sid = new_sid()

    n_junk = rng.randint(4, 9)
    junk_sids = [new_sid() for _ in range(n_junk)]

    def next_state_after(pos):
        if pos + 1 < n_stmts:
            return state_ids[order[pos + 1]]
        return exit_sid

    sm_var = gen_name_fn()
    junk_var_prefix = gen_name_fn()

    branches = []
    for pos, idx in enumerate(order):
        sid = state_ids[idx]
        nxt = next_state_after(pos)
        branches.append((sid, stmts[idx], nxt))

    rng.shuffle(branches)

    lines = []
    if forward_names:
        seen = []
        for nm in forward_names:
            if nm not in seen:
                seen.append(nm)
        lines.append(f"local {','.join(seen)} ")
    lines.append(f"local {sm_var}={state_ids[order[0]]} ")
    lines.append(f"while {sm_var}~={exit_sid} do ")

    first = True
    for sid, stmt_text, nxt in branches:
        kw = "if" if first else "elseif"
        first = False
        lines.append(f"{kw} {sm_var}=={sid} then ")
        lines.append(stmt_text)
        lines.append(f" {sm_var}={nxt} ")

    for jsid in junk_sids:
        fake_target_pool = [state_ids[i] for i in range(n_stmts)] + [exit_sid]
        fake_next = rng.choice(fake_target_pool)
        junk_val = rng.randint(0, 2**31 - 1)
        lines.append(f"elseif {sm_var}=={jsid} then ")
        lines.append(f"local {junk_var_prefix}{jsid}={junk_val} ")
        if rng.random() < 0.5:
            lines.append(f"if {junk_var_prefix}{jsid}=={junk_val + 1} then {sm_var}={fake_next} else {sm_var}={fake_next} end ")
        else:
            lines.append(f"{sm_var}={fake_next} ")

    lines.append("else break end ")
    lines.append("end ")

    return "".join(lines)
  
