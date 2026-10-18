import random
import string
import secrets
from crypto import CHACHA_CONST, CHACHA_ROUNDS, MASK32

_used_names = set()
_name_rng = None

_CONFUSABLES = ["l", "I", "O", "o", "0", "1"]
_LUA_KEYWORDS = {
    'and','break','continue','do','else','elseif','end','false','for','function',
    'if','in','local','nil','not','or','repeat','return','then','true',
    'until','while',
}

def reset_names():
    global _used_names, _name_rng
    _used_names = set()
    _name_rng = random.Random(secrets.randbits(128))

def gen_name(rng=None):
    r = rng or _name_rng or random
    while True:
        length = r.randint(3, 5)
        first = r.choice(string.ascii_letters + "_")
        rest = "".join(r.choice(_CONFUSABLES) for _ in range(length - 1))
        name = first + rest
        if name not in _used_names and name not in _LUA_KEYWORDS:
            _used_names.add(name)
            return name

DEFLATE_LEN_BASE = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
DEFLATE_LEN_EXTRA = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0]
DEFLATE_DIST_BASE = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
DEFLATE_DIST_EXTRA = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13]
DEFLATE_CLEN_ORDER = [16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]

def deflate_tables_blob():
    segs = [DEFLATE_LEN_BASE, DEFLATE_LEN_EXTRA, DEFLATE_DIST_BASE, DEFLATE_DIST_EXTRA, DEFLATE_CLEN_ORDER]
    return ";".join(",".join(str(v) for v in seg) for seg in segs)

def build_inflate_runtime():
    band, bor = "bit32.band", "bit32.bor"
    lshift, rshift = "bit32.lshift", "bit32.rshift"

    names = {}
    for key in (
        "reader", "getbit", "getbits", "construct", "decodesym", "inflateblock",
        "inflatedynamic", "inflatestored", "inflatemain", "buildfixed",
        "fixedlit", "fixeddist", "lenbase", "lenextra", "distbase", "distextra",
        "clenorder", "r1", "bval", "n1", "i1", "count1", "sym1", "offs1", "len1",
        "symbol1", "h1", "code1", "first1", "index1", "cnt1", "len2", "out1",
        "littree1", "disttree1", "sym2", "idx1", "length1", "dsym1", "dist1",
        "start1", "i2", "litlen1", "i3", "dist2", "i4", "hlit1", "hdist1",
        "hclen1", "clenlen1", "i5", "clentree1", "lengths1", "n2", "sym3",
        "rep1", "prev1", "i6", "litlen2", "i7", "distlen1", "i8", "littree2",
        "disttree2", "data1", "out2", "len3", "i9", "bfinal1", "btype1", "out3",
        "fl1", "fd1", "data2", "splitv", "ssep", "sres", "spos", "sidx",
        "parsetables", "pblob", "psegs", "pout", "pi", "pnums", "parr", "pj",
    ):
        names[key] = gen_name()

    n = names

    src = (
        f"local function {n['getbit']}({n['r1']}) "
        f"if {n['r1']}.n==0 then {n['r1']}.b={n['r1']}.d[{n['r1']}.p] {n['r1']}.p={n['r1']}.p+1 {n['r1']}.n=8 end "
        f"local {n['bval']}={band}({n['r1']}.b,1) {n['r1']}.b={rshift}({n['r1']}.b,1) {n['r1']}.n={n['r1']}.n-1 "
        f"return {n['bval']} end "
        f"local function {n['getbits']}({n['r1']},{n['n1']}) "
        f"local {n['bval']}=0 "
        f"for {n['i1']}=0,{n['n1']}-1,1 do {n['bval']}={bor}({n['bval']},{lshift}({n['getbit']}({n['r1']}),{n['i1']})) end "
        f"return {n['bval']} end "
        f"local function {n['construct']}({n['len1']},{n['n1']}) "
        f"local {n['count1']}={{}} for {n['i1']}=0,15,1 do {n['count1']}[{n['i1']}]=0 end "
        f"for {n['sym1']}=1,{n['n1']},1 do {n['count1']}[{n['len1']}[{n['sym1']}]]={n['count1']}[{n['len1']}[{n['sym1']}]]+1 end "
        f"{n['count1']}[0]=0 "
        f"local {n['offs1']}={{}} {n['offs1']}[1]=0 "
        f"for {n['i1']}=1,14,1 do {n['offs1']}[{n['i1']}+1]={n['offs1']}[{n['i1']}]+{n['count1']}[{n['i1']}] end "
        f"local {n['symbol1']}={{}} "
        f"for {n['sym1']}=1,{n['n1']},1 do "
        f"local {n['len2']}={n['len1']}[{n['sym1']}] "
        f"if {n['len2']}~=0 then {n['offs1']}[{n['len2']}]={n['offs1']}[{n['len2']}]+1 {n['symbol1']}[{n['offs1']}[{n['len2']}]]={n['sym1']}-1 end "
        f"end "
        f"return {{count={n['count1']},symbol={n['symbol1']}}} end "
        f"local function {n['decodesym']}({n['r1']},{n['h1']}) "
        f"local {n['code1']}=0 local {n['first1']}=0 local {n['index1']}=0 "
        f"for {n['len2']}=1,15,1 do "
        f"{n['code1']}={bor}({n['code1']},{n['getbit']}({n['r1']})) "
        f"local {n['cnt1']}={n['h1']}.count[{n['len2']}] "
        f"if {n['code1']}-{n['first1']}<{n['cnt1']} then return {n['h1']}.symbol[{n['index1']}+({n['code1']}-{n['first1']})+1] end "
        f"{n['index1']}={n['index1']}+{n['cnt1']} {n['first1']}={n['first1']}+{n['cnt1']} "
        f"{n['first1']}={lshift}({n['first1']},1) {n['code1']}={lshift}({n['code1']},1) "
        f"end "
        f"error('',0) end "
        f"local {n['lenbase']} local {n['lenextra']} local {n['distbase']} local {n['distextra']} local {n['clenorder']} "
        f"local function {n['splitv']}({n['pblob']},{n['ssep']}) "
        f"local {n['sres']}={{}} local {n['spos']}=1 "
        f"while true do "
        f"local {n['sidx']}=string.find({n['pblob']},{n['ssep']},{n['spos']},true) "
        f"if not {n['sidx']} then {n['sres']}[#{n['sres']}+1]=string.sub({n['pblob']},{n['spos']}) break end "
        f"{n['sres']}[#{n['sres']}+1]=string.sub({n['pblob']},{n['spos']},{n['sidx']}-1) {n['spos']}={n['sidx']}+1 "
        f"end return {n['sres']} end "
        f"local function {n['parsetables']}({n['pblob']}) "
        f"local {n['psegs']}={n['splitv']}({n['pblob']},';') "
        f"local {n['pout']}={{}} "
        f"for {n['pi']}=1,#{n['psegs']},1 do "
        f"local {n['pnums']}={n['splitv']}({n['psegs']}[{n['pi']}],',') "
        f"local {n['parr']}={{}} "
        f"for {n['pj']}=1,#{n['pnums']},1 do {n['parr']}[{n['pj']}]=tonumber({n['pnums']}[{n['pj']}]) end "
        f"{n['pout']}[{n['pi']}]={n['parr']} end "
        f"return {n['pout']} end "
        f"local function {n['inflateblock']}({n['r1']},{n['out1']},{n['littree1']},{n['disttree1']}) "
        f"while true do "
        f"local {n['sym2']}={n['decodesym']}({n['r1']},{n['littree1']}) "
        f"if {n['sym2']}<256 then {n['out1']}[#{n['out1']}+1]={n['sym2']} "
        f"elseif {n['sym2']}==256 then return "
        f"else "
        f"local {n['idx1']}={n['sym2']}-257 "
        f"local {n['length1']}={n['lenbase']}[{n['idx1']}+1]+{n['getbits']}({n['r1']},{n['lenextra']}[{n['idx1']}+1]) "
        f"local {n['dsym1']}={n['decodesym']}({n['r1']},{n['disttree1']}) "
        f"local {n['dist1']}={n['distbase']}[{n['dsym1']}+1]+{n['getbits']}({n['r1']},{n['distextra']}[{n['dsym1']}+1]) "
        f"local {n['start1']}=#{n['out1']}-{n['dist1']}+1 "
        f"for {n['i2']}=0,{n['length1']}-1,1 do {n['out1']}[#{n['out1']}+1]={n['out1']}[{n['start1']}+{n['i2']}] end "
        f"end end end "
        f"local function {n['inflatedynamic']}({n['r1']},{n['out1']}) "
        f"local {n['hlit1']}={n['getbits']}({n['r1']},5)+257 "
        f"local {n['hdist1']}={n['getbits']}({n['r1']},5)+1 "
        f"local {n['hclen1']}={n['getbits']}({n['r1']},4)+4 "
        f"local {n['clenlen1']}={{}} for {n['i3']}=1,19,1 do {n['clenlen1']}[{n['i3']}]=0 end "
        f"for {n['i3']}=1,{n['hclen1']},1 do {n['clenlen1']}[{n['clenorder']}[{n['i3']}]+1]={n['getbits']}({n['r1']},3) end "
        f"local {n['clentree1']}={n['construct']}({n['clenlen1']},19) "
        f"local {n['lengths1']}={{}} local {n['n2']}=0 "
        f"while {n['n2']}<{n['hlit1']}+{n['hdist1']} do "
        f"local {n['sym3']}={n['decodesym']}({n['r1']},{n['clentree1']}) "
        f"if {n['sym3']}<16 then {n['n2']}={n['n2']}+1 {n['lengths1']}[{n['n2']}]={n['sym3']} "
        f"elseif {n['sym3']}==16 then "
        f"local {n['rep1']}={n['getbits']}({n['r1']},2)+3 local {n['prev1']}={n['lengths1']}[{n['n2']}] "
        f"for {n['i4']}=1,{n['rep1']},1 do {n['n2']}={n['n2']}+1 {n['lengths1']}[{n['n2']}]={n['prev1']} end "
        f"elseif {n['sym3']}==17 then "
        f"local {n['rep1']}={n['getbits']}({n['r1']},3)+3 "
        f"for {n['i4']}=1,{n['rep1']},1 do {n['n2']}={n['n2']}+1 {n['lengths1']}[{n['n2']}]=0 end "
        f"else "
        f"local {n['rep1']}={n['getbits']}({n['r1']},7)+11 "
        f"for {n['i4']}=1,{n['rep1']},1 do {n['n2']}={n['n2']}+1 {n['lengths1']}[{n['n2']}]=0 end "
        f"end end "
        f"local {n['litlen1']}={{}} for {n['i3']}=1,{n['hlit1']},1 do {n['litlen1']}[{n['i3']}]={n['lengths1']}[{n['i3']}] end "
        f"local {n['distlen1']}={{}} for {n['i3']}=1,{n['hdist1']},1 do {n['distlen1']}[{n['i3']}]={n['lengths1']}[{n['hlit1']}+{n['i3']}] end "
        f"local {n['littree2']}={n['construct']}({n['litlen1']},{n['hlit1']}) "
        f"local {n['disttree2']}={n['construct']}({n['distlen1']},{n['hdist1']}) "
        f"{n['inflateblock']}({n['r1']},{n['out1']},{n['littree2']},{n['disttree2']}) end "
        f"local function {n['inflatestored']}({n['r1']},{n['out1']}) "
        f"{n['r1']}.b=0 {n['r1']}.n=0 "
        f"local {n['len3']}={n['r1']}.d[{n['r1']}.p]+{n['r1']}.d[{n['r1']}.p+1]*256 "
        f"{n['r1']}.p={n['r1']}.p+4 "
        f"for {n['i9']}=0,{n['len3']}-1,1 do {n['out1']}[#{n['out1']}+1]={n['r1']}.d[{n['r1']}.p+{n['i9']}] end "
        f"{n['r1']}.p={n['r1']}.p+{n['len3']} end "
        f"local function {n['buildfixed']}() "
        f"local {n['litlen2']}={{}} "
        f"for {n['i6']}=1,144,1 do {n['litlen2']}[{n['i6']}]=8 end "
        f"for {n['i6']}=145,256,1 do {n['litlen2']}[{n['i6']}]=9 end "
        f"for {n['i6']}=257,280,1 do {n['litlen2']}[{n['i6']}]=7 end "
        f"for {n['i6']}=281,288,1 do {n['litlen2']}[{n['i6']}]=8 end "
        f"local {n['dist2']}={{}} for {n['i7']}=1,30,1 do {n['dist2']}[{n['i7']}]=5 end "
        f"return {n['construct']}({n['litlen2']},288),{n['construct']}({n['dist2']},30) end "
        f"local {n['fixedlit']},{n['fixeddist']}={n['buildfixed']}() "
        f"local function {n['inflatemain']}({n['data2']}) "
        f"local {n['r1']}={{d={n['data2']},p=1,b=0,n=0}} "
        f"local {n['out3']}={{}} "
        f"while true do "
        f"local {n['bfinal1']}={n['getbit']}({n['r1']}) "
        f"local {n['btype1']}={n['getbits']}({n['r1']},2) "
        f"if {n['btype1']}==0 then {n['inflatestored']}({n['r1']},{n['out3']}) "
        f"elseif {n['btype1']}==1 then {n['inflateblock']}({n['r1']},{n['out3']},{n['fixedlit']},{n['fixeddist']}) "
        f"elseif {n['btype1']}==2 then {n['inflatedynamic']}({n['r1']},{n['out3']}) "
        f"else error('',0) end "
        f"if {n['bfinal1']}==1 then break end end "
        f"return {n['out3']} end "
    )
    table_info = {
        "lenbase": n['lenbase'],
        "lenextra": n['lenextra'],
        "distbase": n['distbase'],
        "distextra": n['distextra'],
        "clenorder": n['clenorder'],
        "parsetables": n['parsetables'],
    }
    return src, n['inflatemain'], table_info

def build_runtime_header(seeds, var_k, var_Q, var_G, var_B, var_f, var_V, wm_var):
    inflate_src, inflate_fn_v, inflate_tables = build_inflate_runtime()
    flag_v  = gen_name()
    body_v  = gen_name()
    bi_v    = gen_name()
    decv_v  = gen_name()
    chars_v = gen_name()
    ci2_v   = gen_name()
    qr_v    = gen_name()
    blk_v   = gen_name()
    ks_v    = gen_name()
    shuffle = gen_name()
    alpha_v = gen_name()
    N_v     = gen_name()
    RA_v    = gen_name()
    g3      = gen_name()
    xorb_v  = gen_name()
    CC_v    = gen_name()
    sb      = gen_name()
    sc      = gen_name()
    key_v   = gen_name()
    nb_v    = gen_name()
    w_v     = gen_name()
    st_v    = gen_name()
    floor_v = gen_name()
    outw_v  = gen_name()
    outks_v = gen_name()
    cnt_v   = gen_name()
    pos_v   = gen_name()
    words_v = gen_name()
    wv_v    = gen_name()
    ci_v    = gen_name()
    anw_v   = gen_name()
    ksh_v   = gen_name()
    base_v  = gen_name()
    valv_v  = gen_name()
    jv_v    = gen_name()
    iw_v    = gen_name()
    iout_v  = gen_name()
    iks_v   = gen_name()
    ishuf_v = gen_name()
    ishuf2_v = gen_name()
    al_v    = gen_name()
    hh_v    = gen_name()
    ll_v    = gen_name()
    kk_v    = gen_name()
    cc_v    = gen_name()
    dd_v    = gen_name()
    ig3_v   = gen_name()
    ck_v    = gen_name()
    nwords_v = gen_name()
    nlo_v   = gen_name()
    nhi_v   = gen_name()
    nv_v    = gen_name()
    lu_v    = gen_name()
    ri_v    = gen_name()
    par_a   = gen_name()
    par_b   = gen_name()
    par_c   = gen_name()
    par_d   = gen_name()
    par_counter = gen_name()
    par_n1  = gen_name()
    par_n2  = gen_name()
    par_n3  = gen_name()
    par_outlen = gen_name()
    par_ga  = gen_name()
    par_ka_a  = gen_name()
    par_ka_b1 = gen_name()
    par_ka_b2 = gen_name()
    par_ka_b3 = gen_name()
    par_ka_b4 = gen_name()
    par_ka_d1 = gen_name()
    par_ka_d2 = gen_name()
    result_v  = gen_name()
    wm_q_v    = gen_name()

    key = seeds["KEY"]
    nonce_base = seeds["NONCE_BASE"]
    c0, c1, c2, c3 = seeds.get("CC", CHACHA_CONST)
    rot1, rot2, rot3, rot4 = seeds.get("ROT", (16, 12, 8, 7))

    band   = "bit32.band"
    bxor   = "bit32.bxor"
    lrot   = "bit32.lrotate"
    bor    = "bit32.bor"
    lshift = "bit32.lshift"
    rshift = "bit32.rshift"

    key_rng = random.Random(secrets.randbits(64))

    drv_v = gen_name()
    drv_acc_v = gen_name()
    drv_tick_v = gen_name()
    drv_salt_v = gen_name()
    drv_seed = key_rng.randint(0, MASK32)
    drv_mix  = key_rng.randint(0, MASK32) | 1

    drv_prologue = (
        f"local {drv_acc_v}={drv_seed} local {drv_tick_v}=0 "
        f"local function {drv_v}({drv_salt_v}) "
        f"{drv_tick_v}=({drv_tick_v}+1)%4294967296 "
        f"{drv_acc_v}={bxor}(({drv_acc_v}+{drv_salt_v}+{drv_tick_v}+{drv_mix})%4294967296,{lrot}({drv_acc_v},7)) "
        f"return {drv_acc_v} end "
    )

    drv_state = {"acc": drv_seed, "tick": 0}

    def drv_predict(salt):
        drv_state["tick"] = (drv_state["tick"] + 1) & MASK32
        old_acc = drv_state["acc"]
        left = (old_acc + salt + drv_state["tick"] + drv_mix) & MASK32
        rot = ((old_acc << 7) | (old_acc >> 25)) & MASK32
        new_acc = left ^ rot
        drv_state["acc"] = new_acc
        return new_acc

    def scatter_value(value, rot_pool):
        n_parts = key_rng.randint(4, 7)
        use_xor_terms = key_rng.random() < 0.5
        shares = [key_rng.randint(0, MASK32) for _ in range(n_parts - 1)]
        if use_xor_terms:
            acc = 0
            for s in shares:
                acc ^= s
            last = acc ^ value
        else:
            acc = 0
            for s in shares:
                acc = (acc + s) & MASK32
            last = (value - acc) & MASK32
        shares.append(last)
        key_rng.shuffle(shares)

        names = [gen_name() for _ in shares]
        decls = []
        drv_idx = key_rng.randrange(len(shares))
        for i, (nm, sv) in enumerate(zip(names, shares)):
            if i == drv_idx and i != 0:
                salt = key_rng.randint(0, MASK32)
                output = drv_predict(salt)
                if use_xor_terms:
                    fixup = output ^ sv
                    decls.append(f"local {nm}={bxor}({drv_v}({salt}),{fixup}) ")
                else:
                    fixup = (sv - output) & MASK32
                    decls.append(f"local {nm}=({drv_v}({salt})+{fixup})%4294967296 ")
                continue
            mode = key_rng.randint(0, 2)
            if mode == 0 or i == 0:
                decls.append(f"local {nm}={sv} ")
            elif mode == 1:
                pre = (sv ^ key_rng.randint(0, MASK32)) & MASK32
                mask = pre ^ sv
                decls.append(f"local {nm}={bxor}({pre},{mask}) ")
            else:
                prev = names[i - 1]
                delta = (sv - rot_pool.get(prev, 0)) & MASK32
                rot_pool[nm] = sv
                decls.append(f"local {nm}=({delta}+{rot_pool.get(prev, 0)})%4294967296 ")
                rot_pool[prev] = rot_pool.get(prev, 0)

        if use_xor_terms:
            combine = names[0]
            for nm in names[1:]:
                combine = f"{bxor}({combine},{nm})"
        else:
            combine_terms = "+".join(names)
            combine = f"({combine_terms})%4294967296"
        return "".join(decls), combine

    rot_pool = {}
    key_field_exprs = []

    decoy_pool = []

    def make_decoy():
        dn = gen_name()
        if key_rng.random() < 0.35:
            salt = key_rng.randint(0, MASK32)
            target = key_rng.randint(0, MASK32)
            output = drv_predict(salt)
            fixup = (target - output) & MASK32
            line = f"local {dn}=({drv_v}({salt})+{fixup})%4294967296 "
        else:
            line = f"local {dn}={key_rng.randint(0, MASK32)} "
        decoy_pool.append(dn)
        return line

    def make_decoy_sink():
        if len(decoy_pool) < 2:
            return ""
        a, b = key_rng.sample(decoy_pool, 2)
        sv = gen_name()
        never = key_rng.randint(1, MASK32 - 1)
        guard = (never + 1) & MASK32
        return f"local {sv}=({bxor}({a},{b})+{never})%4294967296 if {sv}=={guard} then error(\"integrity\") end "

    interleaved = []
    for val in key[:-1]:
        n_here = key_rng.randint(0, 2)
        for _ in range(n_here):
            interleaved.append(make_decoy())
            if key_rng.random() < 0.6:
                interleaved.append(make_decoy_sink())
        decl, expr = scatter_value(val, rot_pool)
        interleaved.append(decl)
        key_field_exprs.append(expr)

    def scatter_value_standalone(value):
        n_parts = key_rng.randint(4, 7)
        use_xor_terms = key_rng.random() < 0.5
        shares = [key_rng.randint(0, MASK32) for _ in range(n_parts - 1)]
        if use_xor_terms:
            acc = 0
            for s in shares:
                acc ^= s
            last = acc ^ value
        else:
            acc = 0
            for s in shares:
                acc = (acc + s) & MASK32
            last = (value - acc) & MASK32
        shares.append(last)
        key_rng.shuffle(shares)

        names = [gen_name() for _ in shares]
        decls = []
        for i, (nm, sv) in enumerate(zip(names, shares)):
            mode = key_rng.randint(0, 1)
            if mode == 0:
                decls.append(f"local {nm}={sv} ")
            else:
                pre = (sv ^ key_rng.randint(0, MASK32)) & MASK32
                mask = pre ^ sv
                decls.append(f"local {nm}={bxor}({pre},{mask}) ")

        if use_xor_terms:
            combine = names[0]
            for nm in names[1:]:
                combine = f"{bxor}({combine},{nm})"
        else:
            combine_terms = "+".join(names)
            combine = f"({combine_terms})%4294967296"
        return "".join(decls), combine

    boot_last_val = key[-1]
    boot_decl, boot_expr = scatter_value_standalone(boot_last_val)

    boot_src = f"{boot_decl}return {boot_expr}"

    boot_cipher_shift = key_rng.randint(1, 250)
    boot_cipher_bytes = bytes((b + boot_cipher_shift) % 256 for b in boot_src.encode("utf-8"))
    boot_cipher_literal = ",".join(str(b) for b in boot_cipher_bytes)

    boot_ls_v   = gen_name()
    boot_buf_v  = gen_name()
    boot_i_v    = gen_name()
    boot_fn_v   = gen_name()
    boot_err_v  = gen_name()
    boot_bytes_v = gen_name()

    boot_loader = (
        f"local {boot_ls_v}=loadstring or load "
        f"if type({boot_ls_v})~='function' then error('',0) end "
        f"if debug and debug.info and(debug.info({boot_ls_v},'s')~='[C]' or debug.info({boot_ls_v},'l')~=-1) then error('',0) end "
        f"if debug and debug.getinfo and debug.getinfo({boot_ls_v}).what~='C' then error('',0) end "
        f"if (islclosure and islclosure({boot_ls_v})) or (is_synapse_function and is_synapse_function({boot_ls_v})) then error('',0) end "
        f"local {boot_bytes_v}={{{boot_cipher_literal}}} "
        f"local {boot_buf_v}={{}} "
        f"for {boot_i_v}=1,#{boot_bytes_v},1 do {boot_buf_v}[{boot_i_v}]={sc}(({boot_bytes_v}[{boot_i_v}]-{boot_cipher_shift})%256) end "
        f"local {boot_fn_v},{boot_err_v}={boot_ls_v}(table.concat({boot_buf_v})) "
        f"{boot_bytes_v}=nil {boot_buf_v}=nil "
        f"if not {boot_fn_v} then error({boot_err_v} or '',0) end "
    )

    boot_result_v = gen_name()
    boot_call = f"local {boot_result_v}={boot_fn_v}() "

    key_field_exprs.append(boot_result_v)
    n_trailing = key_rng.randint(2, 6)
    for _ in range(n_trailing):
        interleaved.append(make_decoy())

    key_field_decls = "".join(interleaved)

    key_table_decl = f"local {key_v}={{{','.join(key_field_exprs)}}} "

    nb_decl_body, nb_expr = scatter_value(nonce_base, rot_pool)
    nb_decl = f"{nb_decl_body}local {nb_v}={nb_expr} "

    return (
        f'do ("Protected by Melotens Weak Obfuscator."):gsub(".+",function({wm_q_v}){wm_var}={wm_q_v} end) end '
        f"return (function(...) return(function({var_Q},{var_G},{var_B},{var_f},{var_k},{var_V}) "
        f"{drv_prologue}"
        f"{key_field_decls}"
        f"local {sc}=string.char "
        f"{boot_loader}"
        f"{boot_call}"
        f"{key_table_decl}"
        f"{nb_decl}"
        f"local {floor_v}=math.floor local {sb}=string.byte local {sc}=string.char "
        f"local function {xorb_v}({par_a},{par_b}) return {bxor}({par_a},{par_b}) end "
        f"local function {qr_v}({st_v},{par_a},{par_b},{par_c},{par_d}) "
        f"{st_v}[{par_a}]=({st_v}[{par_a}]+{st_v}[{par_b}])%4294967296 "
        f"{st_v}[{par_d}]={lrot}({xorb_v}({st_v}[{par_d}],{st_v}[{par_a}]),{rot1}) "
        f"{st_v}[{par_c}]=({st_v}[{par_c}]+{st_v}[{par_d}])%4294967296 "
        f"{st_v}[{par_b}]={lrot}({xorb_v}({st_v}[{par_b}],{st_v}[{par_c}]),{rot2}) "
        f"{st_v}[{par_a}]=({st_v}[{par_a}]+{st_v}[{par_b}])%4294967296 "
        f"{st_v}[{par_d}]={lrot}({xorb_v}({st_v}[{par_d}],{st_v}[{par_a}]),{rot3}) "
        f"{st_v}[{par_c}]=({st_v}[{par_c}]+{st_v}[{par_d}])%4294967296 "
        f"{st_v}[{par_b}]={lrot}({xorb_v}({st_v}[{par_b}],{st_v}[{par_c}]),{rot4}) "
        f"end "
        f"local function {blk_v}({par_counter},{par_n1},{par_n2},{par_n3}) "
        f"local {st_v}={{{c0},{c1},{c2},{c3},"
        f"{key_v}[1],{key_v}[2],{key_v}[3],{key_v}[4],{key_v}[5],{key_v}[6],{key_v}[7],{key_v}[8],"
        f"{par_counter},{par_n1},{par_n2},{par_n3}}} "
        f"local {w_v}={{}} for {iw_v}=1,16,1 do {w_v}[{iw_v}]={st_v}[{iw_v}] end "
        f"for {lu_v}=1,{CHACHA_ROUNDS // 2},1 do "
        f"{qr_v}({w_v},1,5,9,13) {qr_v}({w_v},2,6,10,14) {qr_v}({w_v},3,7,11,15) {qr_v}({w_v},4,8,12,16) "
        f"{qr_v}({w_v},1,6,11,16) {qr_v}({w_v},2,7,12,13) {qr_v}({w_v},3,8,9,14) {qr_v}({w_v},4,5,10,15) "
        f"end "
        f"local {outw_v}={{}} for {iout_v}=1,16,1 do {outw_v}[{iout_v}]=({w_v}[{iout_v}]+{st_v}[{iout_v}])%4294967296 end "
        f"return {outw_v} end "
        f"local function {ks_v}({par_n1},{par_n2},{par_outlen}) "
        f"local {outks_v}={{}} local {cnt_v}=0 local {pos_v}=0 "
        f"while {pos_v}<{par_outlen} do "
        f"local {words_v}={blk_v}({cnt_v},0,{par_n1},{par_n2}) "
        f"for {iks_v}=1,16,1 do "
        f"local {wv_v}={words_v}[{iks_v}] "
        f"{outks_v}[{pos_v}+1]={wv_v}%256 "
        f"{outks_v}[{pos_v}+2]={floor_v}({wv_v}/256)%256 "
        f"{outks_v}[{pos_v}+3]={floor_v}({wv_v}/65536)%256 "
        f"{outks_v}[{pos_v}+4]={floor_v}({wv_v}/16777216)%256 "
        f"{pos_v}={pos_v}+4 "
        f"if {pos_v}>={par_outlen} then break end "
        f"end "
        f"{cnt_v}=({cnt_v}+1)%4294967296 "
        f"end "
        f"return {outks_v} end "
        f"local function {shuffle}() "
        f"local {ci_v}={{}} for {ishuf_v}=33,126,1 do if {ishuf_v}~=34 and({ishuf_v}~=39 and {ishuf_v}~=92) then {ci_v}[#{ci_v}+1]=string.char({ishuf_v}) end end "
        f"local {anw_v}={blk_v}(2779096485,{nb_v},3266489909,2654435769) "
        f"local {ksh_v}={ks_v}({anw_v}[1],{anw_v}[2],#{ci_v}*4) "
        f"for {ishuf2_v}=#{ci_v},2,-1 do "
        f"local {base_v}=({ishuf2_v}-1)*4 "
        f"local {valv_v}={ksh_v}[{base_v}+1]+{ksh_v}[{base_v}+2]*256+{ksh_v}[{base_v}+3]*65536+{ksh_v}[{base_v}+4]*16777216 "
        f"local {jv_v}={valv_v}%{ishuf2_v}+1 "
        f"{ci_v}[{ishuf2_v}],{ci_v}[{jv_v}]={ci_v}[{jv_v}],{ci_v}[{ishuf2_v}] "
        f"end "
        f"return table.concat({ci_v}) end "
        f"local {alpha_v}={shuffle}() "
        f"local {N_v}=#{alpha_v} "
        f"local {RA_v}={{}} "
        f"for {ri_v}=1,{N_v},1 do {RA_v}[{sb}({alpha_v},{ri_v})]={ri_v} end "
        f"local function {g3}({par_ga}) "
        f"if type({par_ga})~='string' then return nil end "
        f"local {al_v}=#{par_ga} "
        f"local {hh_v}=0 local {ll_v}=0 local {kk_v}=-1 "
        f"local {ig3_v}={{}} "
        f"for {iw_v}=1,{al_v},1 do "
        f"local {cc_v}={RA_v}[{sb}({par_ga},{iw_v})] "
        f"if not {cc_v} then return nil end "
        f"{cc_v}={cc_v}-1 "
        f"if {kk_v}<0 then {kk_v}={cc_v} else "
        f"{kk_v}={kk_v}+{cc_v}*91 "
        f"{hh_v}={bor}({hh_v},{lshift}({kk_v},{ll_v})) "
        f"if {band}({kk_v},8191)>88 then {ll_v}={ll_v}+13 else {ll_v}={ll_v}+14 end "
        f"while {ll_v}>=8 do "
        f"{ig3_v}[#{ig3_v}+1]={band}({hh_v},255) "
        f"{hh_v}={rshift}({hh_v},8) "
        f"{ll_v}={ll_v}-8 "
        f"end "
        f"{kk_v}=-1 "
        f"end end "
        f"if {kk_v}>=0 then {ig3_v}[#{ig3_v}+1]={band}({bor}({hh_v},{lshift}({kk_v},{ll_v})),255) end "
        f"return {ig3_v} end "
        f"{inflate_src}"
        f"local {CC_v}={{}} "
        f"{var_k}=function({par_ka_a},{par_ka_b1},{par_ka_b2},{par_ka_b3},{par_ka_b4},{par_ka_d1},{par_ka_d2}) local {ck_v}={par_ka_b3}*{seeds['MK']}+{par_ka_b1} if {CC_v}[{ck_v}]~=nil then return {CC_v}[{ck_v}] end "
        f"local {dd_v}={g3}({par_ka_a}) if not {dd_v} then return nil end "
        f"local {nwords_v}={blk_v}({par_ka_b3}%4294967296,{nb_v},3266489909,2654435769) "
        f"local {nlo_v}={nwords_v}[1] local {nhi_v}={nwords_v}[2] "
        f"local {ksh_v}={ks_v}({nlo_v},{nhi_v},#{dd_v}) "
        f"local {ig3_v}={{}} for {iw_v}=1,#{dd_v},1 do {ig3_v}[{iw_v}]={xorb_v}({dd_v}[{iw_v}],{ksh_v}[{iw_v}])%256 end "
        f"local {flag_v}={ig3_v}[1] "
        f"local {body_v}={{}} for {bi_v}=2,#{ig3_v},1 do {body_v}[{bi_v}-1]={ig3_v}[{bi_v}] end "
        f"local {decv_v} if {flag_v}==1 then {decv_v}={inflate_fn_v}({body_v}) else {decv_v}={body_v} end "
        f"local {chars_v}={{}} for {ci2_v}=1,#{decv_v},1 do {chars_v}[{ci2_v}]={sc}({decv_v}[{ci2_v}]) end "
        f"local {valv_v}=table.concat({chars_v}) local {result_v} if {par_ka_b1}==1 then {result_v}={valv_v} elseif {par_ka_b1}==2 then local {nv_v}=tonumber({valv_v}) {result_v}={nv_v}==nil and 0 or {nv_v} elseif {par_ka_b1}==3 then {result_v}={valv_v}=='1' end {CC_v}[{ck_v}]={result_v} return {result_v} end "
    ), {"ks": ks_v, "xorb": xorb_v, "nb": nb_v, "sc": sc, "blk": blk_v, "inflate_tables": inflate_tables, "g3": g3, "key": key_v}

def build_vm_dispatch(rng):
    import re
    ops = {
        "add":    ("s,m", "s+m"),
        "sub":    ("s,m", "s-m"),
        "mul":    ("s,m", "s*m"),
        "div":    ("s,m", "s/m"),
        "mod":    ("s,m", "s%m"),
        "pow":    ("s,m", "s^m"),
        "unm":    ("s",   "-s"),
        "len":    ("s",   "#s"),
        "concat": ("s,m", "s..m"),
        "eq":     ("s,m", "s==m"),
        "ne":     ("s,m", "s~=m"),
        "lt":     ("s,m", "s<m"),
        "le":     ("s,m", "s<=m"),
        "gt":     ("s,m", "s>m"),
        "ge":     ("s,m", "s>=m"),
        "not":    ("s",   "not s"),
        "index":  ("s,m", "s[m]"),
        "tostr":  ("s",   'tostring(s) or s..""'),
        "toadd0": ("s",   "s+0"),
        "isnan":  ("s,m", "m==m"),
        "ternary":("s,m", "s~=nil and s or m"),
    }

    seen_hashes = set()
    all_keys = []
    hashes = {}
    dispatch_lines = []
    for op_name, (params, expr) in ops.items():
        count = rng.randint(3, 8)
        for _ in range(count):
            h = rng.randint(0x10000000, 0xFFFFFFFF)
            while h in seen_hashes:
                h = rng.randint(0x10000000, 0xFFFFFFFF)
            seen_hashes.add(h)
            all_keys.append(h)
            hashes[op_name] = h
            ps = gen_name()
            pm = gen_name()
            real_params = ps if params == "s" else f"{ps},{pm}"
            real_expr = re.sub(r'\bs\b', ps, expr)
            if params != "s":
                real_expr = re.sub(r'\bm\b', pm, real_expr)
            dispatch_lines.append(f"[{h}]=function({real_params}) return {real_expr} end")

    expected_count = len(all_keys)
    expected_sum = sum(all_keys) % 0x100000000
    expected_xor = 0
    for k in all_keys:
        expected_xor ^= k
    hashes["__meta__"] = (expected_count, expected_sum, expected_xor)
    dispatch_expr = f"{{{';'.join(dispatch_lines)}}}"
    return dispatch_expr, hashes

def build_anti_tamper_v1(seeds, rng, var_k, encode_fn, detect_var=None, level="full"):
    if level not in ("full", "minimal", "none"):
        level = "full"
    if level == "none":
        return ""

    kill_v  = gen_name()
    db_v    = gen_name()
    t0_v    = gen_name()
    t1_v    = gen_name()
    ti_v    = gen_name()
    acc_v   = gen_name()
    loop2_v = gen_name()
    ev_v    = gen_name()
    mt_v    = gen_name()
    tb_v    = gen_name()
    trap_v  = gen_name()
    nstr_v  = gen_name()
    fnparam_x_v = gen_name()
    ok_v    = gen_name()
    er_v    = gen_name()
    fn_v    = gen_name()
    ch_v    = gen_name()
    hk_v    = gen_name()
    le_v    = gen_name()
    lok1_v  = gen_name()
    lenv1_v = gen_name()
    lok2_v  = gen_name()
    lenv2_v = gen_name()
    lfn_v   = gen_name()
    ln_v    = gen_name()
    lk_v    = gen_name()
    lreq_v  = gen_name()
    lres_v  = gen_name()
    sus_v   = gen_name()
    dc_v    = gen_name()
    otype_v = gen_name()
    opcall_v = gen_name()
    oerror_v = gen_name()
    ostr_v  = gen_name()
    odbg_v  = gen_name()
    dfn_v   = gen_name()
    dmp_v   = gen_name()

    m1 = rng.randint(0x2000, 0xEFFF)
    m2 = rng.randint(0x2000, 0xEFFF)
    m3 = rng.randint(0x2000, 0xEFFF)
    timing_limit = 3.0
    loop_count   = 100000

    executor_globals = [
    ]

    debugger_names = [
        "MobDebug", "remdebug", "RemDebug", "LuaSocket",
        "ldb", "__debugger", "BreakpointHook",
    ]

    lune_modules = [
        "@lune/datetime", "@lune/fs", "@lune/luau", "@lune/net",
        "@lune/process", "@lune/regex", "@lune/roblox", "@lune/serde",
        "@lune/stdio", "@lune/task",
        "datetime", "fs", "luau", "net",
        "process", "regex", "roblox", "serde", "stdio", "task",
        "@lune/date", "@lune/fs/promises", "@lune/stream", "@lune/url",
        "@lune/path", "@lune/child_process", "@lune/encoding",
        "@lune/compression", "@lune/base64", "@lune/random", "@lune/utf8",
        "@lune/hex", "@lune/format", "@lune/fetch", "@lune/timer",
        "@lune/cli", "@lune/ini", "@lune/toml", "@lune/yaml",
        "@lune/discord", "@lune/scheduler", "@lune/cors", "@lune/profiler",
        "@lune/repl", "@lune/terminal", "@lune/assert", "@lune/bench",
        "@lune/buffer", "@lune/cache", "@lune/clipboard", "@lune/color",
        "@lune/config", "@lune/datastore", "@lune/diff", "@lune/dns",
        "@lune/env", "@lune/event", "@lune/expect", "@lune/glob",
        "@lune/html", "@lune/http", "@lune/jwt", "@lune/log",
        "@lune/markdown", "@lune/mime", "@lune/mysql", "@lune/robot",
        "@lune/semver", "@lune/shell", "@lune/signal", "@lune/socket",
        "@lune/sqlite", "@lune/test", "@lune/uuid", "@lune/worker",
        "@lune/crypto",
    ]

    lute_modules = [
        "@lute/fs", "@lute/net", "@lute/task", "@lute/process",
        "@lute/crypto", "@lute/luau", "@lute/vm", "@lute/time",
        "@std/fs", "@std/net", "@std/task", "@std/process",
        "@std/crypto", "@std/luau", "@std/io", "@std/testing",
        "@std/assert", "@std/lint",
        "@lute/date", "@lute/stream", "@lute/url", "@lute/path",
        "@lute/encoding", "@lute/compression", "@lute/serde",
        "@lute/base64", "@lute/random", "@lute/utf8", "@lute/hex",
        "@lute/format", "@lute/timer", "@lute/cli", "@lute/ini",
        "@lute/toml", "@lute/yaml", "@lute/discord", "@lute/scheduler",
        "@lute/cors", "@lute/profiler", "@lute/repl", "@lute/terminal",
        "@lute/roblox", "@lute/assert", "@lute/bench", "@lute/buffer",
        "@lute/cache", "@lute/clipboard", "@lute/color", "@lute/config",
        "@lute/datastore", "@lute/diff", "@lute/dns", "@lute/env",
        "@lute/event", "@lute/expect", "@lute/glob", "@lute/html",
        "@lute/http", "@lute/jwt", "@lute/log", "@lute/markdown",
        "@lute/mime", "@lute/mysql", "@lute/regex", "@lute/robot",
        "@lute/semver", "@lute/shell", "@lute/signal", "@lute/socket",
        "@lute/sqlite", "@lute/test", "@lute/uuid", "@lute/worker",
        "@testez", "@jsdotlua/jest",
    ]

    js_env_globals = [
        "wally", "rojo", "selene", "darklua", "luau_lsp", "remodel",
        "tarmac", "stylua", "lemur", "busted", "luaunit", "telescope",
        "plugin", "fetch", "console", "setTimeout", "setInterval",
        "Buffer", "AbortController", "AbortSignal", "clearInterval",
        "clearTimeout", "crypto", "performance", "global", "Headers",
        "Request", "Response", "TextDecoder", "TextEncoder",
        "atob", "btoa", "self", "FormData", "Blob", "File",
        "URLSearchParams", "Event", "CustomEvent", "structuredClone",
        "__dirname", "__filename", "alert", "confirm", "prompt",
        "navigator", "location", "history", "window", "document",
        "XMLHttpRequest", "EventTarget", "MessageChannel",
        "BroadcastChannel", "queueMicrotask", "reportError",
        "DOMException", "requestAnimationFrame", "cancelAnimationFrame",
        "matchMedia", "postMessage", "Worker", "SharedWorker",
        "ServiceWorker", "IndexedDB", "localStorage", "sessionStorage",
        "caches", "Cache", "CacheStorage", "globalThis", "URL",
        "FileReader", "FileList", "FileSystem", "DirectoryEntry",
        "DOMError", "DOMImplementation", "DOMTokenList",
        "DocumentFragment", "Element", "HTMLElement", "HTMLDocument",
        "Node", "NodeList", "MouseEvent", "KeyboardEvent", "FocusEvent",
        "UIEvent", "WheelEvent", "CompositionEvent", "DragEvent",
        "ClipboardEvent", "PointerEvent", "TouchEvent", "GamepadEvent",
        "MediaQueryList", "MediaQueryListEvent",
        "Screen", "History", "Location", "Navigator", "BarProp",
        "External", "ApplicationCache", "Storage", "StorageEvent",
        "CloseEvent", "MessageEvent", "ErrorEvent", "PopStateEvent",
        "HashChangeEvent", "PageTransitionEvent", "PromiseRejectionEvent",
        "BeforeUnloadEvent", "SecurityPolicyViolationEvent",
        "XMLHttpRequestEventTarget", "XMLHttpRequestUpload", "FetchEvent",
        "ServiceWorkerRegistration", "ServiceWorkerGlobalScope",
        "WorkerGlobalScope", "DedicatedWorkerGlobalScope",
        "SharedWorkerGlobalScope", "Worklet", "AudioWorklet",
        "PaintWorklet", "LayoutWorklet", "AnimationWorklet",
        "CSS", "CSSStyleDeclaration", "CSSStyleSheet", "StyleSheet",
        "StyleSheetList", "StyleMedia", "MediaList", "MediaError",
        "MediaSource", "SourceBuffer", "SourceBufferList", "TextTrack",
        "TextTrackList", "TextTrackCue", "VTTCue", "VTTRegion",
        "CanvasRenderingContext2D", "CanvasGradient", "CanvasPattern",
        "ImageBitmap", "ImageBitmapRenderingContext", "OffscreenCanvas",
        "HTMLCanvasElement", "HTMLImageElement", "HTMLVideoElement",
        "HTMLAudioElement", "HTMLMediaElement", "HTMLSourceElement",
        "HTMLTrackElement", "HTMLFormElement", "HTMLInputElement",
        "HTMLButtonElement", "HTMLSelectElement", "HTMLOptionElement",
        "HTMLTextAreaElement", "HTMLLabelElement", "HTMLFieldSetElement",
        "HTMLLegendElement", "HTMLDataListElement", "HTMLOutputElement",
        "HTMLProgressElement", "HTMLMeterElement", "HTMLDetailsElement",
        "HTMLDialogElement", "HTMLMenuElement", "HTMLMenuItemElement",
        "HTMLSummaryElement", "HTMLDivElement", "HTMLSpanElement",
        "HTMLHeadingElement", "HTMLParagraphElement", "HTMLPreElement",
        "HTMLQuoteElement", "HTMLOListElement", "HTMLUListElement",
        "HTMLLIElement", "HTMLDListElement", "HTMLDTElement",
        "HTMLDDElement", "HTMLTableElement", "HTMLTableCaptionElement",
        "HTMLTableColElement", "HTMLTableSectionElement",
        "HTMLTableRowElement", "HTMLTableCellElement",
        "HTMLTableDataCellElement", "HTMLTableHeaderCellElement",
        "HTMLFrameSetElement", "HTMLFrameElement", "HTMLIFrameElement",
        "HTMLEmbedElement", "HTMLObjectElement", "HTMLParamElement",
        "HTMLMapElement", "HTMLAreaElement", "HTMLScriptElement",
        "HTMLNoScriptElement", "HTMLStyleElement", "HTMLLinkElement",
        "HTMLBaseElement", "HTMLHeadElement", "HTMLTitleElement",
        "HTMLMetaElement", "HTMLBodyElement", "HTMLHtmlElement",
        "HTMLUnknownElement",
        "SVGElement", "SVGGraphicsElement", "SVGSVGElement",
        "SVGRectElement", "SVGCircleElement", "SVGEllipseElement",
        "SVGLineElement", "SVGPolylineElement", "SVGPolygonElement",
        "SVGPathElement", "SVGTextElement", "SVGTSpanElement",
        "SVGTextPathElement", "SVGImageElement", "SVGForeignObjectElement",
        "SVGDefsElement", "SVGGElement", "SVGSymbolElement",
        "SVGUseElement", "SVGMarkerElement", "SVGClipPathElement",
        "SVGMaskElement", "SVGLinearGradientElement",
        "SVGRadialGradientElement", "SVGStopElement", "SVGPatternElement",
        "SVGScriptElement", "SVGStyleElement", "SVGAnimateElement",
        "SVGAnimateMotionElement", "SVGAnimateTransformElement",
        "SVGSetElement", "SVGMetadataElement", "SVGViewElement",
        "SVGSwitchElement", "SVGDescElement", "SVGTitleElement",
    ]

    def enc_call(name):
        enc, cid = encode_fn(name)
        s0 = rng.randint(100000, 2**31 - 1)
        s2 = rng.randint(100000, 2**31 - 1)
        s3 = rng.randint(100000, 2**31 - 1)
        return f'{var_k}("{enc}",1,{s0},{cid},{cid},{s2},{s3})'

    dc = " ".join(
        f"if rawget({ev_v},{enc_call(dn)})~=nil then {kill_v}() end"
        for dn in debugger_names
    )

    exec_checks = " ".join(
        f"if rawget({ev_v},{enc_call(eg)})~=nil then {kill_v}() end"
        for eg in executor_globals
    )

    lune_check_g = " ".join(
        f"if {le_v}[{enc_call(m)}]~=nil then {sus_v}={sus_v}+1 end"
        for m in lune_modules
    )

    lute_check_g = " ".join(
        f"if {le_v}[{enc_call(m)}]~=nil then {sus_v}={sus_v}+1 end"
        for m in lute_modules
    )

    lune_check_req = " ".join(
        f"do local {lok1_v},{lres_v}=pcall({lreq_v},{enc_call(m)}) if {lok1_v} and {lres_v}~=nil then {sus_v}={sus_v}+1 end end"
        for m in lune_modules
    )

    lute_check_req = " ".join(
        f"do local {lok1_v},{lres_v}=pcall({lreq_v},{enc_call(m)}) if {lok1_v} and {lres_v}~=nil then {sus_v}={sus_v}+1 end end"
        for m in lute_modules
    )

    js_env_check_g = " ".join(
        f"if {le_v}[{enc_call(m)}]~=nil then {sus_v}={sus_v}+1 end"
        for m in js_env_globals
    )

    melodie_messages = [
        "Melodie doesn't approve of skidding be a good boy",
        "Melodie caught you tampering with the bytecode :3",
        "Meloten and Melodie protect this territory",
        "Melodie says: reverse engineering strictly prohibited",
        "Melodie detected an unauthorized debugger or hook",
    ]
    decoy_message = rng.choice(melodie_messages)
    decoy_enc = enc_call(decoy_message)

    def build_kill_v(spam_v, spam_i_v, spam_n_v, decoy_expr, detect_var=None):
        variant = rng.randint(1, 4)
        wait_expr = rng.choice([
            "if task then task.wait(0) elseif coroutine then coroutine.yield() end",
            "if coroutine then coroutine.yield() elseif task then task.wait(0) end",
            "if wait then wait(0) elseif task then task.wait(0) end",
        ])
        junk1 = rng.randint(1000, 9999)
        junk2 = rng.randint(1000, 9999)
        set_detect = f"{detect_var}=true " if detect_var else ""
        spam_stmt = (
            f"{set_detect}"
            f"if not {spam_v} then {spam_v}=true "
            f"local {spam_n_v}=math.random(5,10) "
            f"for {spam_i_v}=1,{spam_n_v} do print({decoy_expr}) end end "
        )
        loop_v = gen_name()
        cnt2_v = gen_name()
        f1_v   = gen_name()
        f2_v   = gen_name()
        melodie_tick = f"print({decoy_expr}) "
        if variant == 1:
            return f"function() {spam_stmt} error('',0) local {loop_v}=true while {loop_v} do {melodie_tick}{wait_expr} error('',0) end end"
        elif variant == 2:
            return f"function() {spam_stmt} local {cnt2_v}={junk1} while true do {cnt2_v}={cnt2_v}+1 {melodie_tick}{wait_expr} if {cnt2_v}>{junk1} then error('',0) end end end"
        elif variant == 3:
            return f"function() {spam_stmt} local {cnt2_v}=0 repeat {cnt2_v}={cnt2_v}+1 {melodie_tick}{wait_expr} error('',0) until {cnt2_v}<0 end"
        else:
            return f"function() {spam_stmt} local {f1_v} local {f2_v}=function() {melodie_tick}{wait_expr} error('',0) return {f1_v}() end {f1_v}={f2_v} return {f2_v}() end"

    spam_v   = gen_name()
    spam_i_v = gen_name()
    spam_n_v = gen_name()
    kill_body = build_kill_v(spam_v, spam_i_v, spam_n_v, decoy_enc, detect_var=detect_var)

    err_probe_marker = f"__mv_{rng.randint(100000,999999)}_{secrets.token_hex(6)}"
    probe_v  = gen_name()
    ic1_v    = gen_name()
    ic1ok_v  = gen_name()
    ic1res_v = gen_name()
    loopvar_v = gen_name()

    err_probe_check = (
        f"do local {probe_v}=function({fn_v}) "
        f"local {ok_v},{er_v}={opcall_v}({fn_v}) "
        f"if {otype_v}({er_v})~='string' then return false end "
        f"return string.find({er_v},'{err_probe_marker}')~=nil end "
        f"local {ic1_v}=true "
        f"for {loopvar_v}=1,5 do "
        f"if not {probe_v}(function() {oerror_v}('{err_probe_marker}') end) then {ic1_v}=false end "
        f"end "
        f"if not {ic1_v} then {kill_v}() end "
        f"end "
    )

    idc_f1_v  = gen_name()
    idc_f2_v  = gen_name()
    idc_s1a_v = gen_name()
    idc_s1b_v = gen_name()
    idc_s2a_v = gen_name()
    idc_s2b_v = gen_name()
    idc_ok1_v = gen_name()
    idc_ok2_v = gen_name()
    idc_l1_v  = gen_name()
    idc_l2_v  = gen_name()

    identity_consistency_check = (
        f"do local {idc_f1_v}=function() end local {idc_f2_v}=function() end "
        f"local {idc_s1a_v}={ostr_v}({idc_f1_v}) local {idc_s2a_v}={ostr_v}({idc_f2_v}) "
        f"local {idc_s1b_v}={ostr_v}({idc_f1_v}) local {idc_s2b_v}={ostr_v}({idc_f2_v}) "
        f"if {idc_s1a_v}~={idc_s1b_v} then {kill_v}() end "
        f"if {idc_s2a_v}~={idc_s2b_v} then {kill_v}() end "
        f"if {idc_s1a_v}=={idc_s2a_v} then {kill_v}() end "
        f"if {odbg_v} and {odbg_v}.info then "
        f"local {idc_ok1_v},{idc_l1_v}={opcall_v}({odbg_v}.info,{idc_f1_v},'l') "
        f"local {idc_ok2_v},{idc_l2_v}={opcall_v}({odbg_v}.info,{idc_f1_v},'l') "
        f"if {idc_ok1_v} and {idc_ok2_v} and {otype_v}({idc_l1_v})=='number' and {otype_v}({idc_l2_v})=='number' and {idc_l1_v}~={idc_l2_v} then {kill_v}() end "
        f"end end "
    )

    stat_n_v   = gen_name()
    stat_acc1_v = gen_name()
    stat_acc2_v = gen_name()
    stat_len_v = gen_name()
    stat_pos_v = gen_name()
    stat_val_v = gen_name()
    stat_should_v = gen_name()
    stat_arr_v = gen_name()
    stat_i_v   = gen_name()
    stat_tmp_v = gen_name()
    stat_j_v   = gen_name()

    statistical_check = (
        f"do local {stat_n_v}=math.random(8,24) "
        f"local {stat_acc1_v}=0 local {stat_acc2_v}=0 "
        f"for {stat_i_v}=1,{stat_n_v} do "
        f"local {stat_len_v}=math.random(1,64) "
        f"local {stat_val_v}=math.random(0,255) "
        f"local {stat_pos_v}=math.random(1,{stat_len_v}) "
        f"local {stat_should_v}=math.random(1,2)==1 "
        f"local {stat_arr_v}={{{opcall_v}(function() "
        f"if {stat_should_v} then {oerror_v}('{err_probe_marker}_S',0) end "
        f"local {stat_tmp_v}={{}} for {stat_j_v}=1,{stat_len_v} do {stat_tmp_v}[{stat_j_v}]=math.random(0,255) end "
        f"{stat_tmp_v}[{stat_pos_v}]={stat_val_v} return {stat_tmp_v}[{stat_pos_v}] end)}} "
        f"if {stat_should_v} then "
        f"if {stat_arr_v}[1]~=false then {kill_v}() end "
        f"else "
        f"if {stat_arr_v}[1]~=true then {kill_v}() end "
        f"{stat_acc1_v}=({stat_acc1_v}+{stat_arr_v}[2])%256 "
        f"{stat_acc2_v}=({stat_acc2_v}+{stat_val_v})%256 "
        f"end "
        f"end "
        f"if {stat_acc1_v}~={stat_acc2_v} then {kill_v}() end "
        f"end "
    )

    phys_part_v = gen_name()
    phys_cam_v = gen_name()
    phys_ok_v = gen_name()
    phys_bv_v = gen_name()
    phys_vel_v = gen_name()
    phys_bp_v = gen_name()
    phys_y_v = gen_name()
    phys_fall_v = gen_name()
    phys_vy_v = gen_name()
    phys_g_v = gen_name()
    phys_lt_v = gen_name()
    phys_player_v = gen_name()
    phys_thread_v = gen_name()
    phys_a_v = gen_name()
    phys_b_v = gen_name()
    phys_okmt_v = gen_name()
    phys_v1_v = gen_name()
    phys_v2_v = gen_name()
    phys_mt_v = gen_name()
    phys_t_v = gen_name()
    phys_vely_v = gen_name()
    phys_bp2_v = gen_name()
    phys_mtval_v = gen_name()
    phys_part2_v = gen_name()
    phys_okpart_v = gen_name()
    phys_oksettings_v = gen_name()
    phys_settings_v = gen_name()

    roblox_behavior_check = (
        f"do local {phys_ok_v}={opcall_v}(function() "
        f"local {phys_part_v}=Instance.new('Part') "
        f"{phys_part_v}.Shape=Enum.PartType.Cylinder "
        f"{phys_part_v}.Parent=workspace "
        f"if {phys_part_v}.Parent~=workspace then {kill_v}() end "
        f"if {phys_part_v}.Shape~=Enum.PartType.Cylinder then {kill_v}() end "
        f"{phys_part_v}:Destroy() "
        f"if not {opcall_v}(function() return workspace.CurrentCamera.CFrame:Inverse() end) then {kill_v}() end "
        f"if not {opcall_v}(function() local {phys_v1_v}=Vector3.new(1,2,3) local {phys_v2_v}=Vector3.new(1.0001,2.0001,3.0001) return {phys_v1_v}:FuzzyEq({phys_v2_v}) end) then {kill_v}() end "
        f"local {phys_player_v}=game.Players.LocalPlayer "
        f"if {otype_v}({phys_player_v})~='userdata' or typeof({phys_player_v})~='Instance' or not {phys_player_v}.Name or not {phys_player_v}.Parent or not {phys_player_v}.Parent.Name then {kill_v}() end "
        f"local {phys_thread_v}=task.spawn(function() end) "
        f"task.cancel({phys_thread_v}) "
        f"if {otype_v}({phys_thread_v})~='thread' then {kill_v}() end "
        f"local {phys_a_v},{phys_b_v}={opcall_v}(function() loadstring('abc')() end) "
        f"if {phys_a_v} then {kill_v}() end "
        f"if not {phys_b_v} then {kill_v}() end "
        f"if {otype_v}(typeof)~='function' then {kill_v}() end "
        f"if typeof({{}})~='table' then {kill_v}() end "
        f"if typeof(game)~='Instance' then {kill_v}() end "
        f"if not {opcall_v}(function() return {odbg_v}.getinfo(print).what=='C' end) then {kill_v}() end "
        f"local {phys_okmt_v},{phys_mtval_v}={opcall_v}(function() local {phys_t_v}={{}} local {phys_mt_v}={{__index={{a=1}}}} setmetatable({phys_t_v},{phys_mt_v}) return {phys_t_v}.a end) "
        f"if not {phys_okmt_v} or {phys_mtval_v}~=1 then {kill_v}() end "
        f"local {phys_okpart_v},{phys_part2_v}={opcall_v}(function() return Instance.new('Part') end) "
        f"if not {phys_okpart_v} or typeof({phys_part2_v})~='Instance' then {kill_v}() end "
        f"local {phys_oksettings_v},{phys_settings_v}={opcall_v}(function() return settings() end) "
        f"if not {phys_oksettings_v} or {otype_v}({phys_settings_v})~='userdata' then {kill_v}() end "
        f"local {phys_bv_v}=Instance.new('Part') "
        f"{phys_bv_v}.Anchored=false "
        f"{phys_bv_v}.Parent=workspace "
        f"local {phys_vel_v}=Instance.new('BodyVelocity',{phys_bv_v}) "
        f"{phys_vel_v}.Velocity=Vector3.new(0,10,0) "
        f"task.wait(0.2) "
        f"local {phys_vely_v}={phys_bv_v}.AssemblyLinearVelocity "
        f"{phys_bv_v}:Destroy() "
        f"if not ({phys_vely_v} and {phys_vely_v}.Y>1) then {kill_v}() end "
        f"local {phys_bp_v}=Instance.new('Part') "
        f"{phys_bp_v}.Position=Vector3.new(0,10,0) "
        f"{phys_bp_v}.Anchored=false "
        f"{phys_bp_v}.Parent=workspace "
        f"local {phys_bp2_v}=Instance.new('BodyPosition',{phys_bp_v}) "
        f"{phys_bp2_v}.Position=Vector3.new(0,50,0) "
        f"{phys_bp2_v}.D=1000 {phys_bp2_v}.P=10000 "
        f"{phys_bp2_v}.MaxForce=Vector3.new(0,4000,0) "
        f"task.wait(0.3) "
        f"local {phys_y_v}={phys_bp_v}.Position.Y "
        f"{phys_bp_v}:Destroy() "
        f"if not ({phys_y_v}>20) then {kill_v}() end "
        f"local {phys_fall_v}=Instance.new('Part') "
        f"{phys_fall_v}.Anchored=false "
        f"{phys_fall_v}.Position=Vector3.new(0,20,0) "
        f"{phys_fall_v}.Parent=workspace "
        f"task.wait(0.3) "
        f"local {phys_vy_v}={phys_fall_v}.AssemblyLinearVelocity.Y "
        f"{phys_fall_v}:Destroy() "
        f"local {phys_g_v}=-workspace.Gravity*0.3 "
        f"if not ({phys_vy_v} and math.abs({phys_vy_v}-{phys_g_v})<5) then {kill_v}() end "
        f"end) "
        f"if not {phys_ok_v} then {kill_v}() end "
        f"end "
    )

    http_v      = gen_name()
    http_ok_v   = gen_name()
    j1_ok_v     = gen_name()
    j1_res_v    = gen_name()
    j2_ok_v     = gen_name()
    j3_ok_v     = gen_name()
    j4_ok_v     = gen_name()
    part3_v     = gen_name()
    name_ok_v   = gen_name()
    name_res_v  = gen_name()
    grawmt_v    = gen_name()
    udim_v      = gen_name()
    coro_v      = gen_name()
    part4_v     = gen_name()
    shape1_ok_v = gen_name()
    shape2_ok_v = gen_name()
    pkg_v       = gen_name()
    lt_v        = gen_name()
    lt_ok_v     = gen_name()
    lt_ent_v    = gen_name()
    lt_key_v    = gen_name()
    lt_val_v    = gen_name()
    lt_lang_v   = gen_name()
    lt_exp_v    = gen_name()
    lt_expl_v   = gen_name()

    lt_langs = ["fr", "es", "de", "pt", "ru"]
    lt_words = {
        "greeting": ("Hello", {"fr": "Bonjour", "es": "Hola", "de": "Hallo", "pt": "Ola", "ru": "Privet"}),
        "farewell": ("Goodbye", {"fr": "Au revoir", "es": "Adios", "de": "Auf Wiedersehen", "pt": "Adeus", "ru": "Do svidaniya"}),
        "thankyou": ("Thank you", {"fr": "Merci", "es": "Gracias", "de": "Danke", "pt": "Obrigado", "ru": "Spasibo"}),
    }

    def lt_entries_literal():
        parts = []
        for key, (source, vals) in lt_words.items():
            vpairs = ",".join(f"[{enc_call(k)}]={enc_call(v)}" for k, v in vals.items())
            vpairs = f"[{enc_call('en')}]={enc_call(source)}," + vpairs
            parts.append(
                f"{{[{enc_call('Key')}]={enc_call(key)},[{enc_call('Source')}]={enc_call(source)},[{enc_call('Values')}]={{{vpairs}}}}}"
            )
        return "{" + ",".join(parts) + "}"

    def lt_expected_literal():
        parts = []
        for key, (_source, vals) in lt_words.items():
            vpairs = ",".join(f"[{enc_call(k)}]={enc_call(v)}" for k, v in vals.items())
            parts.append(f"[{enc_call(key)}]={{{vpairs}}}")
        return "{" + ",".join(parts) + "}"

    extra_sandbox_check = (
        f"do local {http_ok_v},{http_v}={opcall_v}(function() return game:GetService('HttpService') end) "
        f"if not {http_ok_v} or not {http_v} then {kill_v}() end "
        f"local {j1_ok_v},{j1_res_v}={opcall_v}(function() return {http_v}:JSONEncode({{{ostr_v}(1)}}) end) "
        f"if not {j1_ok_v} then {kill_v}() end "
        f"local {j2_ok_v}={opcall_v}(function() return {http_v}:JSONDecode({j1_res_v}) end) "
        f"if not {j2_ok_v} then {kill_v}() end "
        f"local {j3_ok_v}={opcall_v}(function() return {http_v}:GenerateGUID(false) end) "
        f"if not {j3_ok_v} then {kill_v}() end "
        f"local {j4_ok_v}={opcall_v}(function() return {http_v}:UrlEncode('a b') end) "
        f"if not {j4_ok_v} then {kill_v}() end "
        f"end "
        f"do local {part3_v}={opcall_v}(Instance.new,'Part') "
        f"local {name_ok_v},{name_res_v}={opcall_v}(function() return {part3_v}.Name end) "
        f"if not {name_ok_v} or {name_res_v}~='Part' then {kill_v}() end "
        f"end "
        f"do local {udim_v}=UDim2.fromOffset(10,5) "
        f"if {udim_v}.X.Offset~=10 or {udim_v}.Y.Offset~=5 then {kill_v}() end "
        f"end "
        f"do local {coro_v}={opcall_v}(function() return {odbg_v}.getinfo(coroutine.wrap).what end) "
        f"local {ok_v},{er_v}={opcall_v}(function() return {odbg_v}.getinfo(coroutine.wrap).what=='C' end) "
        f"if {ok_v} and not {er_v} then {kill_v}() end "
        f"end "
        f"if Enum.PartType.Cylinder.Name~='Cylinder' then {kill_v}() end "
        f"if Enum.PartType.Cylinder.Value~=2 then {kill_v}() end "
        f"if {ostr_v}(Enum.PartType.Cylinder.EnumType)~='PartType' then {kill_v}() end "
        f"do local {part4_v}=Instance.new('Part') "
        f"local {shape1_ok_v}={opcall_v}(function() {part4_v}.Shape=Enum.PartType.Cylinder end) "
        f"local {shape2_ok_v}={opcall_v}(function() {part4_v}.Shape='Cylinder' end) "
        f"if not {shape1_ok_v} or not {shape2_ok_v} then {kill_v}() end "
        f"{part4_v}:Destroy() "
        f"end "
        f"do local {pkg_v}=package "
        f"if {otype_v}({pkg_v})=='table' then "
        f"if rawget({pkg_v},{enc_call('lune')}) or rawget({pkg_v},{enc_call('lute')}) or rawget({pkg_v},{enc_call('wally')}) or rawget({pkg_v},{enc_call('rojo')}) or rawget({pkg_v},{enc_call('config')}) then {kill_v}() end "
        f"end end "
        f"if os and os.execute~=nil then {kill_v}() end "
        f"if io and io.open and io.read then {kill_v}() end "
        f"do local {lt_v}=Instance.new('LocalizationTable') "
        f"{lt_v}.SourceLocaleId='en' "
        f"{lt_v}:SetEntries({lt_entries_literal()}) "
        f"local {lt_exp_v}={lt_expected_literal()} "
        f"local {lt_ok_v}=true "
        f"for _,{lt_ent_v} in ipairs({lt_v}:GetEntries()) do "
        f"local {lt_key_v}={lt_ent_v}.Key "
        f"local {lt_expl_v}={lt_exp_v}[{lt_key_v}] "
        f"if not {lt_expl_v} then {lt_ok_v}=false break end "
        f"for {lt_lang_v},{lt_val_v} in pairs({lt_expl_v}) do "
        f"if {lt_ent_v}.Values[{lt_lang_v}]~={lt_val_v} then {lt_ok_v}=false break end "
        f"end "
        f"if not {lt_ok_v} then break end "
        f"end "
        f"{lt_v}:Destroy() "
        f"if not {lt_ok_v} then {kill_v}() end "
        f"end "
    )

    genv_v      = gen_name()
    genvres_v   = gen_name()

    getfenv_probe_check = (
        f"if getfenv and setfenv then "
        f"local {genvres_v}=getfenv(0) or getfenv() "
        f"if {genvres_v} and ({genvres_v}.lune or {genvres_v}.lute or {genvres_v}.wally or {genvres_v}.rojo or {genvres_v}.process or {genvres_v}.fs or {genvres_v}.io) then {kill_v}() end "
        f"end "
        f"if _G.game==nil and _G.workspace==nil and ({opcall_v}(require,{enc_call('non_existent_module')}) or _G.require~=nil) then {kill_v}() end "
        f"if _G.process and _G.process.exit then {kill_v}() end "
        f"if _G.script and _G.script.Parent==nil and _G.script.Name==nil then {kill_v}() end "
    )

    obj_trap_v = gen_name()
    obj_trap_mt_v = gen_name()
    obj_trap_hit_v = gen_name()
    obj_trap_fn_v = gen_name()
    obj_trap_px_v = gen_name()

    tostring_trap_check = (
        f"do local {obj_trap_hit_v}=false "
        f"local {obj_trap_mt_v}={{__tostring=function() {obj_trap_hit_v}=true return '' end}} "
        f"local {obj_trap_v}=setmetatable({{}},{obj_trap_mt_v}) "
        f"local {obj_trap_fn_v}=function({obj_trap_px_v}) return {ostr_v}({obj_trap_px_v}) end "
        f"{obj_trap_fn_v}({obj_trap_v}) "
        f"if not {obj_trap_hit_v} then {kill_v}() end "
        f"end "
    )

    risky_checks = (
        f"{err_probe_check}"
        f"{identity_consistency_check}"
        f"{statistical_check}"
        f"{roblox_behavior_check}"
    ) if level == "full" else ""

    result = (
        f"local {sus_v}=0 "
        f"local {spam_v}=false "
        f"local {kill_v} {kill_v}={kill_body} "
        f"local {otype_v}=type "
        f"local {opcall_v}=pcall "
        f"local {oerror_v}=error "
        f"local {ostr_v}=tostring "
        f"local {odbg_v}=debug "
        f"local {db_v}=debug "
        f"if {otype_v}(rawget)~='function' then {kill_v}() end "
        f"if {otype_v}(rawset)~='function' then {kill_v}() end "
        f"if {otype_v}(setmetatable)~='function' then {kill_v}() end "
        f"if {otype_v}(getmetatable)~='function' then {kill_v}() end "
        f"if {otype_v}(pcall)~='function' then {kill_v}() end "
        f"if {otype_v}(xpcall)~='function' then {kill_v}() end "
        f"if {otype_v}(error)~='function' then {kill_v}() end "
        f"if {otype_v}(type)~='function' then {kill_v}() end "
        f"if {otype_v}(tostring)~='function' then {kill_v}() end "
        f"if {otype_v}(tonumber)~='function' then {kill_v}() end "
        f"if {otype_v}(select)~='function' then {kill_v}() end "
        f"if {otype_v}(ipairs)~='function' then {kill_v}() end "
        f"if {otype_v}(pairs)~='function' then {kill_v}() end "
        f"if {otype_v}(next)~='function' then {kill_v}() end "
        f"if {otype_v}(unpack or table.unpack)~='function' then {kill_v}() end "
        f"if {otype_v}(string.byte)~='function' then {kill_v}() end "
        f"if {otype_v}(string.char)~='function' then {kill_v}() end "
        f"if {otype_v}(string.len)~='function' then {kill_v}() end "
        f"if {otype_v}(string.sub)~='function' then {kill_v}() end "
        f"if {otype_v}(string.rep)~='function' then {kill_v}() end "
        f"if {otype_v}(string.find)~='function' then {kill_v}() end "
        f"if {otype_v}(string.format)~='function' then {kill_v}() end "
        f"if {otype_v}(table.concat)~='function' then {kill_v}() end "
        f"if {otype_v}(table.insert)~='function' then {kill_v}() end "
        f"if {otype_v}(table.remove)~='function' then {kill_v}() end "
        f"if {otype_v}(math.floor)~='function' then {kill_v}() end "
        f"if {otype_v}(math.abs)~='function' then {kill_v}() end "
        f"if {otype_v}(math.huge)~='number' then {kill_v}() end "
        f"if {otype_v}(_VERSION)~='string' then {kill_v}() end "
        f"if not(1/0==math.huge) then {kill_v}() end "
        f"if not(math.huge==math.huge*2) then {kill_v}() end "
        f"if not(0/0~=0/0) then {kill_v}() end "
        f"if not(-1/0==-math.huge) then {kill_v}() end "
        f"if math.abs(-{m1})~={m1} then {kill_v}() end "
        f"if math.floor({m1}+0.9)~={m1} then {kill_v}() end "
        f"do local {ok_v},{er_v}={opcall_v}(function() error({m1}) end) if {ok_v} then {kill_v}() end if {otype_v}({er_v})~='string' then {kill_v}() end end "
        f"do local {ti_v}=os and {otype_v}(os.clock)=='function' and os.clock or ({otype_v}(tick)=='function' and tick) or nil local {t0_v}={ti_v} and {ti_v}() or 0 local {acc_v}=0 for {loop2_v}=1,{loop_count} do {acc_v}={acc_v}+1 end local {t1_v}={ti_v} and {ti_v}() or 0 if {acc_v}~={loop_count} then {kill_v}() end if {ti_v} and ({t1_v}-{t0_v})>{timing_limit} then {kill_v}() end end "
        f"do local {tb_v}={{}} local {trap_v}=false local {mt_v}={{__newindex=function() {trap_v}=true end,__index=function() {trap_v}=true end}} setmetatable({tb_v},{mt_v}) local {ok_v}={opcall_v}(function() {tb_v}[{m2}]={m3} end) setmetatable({tb_v},nil) if not {trap_v} then {kill_v}() end end "
        f"do local {fn_v}=function({fnparam_x_v}) return {fnparam_x_v}*{m2}+{m3} end if {otype_v}({fn_v})~='function' then {kill_v}() end if {fn_v}(0)~={m3} then {kill_v}() end if {fn_v}(1)~={m2}+{m3} then {kill_v}() end local {ok_v},{er_v}={opcall_v}({fn_v},'z') if {ok_v} then {kill_v}() end end "
        f"do local {nstr_v}={ostr_v}({m1}+{m2}) if {otype_v}({nstr_v})~='string' then {kill_v}() end if tonumber({nstr_v})~=({m1}+{m2}) then {kill_v}() end end "
        f"do if {otype_v}({m1})~='number' then {kill_v}() end if {otype_v}('')~='string' then {kill_v}() end if {otype_v}({{}})~='table' then {kill_v}() end if {otype_v}(nil)~='nil' then {kill_v}() end if {otype_v}(true)~='boolean' then {kill_v}() end if {otype_v}({otype_v})~='function' then {kill_v}() end end "
        f"do local {ch_v}={ostr_v}({m1}):rep(3) if #{ch_v}~=3*#{ostr_v}({m1}) then {kill_v}() end end "
        f"local {ev_v}=(getfenv and getfenv(0)) or _ENV or {{}} "
        f"if {otype_v}({ev_v})~='table' then {kill_v}() end "
        f"{dc} "
        f"{exec_checks} "
        f"if rawget({ev_v},'__BREAKPOINT__')~=nil then {kill_v}() end "
        f"if rawget({ev_v},'__DEBUG__')~=nil then {kill_v}() end "
        f"if rawget({ev_v},'__ATTACHED__')~=nil then {kill_v}() end "
        f"do local {lreq_v}=require "
        f"local {lenv1_v}=_G "
        f"if type({lenv1_v})=='table' then {le_v}={lenv1_v} {lune_check_g} {lute_check_g} {js_env_check_g} end "
        f"local {lok2_v},{lenv2_v}=pcall(function() return _ENV end) "
        f"if {lok2_v} and {lenv2_v} and type({lenv2_v})=='table' and {lenv2_v}~=_G then {le_v}={lenv2_v} {lune_check_g} {lute_check_g} {js_env_check_g} end "
        f"do local {lok1_v},{lfn_v}=pcall(function() "
        f"local {ln_v}=load or loadstring "
        f"if type({ln_v})~='function' then return nil end "
        f"local {lk_v}={ln_v}('return _ENV') "
        f"if type({lk_v})~='function' then return nil end "
        f"return {lk_v}() end) "
        f"if {lok1_v} and {lfn_v} and type({lfn_v})=='table' and {lfn_v}~=_G then {le_v}={lfn_v} {lune_check_g} {lute_check_g} {js_env_check_g} end end "
        f"if type({lreq_v})=='function' then {lune_check_req} {lute_check_req} end "
        f"end "
        f"do local {dmp_v}={otype_v}(string)=='table' and string.dump "
        f"local {dfn_v}={{{otype_v},{opcall_v},{oerror_v},{ostr_v},tonumber,rawget,rawset,setmetatable,getmetatable,select,ipairs,pairs,next,string.byte,string.char,string.sub,string.find,string.format,table.concat,table.insert,table.remove,math.floor,math.abs}} "
        f"if {dmp_v} then for _,{fn_v} in ipairs({dfn_v}) do "
        f"local {ok_v}={opcall_v}({dmp_v},{fn_v}) "
        f"if {ok_v} then {kill_v}() end "
        f"end end "
        f"end "
        f"do local {dc_v}={sus_v}>0 "
        f"local {ok_v}=pcall(function() end) "
        f"if {dc_v} then print({decoy_enc}) {kill_v}() end "
        f"end "
        f"{tostring_trap_check}"
        f"{risky_checks}"

    )

    return result


def build_anti_tamper_v2(seeds, rng, var_k, encode_fn, detect_var=None, target="luau", level="full"):
    if level not in ("full", "minimal", "none"):
        level = "full"
    if level == "none":
        return ""

    def enc_call(text):
        enc, cid = encode_fn(text)
        s0 = rng.randint(100000, 2**31 - 1)
        s2 = rng.randint(100000, 2**31 - 1)
        s3 = rng.randint(100000, 2**31 - 1)
        return f'{var_k}("{enc}",1,{s0},{cid},{cid},{s2},{s3})'

    melodie_messages = [
        "Melodie doesn't approve of skidding be a good boy",
        "Melodie caught you tampering with the bytecode :3",
        "Meloten and Melodie protect this territory",
        "Melodie says: reverse engineering strictly prohibited",
        "Melodie detected an unauthorized debugger or hook",
    ]
    decoy_message = rng.choice(melodie_messages)
    decoy_enc = enc_call(decoy_message)

    sus_v = gen_name()
    spam_v = gen_name()
    spam_i_v = gen_name()
    spam_n_v = gen_name()
    kill_v = gen_name()
    loop_v = gen_name()
    set_detect = f"{detect_var}=true " if detect_var else ""
    wait_expr = rng.choice([
        "if task and task.wait then task.wait(0) elseif coroutine and coroutine.yield then coroutine.yield() end",
        "if coroutine and coroutine.yield then coroutine.yield() elseif task and task.wait then task.wait(0) end",
    ])
    spam_stmt = (
        f"{set_detect}"
        f"if not {spam_v} then {spam_v}=true "
        f"local {spam_n_v}=math.random(5,10) "
        f"for {spam_i_v}=1,{spam_n_v} do print({decoy_enc}) end end "
    )
    kill_body = (
        f"function() "
        f"{spam_stmt}"
        f"error('',0) "
        f"local {loop_v}=true "
        f"while {loop_v} do print({decoy_enc}) {wait_expr} error('',0) end "
        f"end"
    )

    canary_token = f"WO_{rng.randint(1000000, 9999999)}"
    tok_call = enc_call(canary_token)

    tf_v = gen_name()
    ret_v = gen_name()
    ok1_v = gen_name()
    ok2_v = gen_name()
    ok3_v = gen_name()
    src_v = gen_name()
    cl_v = gen_name()
    arr_v = gen_name()
    lock_v = gen_name()
    ok_v = gen_name()
    mt_t_v = gen_name()
    trap_hit_v = gen_name()
    mt_o_v = gen_name()
    p_ok_v = gen_name()
    p_msg_v = gen_name()
    f1_v = gen_name()
    f2_v = gen_name()
    cf_v = gen_name()
    s_v = gen_name()
    l_v = gen_name()
    a_v = gen_name()
    v_v = gen_name()
    cfns_v = gen_name()
    fn_v = gen_name()
    buf_v = gen_name()
    ev_v = gen_name()
    p_tbl_v = gen_name()
    s_sentinel_v = gen_name()
    h_calls_v = gen_name()
    w_mt_v = gen_name()
    ok_sem_v = gen_name()
    sem_k_v = gen_name()

    parts = [
        f"local {sus_v}=0 ",
        f"local {spam_v}=false ",
        f"local {kill_v} {kill_v}={kill_body} ",
        f"if (1/0~=math.huge) or (-1/0~=-math.huge) or (0/0==0/0) or (math.huge~=math.huge*2) or (math.huge+1~=math.huge) or (math.abs(-5)~=5) or (math.floor(3.7)~=3) or (math.ceil(3.2)~=4) or (1e308*10~=math.huge) then {kill_v}() end ",
        f"if (type(1)~='number') or (type('')~='string') or (type(true)~='boolean') or (type({{}})~='table') or (type(function() end)~='function') or (type(nil)~='nil') then {kill_v}() end ",
        f"if typeof and ((typeof(1)~='number') or (typeof('')~='string') or (typeof({{}})~='table')) then {kill_v}() end ",
        f"if (bit32.band(15,1)~=1) or (bit32.bor(2,1)~=3) or (bit32.bxor(5,5)~=0) or (bit32.lshift(1,3)~=8) or (bit32.rshift(8,3)~=1) or (bit32.lrotate(1,1)~=2) or (bit32.bnot(0)~=0xFFFFFFFF) or (bit32.arshift(-16,2)~=0xFFFFFFFC) or (bit32.extract(0xABCD,4,8)~=0xBC) then {kill_v}() end ",
        f"if table.freeze and table.isfrozen then local {tf_v}={{k=1}} if table.isfrozen({tf_v}) then {kill_v}() end local {ret_v}=table.freeze({tf_v}) if {ret_v}~={tf_v} or not table.isfrozen({tf_v}) then {kill_v}() end local {ok1_v}=pcall(function() {tf_v}.k=2 end) if {ok1_v} then {kill_v}() end local {ok2_v}=pcall(function() {tf_v}.newk=3 end) if {ok2_v} then {kill_v}() end local {ok3_v}=pcall(function() table.insert({tf_v},4) end) if {ok3_v} then {kill_v}() end end ",
        f"if table.clone then local {src_v}={{a=10,b=20}} local {cl_v}=table.clone({src_v}) if {cl_v}=={src_v} or {cl_v}.a~=10 or {cl_v}.b~=20 then {kill_v}() end end ",
        f"if table.find then local {arr_v}={{11,22,33}} if table.find({arr_v},22)~=2 or table.find({arr_v},99)~=nil then {kill_v}() end end ",
        f"if rawlen and (rawlen({{1,2,3,4}})~=4 or rawlen('hello')~=5) then {kill_v}() end ",
        f"if rawequal and (not rawequal(123,123) or rawequal(123,456) or not rawequal('a','a')) then {kill_v}() end ",
        f"do local {lock_v}=setmetatable({{}},{{__metatable='protected'}}) if getmetatable({lock_v})~='protected' then {kill_v}() end local {ok_v}=pcall(setmetatable,{lock_v},{{}}) if {ok_v} then {kill_v}() end local {mt_t_v}=setmetatable({{}},{{__index={{a=42}}}}) if {mt_t_v}.a~=42 then {kill_v}() end rawset({mt_t_v},'a',99) if rawget({mt_t_v},'a')~=99 or {mt_t_v}.a~=99 then {kill_v}() end local {trap_hit_v}=false local {mt_o_v}=setmetatable({{}},{{__tostring=function() {trap_hit_v}=true return {tok_call} end}}) if tostring({mt_o_v})~={tok_call} or not {trap_hit_v} then {kill_v}() end end ",
        f"if string.dump then local {ok_v}=pcall(string.dump,print) if {ok_v} then {kill_v}() end end ",
        f"if debug and debug.gethook and debug.gethook()~=nil then {kill_v}() end ",
        f"do local {p_tbl_v}={{}} local {s_sentinel_v}={{}} local {h_calls_v}=0 "
        f"local {w_mt_v}=setmetatable({p_tbl_v},{{__index=function(_,{sem_k_v}) {h_calls_v}={sem_k_v} return {s_sentinel_v} end,__metatable=false}}) "
        f"local {ok_sem_v}=({w_mt_v}=={p_tbl_v}) and ({h_calls_v}==0) and (next({{}})==nil) and (rawget({{1}},1)==1) and (type(type)=='function') and (tonumber('1')==1) "
        f"if {ok_sem_v} then "
        f"{ok_sem_v}=({p_tbl_v}[1]=={s_sentinel_v}) and ({h_calls_v}==1) and (getmetatable({p_tbl_v})==false) and (rawset({p_tbl_v},1,{s_sentinel_v})=={p_tbl_v}) and (rawget({p_tbl_v},1)=={s_sentinel_v}) "
        f"end "
        f"if not {ok_sem_v} then {kill_v}() end end ",
    ]

    if level == "full":
        parts.append(
            f"do local {p_ok_v},{p_msg_v}=pcall(function() error({tok_call},0) end) if {p_ok_v}~=false or {p_msg_v}~={tok_call} then {kill_v}() end end "
        )
        parts.append(
            f"do local {f1_v}=function() end local {f2_v}=function() end if tostring({f1_v})~=tostring({f1_v}) or tostring({f1_v})==tostring({f2_v}) then {kill_v}() end end "
        )

    if target == "luau":
        parts.append(
            f"if debug and debug.info then "
            f"do local {cf_v}=function() return 1 end local {s_v},{l_v},{a_v},{v_v}=debug.info({cf_v},'slan') if {s_v}=='[C]' or {l_v}<1 or {a_v}~=0 or {v_v}~=false then {kill_v}() end end "
            f"local {cfns_v}={{type,pcall,xpcall,error,setmetatable,getmetatable,rawget,rawset,select,tonumber,tostring,pairs,ipairs,next,string.byte,string.char,string.sub,string.len,string.find,table.insert,table.remove,table.concat,math.floor,math.ceil,math.abs,bit32.band,bit32.bxor,bit32.bor,bit32.lshift,bit32.rshift,coroutine.create,coroutine.resume,coroutine.yield,coroutine.status}} "
            f"for _,{fn_v} in ipairs({cfns_v}) do if debug.info({fn_v},'s')~='[C]' or debug.info({fn_v},'l')~=-1 then {kill_v}() end end "
            f"if debug.getinfo then if debug.getinfo(pcall).what~='C' or debug.getinfo(type).what~='C' or debug.getinfo(setmetatable).what~='C' then {kill_v}() end end "
            f"end "
        )
        parts.append(
            f"if buffer and type(buffer)=='table' and buffer.create and buffer.readu8 and buffer.writeu8 then "
            f"local {buf_v}=buffer.create(4) if buffer.len({buf_v})~=4 then {kill_v}() end buffer.writeu8({buf_v},0,137) buffer.writeu8({buf_v},1,99) if buffer.readu8({buf_v},0)~=137 or buffer.readu8({buf_v},1)~=99 then {kill_v}() end "
            f"end "
        )
        parts.append(
            f"do local {ev_v}=(getfenv and getfenv(0)) or _ENV or _G or {{}} "
            f"if rawget({ev_v},'__DEBUG__') or rawget({ev_v},'__BREAKPOINT__') or rawget({ev_v},'__ATTACHED__') or rawget({ev_v},'MobDebug') or rawget({ev_v},'remdebug') or rawget({ev_v},'ldb') or rawget({ev_v},'BreakpointHook') then {kill_v}() end "
            f"end "
        )
    else:
        plrs_v = gen_name()
        run_v = gen_name()
        http_ok_v = gen_name()
        http_v = gen_name()
        g_ok_v = gen_name()
        g_v = gen_name()
        j_ok_v = gen_name()
        j_v = gen_name()
        p_v = gen_name()
        v1_v = gen_name()
        v2_v = gen_name()
        cf_inv_v = gen_name()
        inv_v = gen_name()
        id_v = gen_name()
        u_v = gen_name()
        th_v = gen_name()
        pkg_v = gen_name()
        bad_globals_v = gen_name()
        bg_v = gen_name()
        req_v = gen_name()
        bad_mods_v = gen_name()
        bm_v = gen_name()
        res_v = gen_name()

        rbx_extra_c = ""
        if level == "full":
            fp1_ok = gen_name()
            fp1_er = gen_name()
            fp2_ok = gen_name()
            fp2_er = gen_name()
            rbx_extra_c = (
                f"if debug.info(Instance.new,'s')~='[C]' or debug.info(Instance.new,'l')~=-1 or "
                f"debug.info(game.GetService,'s')~='[C]' or debug.info(game.GetService,'l')~=-1 then {kill_v}() end "
                f"do local {fp1_ok},{fp1_er}=pcall(Instance.new) if {fp1_ok} or type({fp1_er})~='string' or string.find({fp1_er},'Argument 1')==nil then {kill_v}() end "
                f"local {fp2_ok},{fp2_er}=pcall(game.GetService,game) if {fp2_ok} or type({fp2_er})~='string' or string.find({fp2_er},'Argument 1')==nil then {kill_v}() end end "
            )

        parts.append(
            f"if (typeof==nil) or (game==nil) or (workspace==nil) or (Instance==nil) or (Enum==nil) or (Vector3==nil) or (CFrame==nil) or (task==nil) then {kill_v}() end "
        )
        parts.append(
            f"if debug and debug.info then "
            f"do local {cf_v}=function() return 1 end local {s_v},{l_v}=debug.info({cf_v},'sl') if {s_v}=='[C]' or {l_v}<1 then {kill_v}() end end "
            f"local {cfns_v}={{type,pcall,xpcall,error,setmetatable,getmetatable,rawget,rawset,select,tonumber,tostring,pairs,ipairs,next,string.byte,string.char,string.sub,string.len,table.insert,table.remove,table.concat,math.floor,math.abs,bit32.band,bit32.bxor}} "
            f"for _,{fn_v} in ipairs({cfns_v}) do if debug.info({fn_v},'s')~='[C]' or debug.info({fn_v},'l')~=-1 then {kill_v}() end end "
            f"{rbx_extra_c}"
            f"end "
        )
        parts.append(
            f"if typeof(game)~={enc_call('Instance')} or game.ClassName~={enc_call('DataModel')} then {kill_v}() end "
            f"if typeof(workspace)~={enc_call('Instance')} or workspace.ClassName~={enc_call('Workspace')} then {kill_v}() end "
        )
        parts.append(
            f"do local {plrs_v}=game:GetService({enc_call('Players')}) if typeof({plrs_v})~={enc_call('Instance')} or {plrs_v}.ClassName~={enc_call('Players')} then {kill_v}() end "
            f"local {run_v}=game:GetService({enc_call('RunService')}) if typeof({run_v})~={enc_call('Instance')} or {run_v}.ClassName~={enc_call('RunService')} then {kill_v}() end "
            f"local {http_ok_v},{http_v}=pcall(game.GetService,game,{enc_call('HttpService')}) "
            f"if {http_ok_v} and {http_v} then "
            f"local {g_ok_v},{g_v}=pcall(function() return {http_v}:GenerateGUID(false) end) if {g_ok_v} and (type({g_v})~='string' or #{g_v}<10) then {kill_v}() end "
            f"local {j_ok_v},{j_v}=pcall(function() return {http_v}:JSONDecode({http_v}:JSONEncode({{a=1}})) end) if {j_ok_v} and ({j_v}==nil or {j_v}.a~=1) then {kill_v}() end "
            f"end end "
        )
        parts.append(
            f"do local {ok1_v},{p_v}=pcall(Instance.new,{enc_call('Part')}) "
            f"if not {ok1_v} or typeof({p_v})~={enc_call('Instance')} or {p_v}.ClassName~={enc_call('Part')} then {kill_v}() end "
            f"{p_v}.Shape=Enum.PartType.Cylinder {p_v}.Position=Vector3.new(10,20,30) {p_v}.Size=Vector3.new(2,4,6) "
            f"if {p_v}.Shape~=Enum.PartType.Cylinder or {p_v}.Position.X~=10 or {p_v}.Size.Y~=4 then {kill_v}() end "
            f"{p_v}:Destroy() end "
        )
        parts.append(
            f"if type(Vector3.new())~='userdata' or typeof(Vector3.new())~='Vector3' then {kill_v}() end "
            f"if type(CFrame.new())~='userdata' or typeof(CFrame.new())~='CFrame' then {kill_v}() end "
            f"if type(Color3.new())~='userdata' or typeof(Color3.new())~='Color3' then {kill_v}() end "
            f"if type(UDim2.new())~='userdata' or typeof(UDim2.new())~='UDim2' then {kill_v}() end "
            f"do local {v1_v}=Vector3.new(1,2,3) local {v2_v}=Vector3.new(1.00001,2.00001,3.00001) if not {v1_v}:FuzzyEq({v2_v},0.001) or {v1_v}:FuzzyEq(Vector3.new(4,5,6),0.001) then {kill_v}() end end "
            f"do local {cf_inv_v}=CFrame.new(10,20,30) local {inv_v}={cf_inv_v}:Inverse() local {id_v}={cf_inv_v}*{inv_v} if math.abs({id_v}.Position.X)>0.001 or math.abs({id_v}.Position.Y)>0.001 or math.abs({id_v}.Position.Z)>0.001 then {kill_v}() end end "
            f"do local {u_v}=UDim2.fromOffset(10,5) if {u_v}.X.Offset~=10 or {u_v}.Y.Offset~=5 then {kill_v}() end end "
            f"if Enum.PartType.Cylinder.Name~='Cylinder' or Enum.PartType.Cylinder.Value~=2 or tostring(Enum.PartType.Cylinder.EnumType)~='PartType' then {kill_v}() end "
        )
        parts.append(
            f"do local {th_v}=task.spawn(function() end) task.cancel({th_v}) if type({th_v})~='thread' or typeof({th_v})~='thread' then {kill_v}() end end "
        )
        bad_globals_list = [
            "__LUNE__", "__LUTE__", "wally", "rojo",
            "selene", "darklua", "remodel",
            "MobDebug", "remdebug", "ldb", "BreakpointHook",
            "__BREAKPOINT__", "__DEBUG__", "__ATTACHED__",
        ]
        bad_globals_expr = "{" + ",".join(enc_call(bg) for bg in bad_globals_list) + "}"

        bad_mods_list = [
            "@lune/fs", "@lune/process", "@lune/net",
            "@lune/task", "@lune/luau", "@lune/roblox",
            "@lune/serde", "@lune/stdio", "@lune/datetime",
            "@lune/crypto",
            "@lute/fs", "@lute/net", "@lute/process",
            "@std/fs", "@std/net", "@std/process",
        ]
        bad_mods_expr = "{" + ",".join(enc_call(bm) for bm in bad_mods_list) + "}"

        parts.append(
            f"do local {pkg_v}=package if type({pkg_v})=='table' then "
            f"if rawget({pkg_v},{enc_call('lune')}) or rawget({pkg_v},{enc_call('lute')}) or rawget({pkg_v},{enc_call('wally')}) or rawget({pkg_v},{enc_call('rojo')}) then {kill_v}() end "
            f"end end "
            f"do local {ev_v}=(getfenv and getfenv(0)) or _ENV or _G or {{}} "
            f"local {bad_globals_v}={bad_globals_expr} "
            f"for _,{bg_v} in ipairs({bad_globals_v}) do if rawget({ev_v},{bg_v})~=nil then {kill_v}() end end "
            f"end "
            f"do local {req_v}=require if type({req_v})=='function' then "
            f"local {bad_mods_v}={bad_mods_expr} "
            f"for _,{bm_v} in ipairs({bad_mods_v}) do local {ok_v},{res_v}=pcall({req_v},{bm_v}) if {ok_v} and {res_v}~=nil then {sus_v}={sus_v}+1 end end "
            f"end end "
            f"if {sus_v}>0 then {kill_v}() end "
        )

    return "".join(parts)


def build_anti_tamper(seeds, rng, var_k, encode_fn, detect_var=None, level="full", version="v2", target="luau"):
    if version == "v1":
        return build_anti_tamper_v1(seeds, rng, var_k, encode_fn, detect_var=detect_var, level=level)
    return build_anti_tamper_v2(seeds, rng, var_k, encode_fn, detect_var=detect_var, target=target, level=level)


def build_runtime_footer(var_Q, var_G):
    return f"end)(getfenv and getfenv() or _ENV,table.unpack or unpack,{{}},{{}},nil,{{}}) end)(...)"
    
