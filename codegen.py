import random
import string
from crypto import lcg_next, build_alphabet, LCG_MOD

_name_counter = 0
_used_names = set()

def reset_names():
    global _name_counter, _used_names
    _name_counter = 0
    _used_names = set()

def gen_name(rng=None):
    global _name_counter
    _name_counter += 1
    n = _name_counter
    chars = string.ascii_letters
    result = []
    while n > 0:
        n -= 1
        result.append(chars[n % len(chars)])
        n //= len(chars)
    name = "".join(reversed(result))
    while len(name) < 6:
        if rng:
            name = rng.choice(string.ascii_lowercase) + name
        else:
            name = random.choice(string.ascii_lowercase) + name
    return name

def build_runtime_header(seeds, alphabet_seed, var_k, var_Q, var_G, var_B, var_f, var_V, wm_var):
    lcg1    = gen_name()
    lcg2    = gen_name()
    shuffle = gen_name()
    alpha_v = gen_name()
    N_v     = gen_name()
    RA_v    = gen_name()
    g3      = gen_name()
    g5      = gen_name()
    CC_v    = gen_name()
    sb      = gen_name()
    sc      = gen_name()
    p_v     = gen_name()
    q_v     = gen_name()
    r_v     = gen_name()
    s_v     = gen_name()
    t_v     = gen_name()
    u_v     = gen_name()
    bk_v    = gen_name()
    a1_v    = gen_name()
    a2_v    = gen_name()

    P  = seeds["P"]
    Q  = seeds["Q"]
    R  = seeds["R"]
    S  = seeds["S"]
    T  = seeds["T"]
    U  = seeds["U"]
    BK = seeds["BK"]
    A1 = seeds["A1"]
    A2 = seeds["A2"]

    return (
        f'do ("This file was protected with Weak Obfuscator."):gsub(".+",function(q){wm_var}=q end) end '
        f"return (function(...) return(function({var_Q},{var_G},{var_B},{var_f},{var_k},{var_V}) "
        f"local {p_v},{q_v},{r_v},{s_v}={P},{Q},{R},{S} "
        f"local {t_v},{u_v}={T},{U} "
        f"local {bk_v}={BK} "
        f"local {a1_v},{a2_v}={A1},{A2} "
        f"local _F=math.floor local {sb}=string.byte local {sc}=string.char "
        f"local function {lcg1}(s) return(s*{a1_v})%{LCG_MOD} end "
        f"local function {lcg2}(s) return(s*{a2_v})%{LCG_MOD} end "
        f"local function {shuffle}(seed) local c={{}} for i=33,126,1 do if i~=34 and(i~=39 and i~=92) then c[#c+1]=string.char(i) end end local v=seed for i=#c,2,-1 do v={lcg1}(v) local j=v%i+1 c[i],c[j]=c[j],c[i] end return table.concat(c) end "
        f"local {alpha_v}={shuffle}({alphabet_seed}) "
        f"local {N_v}=#{alpha_v} "
        f"local {RA_v}={{}} "
        f"for _ri=1,{N_v},1 do {RA_v}[{sb}({alpha_v},_ri)]=_ri end "
        f"local function {g3}(a) if type(a)~='string' then return nil end local al=#a if al%2~=0 then return nil end local o={{}} for i=1,al,2 do local h={RA_v}[{sb}(a,i)] local l={RA_v}[{sb}(a,i+1)] if not h or not l then return nil end local kk=(h-1)*{N_v}+(l-1) if kk<0 or kk>255 then return nil end o[#o+1]=kk end return o end "
        f"local function {g5}(E,i0,i1) local o={{}} local s0=(i0+{p_v})%{LCG_MOD} local s1=(i1+{q_v})%{LCG_MOD} local m3={r_v}%256 local m4={s_v}%256 if s0==0 then s0=1 end if s1==0 then s1=1 end for i=1,#E,1 do s0={lcg1}(s0) s1={lcg2}(s1) local kk=((s0+s1)+m3+m4*i)%256 local ct=E[i] o[i]=(ct-kk)%256 s0=(s0+ct)%{LCG_MOD} end return o end "
        f"local {CC_v}={{}} "
        f"{var_k}=function(a,b1,b2,b3,b4,d1,d2) local ck=b3 if {CC_v}[ck]~=nil then return {CC_v}[ck] end local d={g3}(a) if not d then return nil end local c0={t_v}+b3 local c1=({u_v}+b4)+{bk_v} local Y={g5}(d,c0,c1) local o={{}} for i=1,#Y,1 do o[i]={sc}(Y[i]%256) end local v=table.concat(o) local result if b1==1 then result=v elseif b1==2 then local n=tonumber(v) result=n==nil and 0 or n elseif b1==3 then result=v=='1' end {CC_v}[ck]=result return result end "
    )

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

    return (
        f"local {kill_v} {kill_v}=function() error('',0) local _z=true while _z do if task then task.wait(0) elseif coroutine then coroutine.yield() end error('',0) end end "
        f"local {db_v}=debug "
        f"if type(rawget)~='function' then {kill_v}() end "
        f"if type(rawset)~='function' then {kill_v}() end "
        f"if type(setmetatable)~='function' then {kill_v}() end "
        f"if type(getmetatable)~='function' then {kill_v}() end "
        f"if type(pcall)~='function' then {kill_v}() end "
        f"if type(xpcall)~='function' then {kill_v}() end "
        f"if type(error)~='function' then {kill_v}() end "
        f"if type(type)~='function' then {kill_v}() end "
        f"if type(tostring)~='function' then {kill_v}() end "
        f"if type(tonumber)~='function' then {kill_v}() end "
        f"if type(select)~='function' then {kill_v}() end "
        f"if type(ipairs)~='function' then {kill_v}() end "
        f"if type(pairs)~='function' then {kill_v}() end "
        f"if type(next)~='function' then {kill_v}() end "
        f"if type(unpack or table.unpack)~='function' then {kill_v}() end "
        f"if type(string.byte)~='function' then {kill_v}() end "
        f"if type(string.char)~='function' then {kill_v}() end "
        f"if type(string.len)~='function' then {kill_v}() end "
        f"if type(string.sub)~='function' then {kill_v}() end "
        f"if type(string.rep)~='function' then {kill_v}() end "
        f"if type(string.find)~='function' then {kill_v}() end "
        f"if type(string.format)~='function' then {kill_v}() end "
        f"if type(table.concat)~='function' then {kill_v}() end "
        f"if type(table.insert)~='function' then {kill_v}() end "
        f"if type(table.remove)~='function' then {kill_v}() end "
        f"if type(math.floor)~='function' then {kill_v}() end "
        f"if type(math.abs)~='function' then {kill_v}() end "
        f"if type(math.huge)~='number' then {kill_v}() end "
        f"if type(_VERSION)~='string' then {kill_v}() end "
        f"if not(1/0==math.huge) then {kill_v}() end "
        f"if not(math.huge==math.huge*2) then {kill_v}() end "
        f"if not(0/0~=0/0) then {kill_v}() end "
        f"if not(-1/0==-math.huge) then {kill_v}() end "
        f"if math.abs(-{m1})~={m1} then {kill_v}() end "
        f"if math.floor({m1}+0.9)~={m1} then {kill_v}() end "
        f"do local {ok_v},{er_v}=pcall(function() error({m1}) end) if {ok_v} then {kill_v}() end if type({er_v})~='string' then {kill_v}() end end "
        f"do local {ti_v}=os and type(os.clock)=='function' and os.clock or (type(tick)=='function' and tick) or nil local {t0_v}={ti_v} and {ti_v}() or 0 local {acc_v}=0 for _=1,{loop_count} do {acc_v}={acc_v}+1 end local {t1_v}={ti_v} and {ti_v}() or 0 if {acc_v}~={loop_count} then {kill_v}() end if {ti_v} and ({t1_v}-{t0_v})>{timing_limit} then {kill_v}() end end "
        f"do local {tb_v}={{}} local _trap=false local {mt_v}={{__newindex=function() _trap=true end,__index=function() _trap=true end}} setmetatable({tb_v},{mt_v}) local {ok_v}=pcall(function() {tb_v}[{m2}]={m3} end) setmetatable({tb_v},nil) if not _trap then {kill_v}() end end "
        f"do local {fn_v}=function(x) return x*{m2}+{m3} end if type({fn_v})~='function' then {kill_v}() end if {fn_v}(0)~={m3} then {kill_v}() end if {fn_v}(1)~={m2}+{m3} then {kill_v}() end local {ok_v},{er_v}=pcall({fn_v},'z') if {ok_v} then {kill_v}() end end "
        f"do local _n=tostring({m1}+{m2}) if type(_n)~='string' then {kill_v}() end if tonumber(_n)~=({m1}+{m2}) then {kill_v}() end end "
        f"do local _orig_type=type if _orig_type({m1})~='number' then {kill_v}() end if _orig_type('')~='string' then {kill_v}() end if _orig_type({{}})~='table' then {kill_v}() end if _orig_type(nil)~='nil' then {kill_v}() end if _orig_type(true)~='boolean' then {kill_v}() end if _orig_type(_orig_type)~='function' then {kill_v}() end end "
        f"do local {ch_v}=tostring({m1}):rep(3) if #{ch_v}~=3*#tostring({m1}) then {kill_v}() end end "
        f"local {ev_v}=(getfenv and getfenv(0)) or _ENV or {{}} "
        f"if type({ev_v})~='table' then {kill_v}() end "
        f"{dc} "
        f"{exec_checks} "
        f"if rawget({ev_v},'__BREAKPOINT__')~=nil then {kill_v}() end "
        f"if rawget({ev_v},'__DEBUG__')~=nil then {kill_v}() end "
        f"if rawget({ev_v},'__ATTACHED__')~=nil then {kill_v}() end "
        # syn check removed - kills modern executors
    )

def build_runtime_footer(var_Q, var_G):
    return f"end)(getfenv and getfenv() or _ENV,table.unpack or unpack,{{}},{{}},nil,{{}}) end)(...)"
