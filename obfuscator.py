import random
import secrets
from crypto import make_seeds, encode_string, encrypt_bytes
from codegen import (
    reset_names, gen_name,
    build_runtime_header, build_vm_dispatch,
    build_anti_tamper, build_runtime_footer,
)
from vm import try_compile_vm, bytecode_to_lua
from string_fold import fold_strings
from number_fold import fold_numbers
from cff import flatten_top_level, flatten_recursive, can_flatten
from ast_cff import flatten_source as ast_flatten_source

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

        self.wm_var = f"_WO_{secrets.randbelow(10**19 - 10**18) + 10**18}"

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

        buf_var  = gen_name()
        fn_var   = gen_name()
        ok_var   = gen_name()
        er_var   = gen_name()
        ls_var   = gen_name()

        encoded_chunks = []
        for chunk in chunks:
            cid = self.next_call_id()
            enc = encode_string(chunk, cid, self.seeds, self.alphabet_seed)
            if enc is None:
                cid = self.next_call_id()
                enc = encode_string(chunk, cid, self.seeds, self.alphabet_seed)
            encoded_chunks.append((enc, cid))

        lines = []
        lines.append(f"local {ls_var}=loadstring or load ")
        lines.append(f"if type({ls_var})~='function' then error('',0) end ")
        lines.append(f"local {buf_var}='' ")

        for enc, cid in encoded_chunks:
            dv  = gen_name()
            s0  = rng.randint(100000, 2**31 - 1)
            s2  = rng.randint(100000, 2**31 - 1)
            s3  = rng.randint(100000, 2**31 - 1)
            lines.append(
                f"do "
                f"local {dv}={self.var_k}(\"{enc}\",1,{s0},{cid},{cid},{s2},{s3}) "
                f"if type({dv})=='string' then {buf_var}={buf_var}..{dv} end "
                f"end "
            )

        env_var  = gen_name()
        wrap_var = gen_name()
        var_k = self.var_k
        lines.append(
            f"local {env_var}=setmetatable({{}},{{__index=(getfenv and getfenv(0)) or _ENV or {{}}}}) "
            f"do local _kn={self.k_call(self.var_k, ret_type=1)} if type(_kn)=='string' then {env_var}[_kn]={var_k} end end "
            f"local {wrap_var}='(function(...)' .. {buf_var} .. ' end)(...)' "
            f"local {fn_var},{er_var}={ls_var}({wrap_var}) "
            f"if not {fn_var} then error({er_var} or '',0) end "
            f"if setfenv then setfenv({fn_var},{env_var}) end "
            f"local {ok_var},{er_var}=pcall({fn_var}) "
            f"if not {ok_var} then error({er_var} or '',0) end "
        )

        return "".join(lines)

    def build_vm_data_expr(self, bytecode, prims):
        cid = self.next_call_id()
        enc = encrypt_bytes(bytecode, cid, self.seeds)
        nonce_lo, nonce_hi = self.seeds["NONCE_BASE"], cid
        packed = ",".join(str(b) for b in enc)
        arr_v = gen_name()
        out_v = gen_name()
        i_v = gen_name()
        nlo, nhi = cid & 0xFFFFFFFF, (cid ^ self.seeds["NONCE_BASE"]) & 0xFFFFFFFF
        ks_v = prims["ks"]
        xorb_v = prims["xorb"]
        expr = (
            f"(function() local {arr_v}={{{packed}}} "
            f"local {out_v}={ks_v}({nlo},{nhi},#{arr_v}) "
            f"for {i_v}=1,#{arr_v} do {arr_v}[{i_v}]={xorb_v}({arr_v}[{i_v}],{out_v}[{i_v}]) end "
            f"return {arr_v} end)()"
        )
        return expr

    def obfuscate(self, force_vm=False, force_fold=False):
        source = self.source
        rng = self.rng

        if force_fold or not force_vm:
            use_vm = False
        else:
            bytecode_result = try_compile_vm(source, rng=rng)
            if bytecode_result is not None:
                bytecode, opmap = bytecode_result
                use_vm = True
            else:
                if force_vm:
                    raise RuntimeError("--vm Error")
                use_vm = False

        header, prims = build_runtime_header(
            self.seeds, self.alphabet_seed,
            self.var_k, self.var_Q, self.var_G,
            self.var_B, self.var_f, self.var_V,
            self.wm_var,
        )

        dispatch_table, hashes = build_vm_dispatch(self.var_V, rng)

        anti_tamper = build_anti_tamper(
            self.seeds, rng, self.var_k, self.encode
        )

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

        if use_vm:
            data_expr = self.build_vm_data_expr(bytecode, prims)
            payload = bytecode_to_lua(bytecode, rng, gen_name, opmap, data_expr=data_expr)
            vmres_v = gen_name()
            payload_stage = f"local {vmres_v}=(function(...) {payload} end)() "
        else:
            flattened = ast_flatten_source(source, rng, gen_name)
            if flattened is None:
                flattened = source
            numbered = fold_numbers(flattened, rng)
            folded = fold_strings(numbered, self.encode, self.var_k, rng)
            n_chunks = rng.randint(MIN_CHUNKS, MAX_CHUNKS)
            chunks = split_source(folded, n_chunks)
            payload_stage = self.build_chunk_loader(chunks)

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
            f"{payload_stage}"
            f"{sm_var}={sid3} "
            f"elseif {sm_var}=={sid3} then break "
            f"elseif {sm_var}=={sid4} then "
            f'error({k}("{err_enc}",1,{s0e},{err_cid},{err_cid},{s2e},{s3e}),2) '
            f"end end "
        )

        footer = build_runtime_footer(self.var_Q, self.var_G)

        banner = (
            "--[[\n"
            "  Protected by Weak Obfuscator v2.1\n"
            "  https://github.com/Melodieshusband/Weak-Lua-Obfuscator\n"
            "]]\n"
        )

        mode = "VM (no loadstring)" if use_vm else "chunks+string-fold"
        return banner + header + body + footer, mode
