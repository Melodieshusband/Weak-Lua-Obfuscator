import random
import string
import secrets
from crypto import CHACHA_CONST, CHACHA_ROUNDS, MASK32

_used_names = set()
_name_rng = None

_CONFUSABLES = ["l", "I", "O", "o", "0", "1"]

def reset_names():
    global _used_names, _name_rng
    _used_names = set()
    _name_rng = random.Random(secrets.randbits(128))

def gen_name(rng=None):
    r = rng or _name_rng or random
    while True:
        length = r.randint(6, 10)
        first = r.choice(string.ascii_letters + "_")
        rest = "".join(r.choice(_CONFUSABLES) for _ in range(length - 1))
        name = first + rest
        if name not in _used_names:
            _used_names.add(name)
            return name

def build_runtime_header(seeds, alphabet_seed, var_k, var_Q, var_G, var_B, var_f, var_V, wm_var):
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

    key = seeds["KEY"]
    nonce_base = seeds["NONCE_BASE"]
    c0, c1, c2, c3 = CHACHA_CONST

    band  = "bit32.band"
    bxor  = "bit32.bxor"
    lrot  = "bit32.lrotate"

    return (
        f'do ("This file was protected with Weak Obfuscator."):gsub(".+",function(q){wm_var}=q end) end '
        f"return (function(...) return(function({var_Q},{var_G},{var_B},{var_f},{var_k},{var_V}) "
        f"local {key_v}={{{','.join(str(k) for k in key)}}} "
        f"local {nb_v}={nonce_base} "
        f"local _F=math.floor local {sb}=string.byte local {sc}=string.char "
        f"local function {xorb_v}(a,b) return {bxor}(a,b) end "
        f"local function {qr_v}({st_v},a,b,c,d) "
        f"{st_v}[a]=({st_v}[a]+{st_v}[b])%4294967296 "
        f"{st_v}[d]={lrot}({xorb_v}({st_v}[d],{st_v}[a]),16) "
        f"{st_v}[c]=({st_v}[c]+{st_v}[d])%4294967296 "
        f"{st_v}[b]={lrot}({xorb_v}({st_v}[b],{st_v}[c]),12) "
        f"{st_v}[a]=({st_v}[a]+{st_v}[b])%4294967296 "
        f"{st_v}[d]={lrot}({xorb_v}({st_v}[d],{st_v}[a]),8) "
        f"{st_v}[c]=({st_v}[c]+{st_v}[d])%4294967296 "
        f"{st_v}[b]={lrot}({xorb_v}({st_v}[b],{st_v}[c]),7) "
        f"end "
        f"local function {blk_v}(counter,n1,n2,n3) "
        f"local {st_v}={{{c0},{c1},{c2},{c3},"
        f"{key_v}[1],{key_v}[2],{key_v}[3],{key_v}[4],{key_v}[5],{key_v}[6],{key_v}[7],{key_v}[8],"
        f"counter,n1,n2,n3}} "
        f"local {w_v}={{}} for i=1,16,1 do {w_v}[i]={st_v}[i] end "
        f"for _=1,{CHACHA_ROUNDS // 2},1 do "
        f"{qr_v}({w_v},1,5,9,13) {qr_v}({w_v},2,6,10,14) {qr_v}({w_v},3,7,11,15) {qr_v}({w_v},4,8,12,16) "
        f"{qr_v}({w_v},1,6,11,16) {qr_v}({w_v},2,7,12,13) {qr_v}({w_v},3,8,9,14) {qr_v}({w_v},4,5,10,15) "
        f"end "
        f"local out={{}} for i=1,16,1 do out[i]=({w_v}[i]+{st_v}[i])%4294967296 end "
        f"return out end "
        f"local function {ks_v}(n1,n2,outlen) "
        f"local out={{}} local counter=0 local pos=0 "
        f"while pos<outlen do "
        f"local words={blk_v}(counter,0,n1,n2) "
        f"for i=1,16,1 do "
        f"local wv=words[i] "
        f"out[pos+1]=wv%256 "
        f"out[pos+2]=_F(wv/256)%256 "
        f"out[pos+3]=_F(wv/65536)%256 "
        f"out[pos+4]=_F(wv/16777216)%256 "
        f"pos=pos+4 "
        f"if pos>=outlen then break end "
        f"end "
        f"counter=(counter+1)%4294967296 "
        f"end "
        f"return out end "
        f"local function {shuffle}(seed) "
        f"local c={{}} for i=33,126,1 do if i~=34 and(i~=39 and i~=92) then c[#c+1]=string.char(i) end end "
        f"local ks={ks_v}(seed,2779096485,#c*4) "
        f"for i=#c,2,-1 do "
        f"local base=(i-1)*4 "
        f"local v=ks[base+1]+ks[base+2]*256+ks[base+3]*65536+ks[base+4]*16777216 "
        f"local j=v%i+1 "
        f"c[i],c[j]=c[j],c[i] "
        f"end "
        f"return table.concat(c) end "
        f"local {alpha_v}={shuffle}({alphabet_seed}) "
        f"local {N_v}=#{alpha_v} "
        f"local {RA_v}={{}} "
        f"for _ri=1,{N_v},1 do {RA_v}[{sb}({alpha_v},_ri)]=_ri end "
        f"local function {g3}(a) if type(a)~='string' then return nil end local al=#a if al%2~=0 then return nil end local o={{}} for i=1,al,2 do local h={RA_v}[{sb}(a,i)] local l={RA_v}[{sb}(a,i+1)] if not h or not l then return nil end local kk=(h-1)*{N_v}+(l-1) if kk<0 or kk>255 then return nil end o[#o+1]=kk end return o end "
        f"local {CC_v}={{}} "
        f"{var_k}=function(a,b1,b2,b3,b4,d1,d2) local ck=b3*{seeds['MK']}+b1 if {CC_v}[ck]~=nil then return {CC_v}[ck] end "
        f"local d={g3}(a) if not d then return nil end "
        f"local nonce_lo=b3%4294967296 local nonce_hi={xorb_v}(b3,{nb_v}) "
        f"local ks={ks_v}(nonce_lo,nonce_hi,#d) "
        f"local o={{}} for i=1,#d,1 do o[i]={sc}({xorb_v}(d[i],ks[i])%256) end "
        f"local v=table.concat(o) local result if b1==1 then result=v elseif b1==2 then local n=tonumber(v) result=n==nil and 0 or n elseif b1==3 then result=v=='1' end {CC_v}[ck]=result return result end "
    ), {"ks": ks_v, "xorb": xorb_v, "nb": nb_v, "sc": sc}

def build_vm_dispatch(var_V, rng):
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

    hashes = {}
    dispatch_lines = []
    for op_name, (params, expr) in ops.items():
        count = rng.randint(3, 8)
        for _ in range(count):
            h = rng.randint(0x10000000, 0xFFFFFFFF)
            while h in hashes:
                h = rng.randint(0x10000000, 0xFFFFFFFF)
            hashes[op_name] = h
            dispatch_lines.append(f"[{h}]=function({params}) return {expr} end")

    dispatch_table = f"local {var_V}={{{';'.join(dispatch_lines)}}} "
    return dispatch_table, hashes

def build_anti_tamper(seeds, rng, var_k, encode_fn):
    kill_v  = gen_name()
    db_v    = gen_name()
    t0_v    = gen_name()
    t1_v    = gen_name()
    ti_v    = gen_name()
    acc_v   = gen_name()
    ev_v    = gen_name()
    mt_v    = gen_name()
    tb_v    = gen_name()
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
        # Убраны стандартные executor API (getgenv, hookfunction, etc.)
        # которые есть в любом нормальном executor'е и не являются признаком отладки
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
    ]

    lute_modules = [
        "@lute/fs", "@lute/net", "@lute/task", "@lute/process",
        "@lute/crypto", "@lute/luau", "@lute/vm", "@lute/time",
        "@std/fs", "@std/net", "@std/task", "@std/process",
        "@std/crypto", "@std/luau", "@std/io", "@std/testing",
        "@std/assert", "@std/lint",
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

    decoy_message = "Melodie doesn't approve of skidding be a good boy"
    decoy_enc = enc_call(decoy_message)

    def build_kill_v():
        variant = rng.randint(1, 4)
        wait_expr = rng.choice([
            "if task then task.wait(0) elseif coroutine then coroutine.yield() end",
            "if coroutine then coroutine.yield() elseif task then task.wait(0) end",
            "if wait then wait(0) elseif task then task.wait(0) end",
        ])
        junk1 = rng.randint(1000, 9999)
        junk2 = rng.randint(1000, 9999)
        if variant == 1:
            return f"function() error('',0) local _z=true while _z do {wait_expr} error('',0) end end"
        elif variant == 2:
            return f"function() local _k={junk1} while true do _k=_k+1 {wait_expr} if _k>{junk1} then error('',0) end end end"
        elif variant == 3:
            return f"function() local _k=0 repeat _k=_k+1 {wait_expr} error('',0) until _k<0 end"
        else:
            return f"function() local _f local _g=function() {wait_expr} error('',0) return _f() end _f=_g return _g() end"

    kill_body = build_kill_v()

    return (
        f"local {sus_v}=0 "
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
        f"do local {ti_v}=os and {otype_v}(os.clock)=='function' and os.clock or ({otype_v}(tick)=='function' and tick) or nil local {t0_v}={ti_v} and {ti_v}() or 0 local {acc_v}=0 for _=1,{loop_count} do {acc_v}={acc_v}+1 end local {t1_v}={ti_v} and {ti_v}() or 0 if {acc_v}~={loop_count} then {kill_v}() end if {ti_v} and ({t1_v}-{t0_v})>{timing_limit} then {kill_v}() end end "
        f"do local {tb_v}={{}} local _trap=false local {mt_v}={{__newindex=function() _trap=true end,__index=function() _trap=true end}} setmetatable({tb_v},{mt_v}) local {ok_v}={opcall_v}(function() {tb_v}[{m2}]={m3} end) setmetatable({tb_v},nil) if not _trap then {kill_v}() end end "
        f"do local {fn_v}=function(x) return x*{m2}+{m3} end if {otype_v}({fn_v})~='function' then {kill_v}() end if {fn_v}(0)~={m3} then {kill_v}() end if {fn_v}(1)~={m2}+{m3} then {kill_v}() end local {ok_v},{er_v}={opcall_v}({fn_v},'z') if {ok_v} then {kill_v}() end end "
        f"do local _n={ostr_v}({m1}+{m2}) if {otype_v}(_n)~='string' then {kill_v}() end if tonumber(_n)~=({m1}+{m2}) then {kill_v}() end end "
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
        f"if type({lenv1_v})=='table' then {le_v}={lenv1_v} {lune_check_g} {lute_check_g} end "
        f"local {lok2_v},{lenv2_v}=pcall(function() return _ENV end) "
        f"if {lok2_v} and {lenv2_v} and type({lenv2_v})=='table' and {lenv2_v}~=_G then {le_v}={lenv2_v} {lune_check_g} {lute_check_g} end "
        f"do local {lok1_v},{lfn_v}=pcall(function() "
        f"local {ln_v}=load or loadstring "
        f"if type({ln_v})~='function' then return nil end "
        f"local {lk_v}={ln_v}('return _ENV') "
        f"if type({lk_v})~='function' then return nil end "
        f"return {lk_v}() end) "
        f"if {lok1_v} and {lfn_v} and type({lfn_v})=='table' and {lfn_v}~=_G then {le_v}={lfn_v} {lune_check_g} {lute_check_g} end end "
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
        # syn check removed - kills modern executors
    )

def build_runtime_footer(var_Q, var_G):
    return f"end)(getfenv and getfenv() or _ENV,table.unpack or unpack,{{}},{{}},nil,{{}}) end)(...)"
    
