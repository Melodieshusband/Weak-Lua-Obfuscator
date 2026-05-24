import random
import secrets
from crypto import make_seeds, encode_string
from codegen import (
    reset_names, gen_name,
    build_runtime_header, build_vm_dispatch,
    build_anti_tamper, build_runtime_footer,
)

MIN_CHUNKS = 3
MAX_CHUNKS = 7

def split_source(source, n):
    size = max(1, len(source) // n)
    chunks = []
    for i in range(n):
        start = i * size
        end = start + size if i < n - 1 else len(source)
        chunks.append(source[start:end])
    return [c for c in chunks if c]

class Obfuscator:
    def __init__(self, source, watermark="Weak_Obfuscator"):
        self.source = source
        self.watermark = watermark
        self.seeds = make_seeds()
        self.alphabet_seed = secrets.randbelow(89999999) + 10000000
        self.call_counter = 0
        self.rng = random.Random(secrets.randbits(128))
        reset_names()

        self.var_V = gen_name()
        self.var_k = gen_name()
        self.var_f = gen_name()
        self.var_B = gen_name()
        self.var_n = gen_name()
        self.var_Q = gen_name()
        self.var_G = gen_name()
        self.var_y = gen_name()
        self.var_o = gen_name()
        self.var_S = gen_name()
        self.var_e = gen_name()
        self.var_z = gen_name()
        self.var_h = gen_name()
        self.var_r = gen_name()

        self.wm_var = f"Weak_Obfuscator_{secrets.randbelow(10**19 - 10**18) + 10**18}"

    def next_call_id(self):
        self.call_counter += 1
        return self.call_counter

    def encode(self, text):
        call_id = self.next_call_id()
        encoded = encode_string(text, call_id, self.seeds, self.alphabet_seed)
        if encoded is None:
            call_id = self.next_call_id()
            encoded = encode_string(text, call_id, self.seeds, self.alphabet_seed)
        return encoded, call_id

    def k_call(self, text, ret_type=1):
        encoded, call_id = self.encode(text)
        s0 = self.rng.randint(100000, 2**31 - 1)
        s2 = self.rng.randint(100000, 2**31 - 1)
        s3 = self.rng.randint(100000, 2**31 - 1)
        return f'{self.var_k}("{encoded}",{ret_type},{s0},{call_id},{call_id},{s2},{s3})'

    def build_chunk_loader(self, chunks):
        rng = self.rng
        k = self.var_k

        buf_var   = gen_name()
        idx_var   = gen_name()
        fn_var    = gen_name()
        ok_var    = gen_name()
        er_var    = gen_name()
        ls_var    = gen_name()
        step_var  = gen_name()

        n = len(chunks)

        chunk_seeds = [make_seeds() for _ in chunks]
        chunk_alpha = [secrets.randbelow(89999999) + 10000000 for _ in chunks]

        encoded_chunks = []
        for i, chunk in enumerate(chunks):
            cseeds = chunk_seeds[i]
            calpha = chunk_alpha[i]
            cid = self.next_call_id()
            enc = encode_string(chunk, cid, cseeds, calpha)
            if enc is None:
                cid = self.next_call_id()
                enc = encode_string(chunk, cid, cseeds, calpha)
            encoded_chunks.append((enc, cid, cseeds, calpha))

        lines = []

        lines.append(f"local {ls_var}=loadstring or load ")
        lines.append(f"if type({ls_var})~='function' then error('',0) end ")
        lines.append(f"local {buf_var}='' ")

        for i, (enc, cid, cseeds, calpha) in enumerate(encoded_chunks):
            dv   = gen_name()
            lcg1 = gen_name()
            lcg2 = gen_name()
            shuf = gen_name()
            alp  = gen_name()
            Nv   = gen_name()
            RAv  = gen_name()
            g3v  = gen_name()
            g5v  = gen_name()
            sbv  = gen_name()
            scv  = gen_name()

            P  = cseeds["P"]
            Q  = cseeds["Q"]
            R  = cseeds["R"]
            S  = cseeds["S"]
            T  = cseeds["T"]
            U  = cseeds["U"]
            BK = cseeds["BK"]
            A1 = cseeds["A1"]
            A2 = cseeds["A2"]

            s0r = rng.randint(100000, 2**31 - 1)
            s2r = rng.randint(100000, 2**31 - 1)
            s3r = rng.randint(100000, 2**31 - 1)

            lines.append(f"do ")
            lines.append(f"local {sbv}=string.byte local {scv}=string.char ")
            lines.append(f"local function {lcg1}(s) return(s*{A1})%2147483647 end ")
            lines.append(f"local function {lcg2}(s) return(s*{A2})%2147483647 end ")
            lines.append(
                f"local function {shuf}(seed) local c={{}} for i=33,126 do "
                f"if i~=34 and i~=39 and i~=92 then c[#c+1]={scv}(i) end end "
                f"local v=seed for i=#c,2,-1 do v={lcg1}(v) local j=v%i+1 "
                f"c[i],c[j]=c[j],c[i] end return table.concat(c) end "
            )
            lines.append(f"local {alp}={shuf}({calpha}) ")
            lines.append(f"local {Nv}=#{alp} ")
            lines.append(f"local {RAv}={{}} for _i=1,{Nv} do {RAv}[{sbv}({alp},_i)]=_i end ")
            lines.append(
                f"local function {g3v}(a) if type(a)~='string' then return nil end "
                f"local al=#a if al%2~=0 then return nil end local o={{}} "
                f"for i=1,al,2 do local h={RAv}[{sbv}(a,i)] local l={RAv}[{sbv}(a,i+1)] "
                f"if not h or not l then return nil end "
                f"local kk=(h-1)*{Nv}+(l-1) if kk<0 or kk>255 then return nil end "
                f"o[#o+1]=kk end return o end "
            )
            lines.append(
                f"local function {g5v}(E,i0,i1) local o={{}} "
                f"local s0=(i0+{P})%2147483647 local s1=(i1+{Q})%2147483647 "
                f"local m3={R}%256 local m4={S}%256 "
                f"if s0==0 then s0=1 end if s1==0 then s1=1 end "
                f"for i=1,#E do s0={lcg1}(s0) s1={lcg2}(s1) "
                f"local kk=((s0+s1)+m3+m4*i)%256 local ct=E[i] "
                f"o[i]=(ct-kk)%256 s0=(s0+ct)%2147483647 end return o end "
            )
            lines.append(
                f"local {dv}={g3v}(\"{enc}\") "
                f"if {dv} then "
                f"local _Y={g5v}({dv},{T}+{cid},{U}+{cid}+{BK}) "
                f"local _o={{}} for i=1,#_Y do _o[i]={scv}(_Y[i]%256) end "
                f"{buf_var}={buf_var}..table.concat(_o) "
                f"end "
            )
            lines.append(f"end ")

        lines.append(
            f"local {fn_var},{er_var}={ls_var}({buf_var}) "
            f"if not {fn_var} then error({er_var} or '',0) end "
            f"local {ok_var},{er_var}=pcall({fn_var}) "
            f"if not {ok_var} then error({er_var} or '',0) end "
        )

        return "".join(lines)

    def obfuscate(self):
        source = self.source
        rng = self.rng

        header = build_runtime_header(
            self.seeds, self.alphabet_seed,
            self.var_k, self.var_Q, self.var_G,
            self.var_B, self.var_f, self.var_V,
            self.wm_var,
        )

        dispatch_table, hashes = build_vm_dispatch(self.var_V, rng)

        anti_tamper = build_anti_tamper(
            self.seeds, rng, self.var_k, self.encode
        )

        n_chunks = rng.randint(MIN_CHUNKS, MAX_CHUNKS)
        chunks = split_source(source, n_chunks)
        chunk_loader = self.build_chunk_loader(chunks)

        sm_var = gen_name()
        sid1 = rng.randint(1000000,   5000000)
        sid2 = rng.randint(5000001,   9000000)
        sid3 = rng.randint(9000001,  13000000)
        sid4 = rng.randint(13000001, 16000000)

        junk_sids = [rng.randint(1000000, 16000000) for _ in range(10)]
        junk_parts = " ".join(
            f"elseif {sm_var}=={sid} then local _d{rng.randint(1000,9999)}={rng.randint(0,65535)}"
            for sid in junk_sids
        )

        err_enc, err_cid = self.encode("Script protection fault")
        s0e = rng.randint(100000, 2**31 - 1)
        s2e = rng.randint(100000, 2**31 - 1)
        s3e = rng.randint(100000, 2**31 - 1)
        k = self.var_k

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
            f"{chunk_loader}"
            f"{sm_var}={sid3} "
            f"elseif {sm_var}=={sid3} then break "
            f"elseif {sm_var}=={sid4} then "
            f'error({k}("{err_enc}",1,{s0e},{err_cid},{err_cid},{s2e},{s3e}),2) '
            f"end end "
        )

        footer = build_runtime_footer(self.var_Q, self.var_G)

        banner = (
            "--[[\n"
            "  Protected by Weak Obfuscator v2.0\n"
            "  https://github.com/Melodieshusband/Weak-Lua-Obfuscator\n"
            "]]\n"
        )

        return banner + header + body + footer
