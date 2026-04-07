import random
import string
import hashlib
import re
import sys

LCG_MOD = 2147483647

def lcg_next(s, a=48271):
    return (s * a) % LCG_MOD

def lcg_next2(s, a=69621):
    return (s * a) % LCG_MOD

def build_alphabet(seed):
    chars = [chr(i) for i in range(33, 127) if i not in (34, 39, 92)]
    v = seed
    for i in range(len(chars), 1, -1):
        v = lcg_next(v)
        j = v % i
        chars[i - 1], chars[j] = chars[j], chars[i - 1]
    return "".join(chars)

SEED_P = 1322857472
SEED_Q = 2984711168
SEED_R = 976564224
SEED_S = 4059994112
SEED_T = 1099760103
SEED_U = 724178073
SEED_BK = 3578128

def encode_string(text, call_id, alphabet_seed):
    alphabet = build_alphabet(alphabet_seed)
    N = len(alphabet)
    data = [ord(c) for c in text]
    s0 = (SEED_T + call_id + SEED_P) % LCG_MOD
    s1 = (SEED_U + call_id + SEED_BK + SEED_Q) % LCG_MOD
    m3 = SEED_R % 256
    m4 = SEED_S % 256
    if s0 == 0: s0 = 1
    if s1 == 0: s1 = 1
    encrypted = []
    for i, byte in enumerate(data, 1):
        s0 = lcg_next(s0)
        s1 = lcg_next2(s1)
        k = (s0 + s1 + m3 + m4 * i) % 256
        enc = (byte + k) % 256
        encrypted.append(enc)
        s0 = (s0 + enc) % LCG_MOD
    result = []
    for b in encrypted:
        hi = b // N
        lo = b % N
        if hi >= N or lo >= N:
            return None
        result.append(alphabet[hi])
        result.append(alphabet[lo])
    return "".join(result)

def decode_string(encoded, call_id, alphabet_seed):
    alphabet = build_alphabet(alphabet_seed)
    N = len(alphabet)
    ra = {ord(c): i + 1 for i, c in enumerate(alphabet)}
    pairs = []
    for i in range(0, len(encoded), 2):
        h = ra.get(ord(encoded[i]))
        l = ra.get(ord(encoded[i + 1]))
        if h is None or l is None:
            return None
        pairs.append((h - 1) * N + (l - 1))
    s0 = (SEED_T + call_id + SEED_P) % LCG_MOD
    s1 = (SEED_U + call_id + SEED_BK + SEED_Q) % LCG_MOD
    m3 = SEED_R % 256
    m4 = SEED_S % 256
    if s0 == 0: s0 = 1
    if s1 == 0: s1 = 1
    result = []
    for i, enc in enumerate(pairs, 1):
        s0 = lcg_next(s0)
        s1 = lcg_next2(s1)
        k = (s0 + s1 + m3 + m4 * i) % 256
        result.append(chr((enc - k) % 256))
        s0 = (s0 + enc) % LCG_MOD
    return "".join(result)

_name_counter = 0
_used_names = set()

def reset_names():
    global _name_counter, _used_names
    _name_counter = 0
    _used_names = set()

def gen_name():
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
        name = random.choice(string.ascii_lowercase) + name
    return name

def minify_lua(code):
    lines = code.split('\n')
    parts = []
    for line in lines:
        s = line.strip()
        if s:
            parts.append(s)
    joined = ';'.join(parts)
    joined = re.sub(r'\{;+', '{', joined)
    while ';;' in joined:
        joined = joined.replace(';;', ';')
    return joined

class WeakObfuscator:
    def __init__(self, source, watermark="Weak_Obfuscator"):
        self.source = source
        self.watermark = watermark
        self.rng = random.Random(hashlib.md5(source.encode()).hexdigest())
        self.alphabet_seed = self.rng.randint(10_000_000, 99_999_999)
        self.call_counter = 0
        self.string_cache = {}
        reset_names()

        self.V = gen_name()
        self.k = gen_name()
        self.f = gen_name()
        self.B = gen_name()
        self.n = gen_name()
        self.Q = gen_name()
        self.G = gen_name()
        self.y = gen_name()
        self.o = gen_name()
        self.S = gen_name()
        self.e = gen_name()
        self.z = gen_name()
        self.h = gen_name()
        self.r = gen_name()

        self.wm_var = f"Weak_Obfuscator_{self.rng.randint(10**18, 10**19 - 1)}"

    def next_call_id(self):
        self.call_counter += 1
        return self.call_counter

    def encode(self, text):
        call_id = self.next_call_id()
        encoded = encode_string(text, call_id, self.alphabet_seed)
        if encoded is None:
            call_id = self.next_call_id()
            encoded = encode_string(text, call_id, self.alphabet_seed)
        return encoded, call_id

    def k_call(self, text, ret_type=1):
        encoded, call_id = self.encode(text)
        s0 = self.rng.randint(100000, 2**31 - 1)
        s2 = self.rng.randint(100000, 2**31 - 1)
        s3 = self.rng.randint(100000, 2**31 - 1)
        return f'{self.k}("{encoded}",{ret_type},{s0},{call_id},{call_id},{s2},{s3})'

    def build_runtime_header(self):
        wm = self.wm_var
        alg_seed = self.alphabet_seed
        Q, k, f, B, G, V = self.Q, self.k, self.f, self.B, self.G, self.V

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

        return (
            f'do ("This file was protected with Weak Obfuscator."):gsub(".+",function(q){wm}=q end) end '
            f"return (function(...) return(function({Q},{G},{B},{f},{k},{V}) "
            f"local {p_v},{q_v},{r_v},{s_v}={SEED_P},{SEED_Q},{SEED_R},{SEED_S} "
            f"local {t_v},{u_v}={SEED_T},{SEED_U} "
            f"local {bk_v}={SEED_BK} "
            f"local _F=math.floor local {sb}=string.byte local {sc}=string.char "
            f"local function {lcg1}(s) return(s*48271)%2147483647 end "
            f"local function {lcg2}(s) return(s*69621)%2147483647 end "
            f"local function {shuffle}(seed) local c={{}} for i=33,126,1 do if i~=34 and(i~=39 and i~=92) then c[#c+1]=string.char(i) end end local v=seed for i=#c,2,-1 do v={lcg1}(v) local j=v%i+1 c[i],c[j]=c[j],c[i] end return table.concat(c) end "
            f"local {alpha_v}={shuffle}({alg_seed}) "
            f"local {N_v}=#{alpha_v} "
            f"local {RA_v}={{}} "
            f"for _ri=1,{N_v},1 do {RA_v}[{sb}({alpha_v},_ri)]=_ri end "
            f"local function {g3}(a) if type(a)~='string' then return nil end local al=#a if al%2~=0 then return nil end local o={{}} for i=1,al,2 do local h={RA_v}[{sb}(a,i)] local l={RA_v}[{sb}(a,i+1)] if not h or not l then return nil end local kk=(h-1)*{N_v}+(l-1) if kk<0 or kk>255 then return nil end o[#o+1]=kk end return o end "
            f"local function {g5}(E,i0,i1) local o={{}} local s0=(i0+{p_v})%2147483647 local s1=(i1+{q_v})%2147483647 local m3={r_v}%256 local m4={s_v}%256 if s0==0 then s0=1 end if s1==0 then s1=1 end for i=1,#E,1 do s0={lcg1}(s0) s1={lcg2}(s1) local kk=((s0+s1)+m3+m4*i)%256 local ct=E[i] o[i]=(ct-kk)%256 s0=(s0+ct)%2147483647 end return o end "
            f"local {CC_v}={{}} "
            f"{k}=function(a,b1,b2,b3,b4,d1,d2) local ck=b3 if {CC_v}[ck]~=nil then return {CC_v}[ck] end local d={g3}(a) if not d then return nil end local c0={t_v}+b3 local c1=({u_v}+b4)+{bk_v} local Y={g5}(d,c0,c1) local o={{}} for i=1,#Y,1 do o[i]={sc}(Y[i]%256) end local v=table.concat(o) local result if b1==1 then result=v elseif b1==2 then local n=tonumber(v) result=n==nil and 0 or n elseif b1==3 then result=v=='1' end {CC_v}[ck]=result return result end "
        )

    def build_vm_dispatch(self):
        V = self.V
        rng = self.rng

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

        dispatch_table = f"local {V}={{{';'.join(dispatch_lines)}}} "
        return dispatch_table, hashes

    def wrap_globals(self, source, hashes):
        k = self.k
        global_names = [
            "print","tostring","tonumber","type","error","pcall","xpcall",
            "setmetatable","getmetatable","rawget","rawset","rawequal","rawlen",
            "select","ipairs","pairs","next","unpack","table","string","math",
            "coroutine","require","loadstring","loadfile","load","dofile",
            "collectgarbage","gcinfo","newproxy","getfenv","setfenv",
            "game","workspace","script","plugin","shared",
            "task","warn","wait","delay","spawn","tick","time",
            "Vector2","Vector3","CFrame","Color3","UDim","UDim2",
            "BrickColor","Enum","Instance","Ray","Region3","NumberRange",
            "TweenInfo","PhysicalProperties","Font","Axes","Faces",
            "os","io","bit32","utf8","buffer",
        ]
        result_lines = []
        for name in global_names:
            encoded, cid = self.encode(name)
            s0 = self.rng.randint(100000, 2**31 - 1)
            s2 = self.rng.randint(100000, 2**31 - 1)
            s3 = self.rng.randint(100000, 2**31 - 1)
            result_lines.append(
                f'[{k}("{encoded}",1,{s0},{cid},{cid},{s2},{s3})]={name}'
            )
        return f"local _ENV_MAP={{{';'.join(result_lines)}}}\n"

    def build_anti_tamper(self):
        rng  = self.rng
        k    = self.k

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

        m1 = rng.randint(0x2000, 0xEFFF)
        m2 = rng.randint(0x2000, 0xEFFF)
        m3 = rng.randint(0x2000, 0xEFFF)
        timing_limit = 3.0
        loop_count   = 100000

        debugger_names = ["MobDebug","remdebug","RemDebug","LuaSocket","ldb","__debugger","BreakpointHook"]
        enc_debuggers = []
        for dn in debugger_names:
            enc, cid = self.encode(dn)
            s0 = rng.randint(100000, 2**31 - 1)
            s2 = rng.randint(100000, 2**31 - 1)
            s3 = rng.randint(100000, 2**31 - 1)
            enc_debuggers.append(f'{k}("{enc}",1,{s0},{cid},{cid},{s2},{s3})')

        debugger_checks = "\n".join(
            f"if rawget({ev_v},{enc})~=nil then {kill_v}() end"
            for enc in enc_debuggers
        )

        dc = " ".join(
            f"if rawget({ev_v},{enc})~=nil then {kill_v}() end"
            for enc in enc_debuggers
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
            f"local {ev_v}=(getfenv and getfenv(0)) or _ENV or {{}} "
            f"if type({ev_v})~='table' then {kill_v}() end "
            f"{dc} "
            f"if rawget({ev_v},'__BREAKPOINT__')~=nil then {kill_v}() end "
            f"if rawget({ev_v},'__DEBUG__')~=nil then {kill_v}() end "
            f"if rawget({ev_v},'__ATTACHED__')~=nil then {kill_v}() end "
            f"if rawget({ev_v},'syn') and rawget(rawget({ev_v},'syn'),'is_executor_closure') then {kill_v}() end "
        )

    def build_runtime_footer(self):
        Q = self.Q
        G = self.G
        return f"end)(getfenv and getfenv() or _ENV,table.unpack or unpack,{{}},{{}},nil,{{}}) end)(...)"

    def obfuscate(self):
        source = self.source
        dispatch_table, hashes = self.build_vm_dispatch()
        src_encoded, src_cid = self.encode(source)
        s0 = self.rng.randint(100000, 2**31 - 1)
        s2 = self.rng.randint(100000, 2**31 - 1)
        s3 = self.rng.randint(100000, 2**31 - 1)

        k = self.k

        banner = f"""--[[
  Protected by Weak Obfuscator v1.0

  Weak Obfuscator: https://github.com/Melodieshusband/Weak-Lua-Obfuscator
]]"""

        header      = self.build_runtime_header()
        anti_tamper = self.build_anti_tamper()

        sm_var = gen_name()
        fn_var = gen_name()
        ok_var = gen_name()
        er_var = gen_name()
        sid1 = self.rng.randint(1000000, 5000000)
        sid2 = self.rng.randint(5000001, 9000000)
        sid3 = self.rng.randint(9000001, 13000000)
        sid4 = self.rng.randint(13000001, 16000000)

        junk_sids = [self.rng.randint(1000000, 16000000) for _ in range(10)]
        junk_parts = " ".join(
            f"elseif {sm_var}=={sid} then local _d{self.rng.randint(1000,9999)}={self.rng.randint(0,65535)}"
            for sid in junk_sids
        )

        err_enc, err_cid = self.encode('Script protection fault')
        s0e = self.rng.randint(100000, 2**31 - 1)
        s2e = self.rng.randint(100000, 2**31 - 1)
        s3e = self.rng.randint(100000, 2**31 - 1)

        body = (
            f"{anti_tamper}"
            f"{dispatch_table}"
            f"local {sm_var}={sid1} "
            f"while {sm_var} do "
            f"if {sm_var}<{sid2} then "
            f"if {sm_var}=={sid1} then {sm_var}={sid2} "
            f"{junk_parts} "
            f"end "
            f"elseif {sm_var}=={sid2} then "
            f"local {fn_var},{er_var}=(loadstring or load)({k}(\"{src_encoded}\",1,{s0},{src_cid},{src_cid},{s2},{s3})) "
            f"if not {fn_var} then {sm_var}={sid4} "
            f"else local {ok_var},{er_var}=pcall({fn_var}) "
            f"if {ok_var} then {sm_var}={sid3} else {sm_var}={sid4} end "
            f"end "
            f"elseif {sm_var}=={sid3} then break "
            f"elseif {sm_var}=={sid4} then "
            f"error({k}(\"{err_enc}\",1,{s0e},{err_cid},{err_cid},{s2e},{s3e}),2) "
            f"end end "
        )

        footer = self.build_runtime_footer()
        full_code = header + body + footer

        return banner + "\n" + full_code


def main():
    if len(sys.argv) < 2:
        print("Usage: python obfuscator.py <input.lua> [output.lua]")
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace(".lua", "_obf.lua")

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    obf    = WeakObfuscator(source, watermark="Weak_Obfuscator")
    result = obf.obfuscate()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"[+] Obfuscated:    {input_path} -> {output_path}")
    print(f"[+] Alphabet seed: {obf.alphabet_seed}")
    print(f"[+] Watermark var: {obf.wm_var}")
    print(f"[+] Call counter:  {obf.call_counter}")

if __name__ == "__main__":
    main()
