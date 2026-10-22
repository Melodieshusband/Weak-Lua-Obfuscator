import random
import secrets
from crypto import make_seeds, encode_string, encrypt_bytes
from codegen import (
    reset_names, gen_name,
    build_runtime_header, build_vm_dispatch,
    build_anti_tamper, build_runtime_footer,
    deflate_tables_blob, build_luajit_polyfill,
)
from vm import try_compile_vm, bytecode_to_lua, bytecode_to_lua_legacy
from string_fold import fold_strings
from number_fold import fold_numbers

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
        encoded = encode_string(text, call_id, self.seeds)
        if encoded is None:
            call_id = self.next_call_id()
            encoded = encode_string(text, call_id, self.seeds)
        return encoded, call_id

    def k_call(self, text, ret_type=1):
        encoded, call_id = self.encode(text)
        s0 = self.rng.randint(100000, 2**31 - 1)
        s2 = self.rng.randint(100000, 2**31 - 1)
        s3 = self.rng.randint(100000, 2**31 - 1)
        return f'{self.var_k}("{encoded}",{ret_type},{s0},{call_id},{call_id},{s2},{s3})'

    def k_call_uncompressed(self, text, ret_type=1):
        call_id = self.next_call_id()
        encoded = encode_string(text, call_id, self.seeds, allow_compress=False)
        if encoded is None:
            call_id = self.next_call_id()
            encoded = encode_string(text, call_id, self.seeds, allow_compress=False)
        s0 = self.rng.randint(100000, 2**31 - 1)
        s2 = self.rng.randint(100000, 2**31 - 1)
        s3 = self.rng.randint(100000, 2**31 - 1)
        return f'{self.var_k}("{encoded}",{ret_type},{s0},{call_id},{call_id},{s2},{s3})'

    def build_chunk_loader(self, chunks, result_var):
        rng = self.rng

        buf_var  = gen_name()
        fn_var   = gen_name()
        ok_var   = gen_name()
        er_var   = gen_name()
        ls_var   = gen_name()
        pk_var   = gen_name()

        encoded_chunks = []
        for chunk in chunks:
            cid = self.next_call_id()
            enc = encode_string(chunk, cid, self.seeds)
            if enc is None:
                cid = self.next_call_id()
                enc = encode_string(chunk, cid, self.seeds)
            encoded_chunks.append((enc, cid))

        lines = []
        canary = rng.randint(1000000, 9999999)
        c_fn = gen_name()
        c_ok = gen_name()
        c_bad = gen_name()
        lines.append(f"local {ls_var}=loadstring or load ")
        lines.append(f"if type({ls_var})~='function' then error('',0) end ")
        lines.append(f"if debug and debug.info and(debug.info({ls_var},'s')~='[C]' or debug.info({ls_var},'l')~=-1) then error('',0) end ")
        lines.append(f"if debug and debug.getinfo and debug.getinfo({ls_var}).what~='C' then error('',0) end ")
        lines.append(f"if (islclosure and islclosure({ls_var})) or (is_synapse_function and is_synapse_function({ls_var})) then error('',0) end ")
        lines.append(f"local {c_ok},{c_fn}=pcall({ls_var},'return {canary}') ")
        lines.append(f"if not {c_ok} or type({c_fn})~='function' or {c_fn}()~={canary} then error('',0) end ")
        lines.append(f"local _,{c_bad}=pcall({ls_var},'return (') ")
        lines.append(f"if {c_bad}~=nil then error('',0) end ")
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
        kn_var   = gen_name()
        var_k = self.var_k
        lines.append(
            f"local {env_var}=setmetatable({{}},{{__index=(getfenv and getfenv(0)) or _ENV or {{}}}}) "
            f"do local {kn_var}={self.k_call(self.var_k, ret_type=1)} if type({kn_var})=='string' then {env_var}[{kn_var}]={var_k} end end "
            f"local {wrap_var}='return (function(...)' .. {buf_var} .. ' end)(...)' "
            f"local {fn_var},{er_var}={ls_var}({wrap_var}) "
            f"{buf_var}=nil {wrap_var}=nil "
            f"if not {fn_var} then error({er_var} or '',0) end "
            f"if setfenv then setfenv({fn_var},{env_var}) end "
            f"local {pk_var}={{pcall({fn_var})}} "
            f"local {ok_var}={pk_var}[1] "
            f"if not {ok_var} then error({pk_var}[2] or '',0) end "
            f"{result_var}={pk_var} "
        )

        return "".join(lines)

    def build_hidden_chunk(self, lua_source, env_names=None):
        ls_v = gen_name()
        env_v = gen_name()
        fn_v = gen_name()
        er_v = gen_name()
        lines = []
        lines.append(f"local {ls_v}=loadstring or load ")
        lines.append(f"if type({ls_v})~='function' then error('',0) end ")
        lines.append(f"if debug and debug.info and(debug.info({ls_v},'s')~='[C]' or debug.info({ls_v},'l')~=-1) then error('',0) end ")
        lines.append(f"if debug and debug.getinfo and debug.getinfo({ls_v}).what~='C' then error('',0) end ")
        lines.append(f"if (islclosure and islclosure({ls_v})) or (is_synapse_function and is_synapse_function({ls_v})) then error('',0) end ")
        lines.append(
            f"local {env_v}=setmetatable({{}},{{__index=(getfenv and getfenv(0)) or _ENV or {{}}}}) "
        )
        for real_name in (env_names or []):
            kn_v = gen_name()
            lines.append(
                f"do local {kn_v}={self.k_call(real_name, ret_type=1)} "
                f"{env_v}[{kn_v}]={real_name} end "
            )
        lines.append(f"local {fn_v},{er_v}={ls_v}({self.k_call(lua_source, ret_type=1)}) ")
        lines.append(f"if not {fn_v} then error({er_v} or '',0) end ")
        lines.append(f"if setfenv then setfenv({fn_v},{env_v}) end ")
        return "".join(lines), fn_v

    def build_vm_data_expr(self, bytecode, prims):
        cid = self.next_call_id()
        enc = encrypt_bytes(bytecode, cid, self.seeds)
        from crypto import build_alphabet, base91_encode
        alphabet = build_alphabet(self.seeds["KEY"], self.seeds["NONCE_BASE"], self.seeds.get("CC"), self.seeds.get("ROT"))
        b91 = base91_encode(enc, alphabet)
        arr_v = gen_name()
        out_v = gen_name()
        i_v = gen_name()
        nw_v = gen_name()
        ks_v = prims["ks"]
        xorb_v = prims["xorb"]
        blk_v = prims["blk"]
        nb_v = prims["nb"]
        g3_v = prims["g3"]
        expr = (
            f"(function() local {arr_v}={g3_v}(\"{b91}\") "
            f"local {nw_v}={blk_v}({cid}%4294967296,{nb_v},3266489909,2654435769) "
            f"local {out_v}={ks_v}({nw_v}[1],{nw_v}[2],#{arr_v}) "
            f"for {i_v}=1,#{arr_v} do {arr_v}[{i_v}]={xorb_v}({arr_v}[{i_v}],{out_v}[{i_v}]) end "
            f"return {arr_v} end)()"
        )
        return expr

    def obfuscate(self, force_vm=False, force_fold=False, anti_tamper_level="full", hide_vm_source=False, at_version="v2", at_target="luau"):
        source = self.source
        rng = self.rng

        if force_fold:
            use_vm = False
        else:
            bytecode_result = try_compile_vm(source, rng=rng)
            if bytecode_result is not None:
                bytecode, opmap, bc_format = bytecode_result
                use_vm = True
            else:
                if force_vm:
                    raise RuntimeError("--vm Error")
                use_vm = False

        header, prims = build_runtime_header(
            self.seeds,
            self.var_k, self.var_Q, self.var_G,
            self.var_B, self.var_f, self.var_V,
            self.wm_var,
        )

        if at_target == "luajit":
            header = build_luajit_polyfill() + header

        it = prims["inflate_tables"]
        tables_expr = self.k_call_uncompressed(deflate_tables_blob())
        tables_parsed_v = gen_name()
        header += (
            f"local {tables_parsed_v}={it['parsetables']}({tables_expr}) "
            f"{it['lenbase']}={tables_parsed_v}[1] "
            f"{it['lenextra']}={tables_parsed_v}[2] "
            f"{it['distbase']}={tables_parsed_v}[3] "
            f"{it['distextra']}={tables_parsed_v}[4] "
            f"{it['clenorder']}={tables_parsed_v}[5] "
        )

        dispatch_expr, hashes = build_vm_dispatch(rng)
        expected_count, expected_sum, expected_xor = hashes.get("__meta__", (0, 0, 0))
        dispatch_loader, dispatch_fn_v = self.build_hidden_chunk(f"return {dispatch_expr}")
        dispatch_table = f"{dispatch_loader}local {self.var_V}={dispatch_fn_v}() "

        detect_var = gen_name()

        if anti_tamper_level != "none" and expected_count > 0:
            chk_cnt_v = gen_name()
            chk_sum_v = gen_name()
            chk_xor_v = gen_name()
            chk_k_v   = gen_name()
            chk_fn_v  = gen_name()
            snap_v    = gen_name()
            dispatch_verify = (
                f"local {snap_v}={self.var_V} "
                f"do local {chk_cnt_v}=0 local {chk_sum_v}=0 local {chk_xor_v}=0 "
                f"for {chk_k_v},{chk_fn_v} in pairs({self.var_V}) do "
                f"if type({chk_k_v})~='number' or type({chk_fn_v})~='function' then {detect_var}=true error('',0) end "
                f"{chk_cnt_v}={chk_cnt_v}+1 "
                f"{chk_sum_v}=({chk_sum_v}+{chk_k_v})%4294967296 "
                f"{chk_xor_v}=bit32.bxor({chk_xor_v},{chk_k_v}) "
                f"end "
                f"if {chk_cnt_v}~={expected_count} or {chk_sum_v}~={expected_sum} or {chk_xor_v}~={expected_xor} or {self.var_V}~={snap_v} then "
                f"{detect_var}=true error('',0) "
                f"end end "
            )
            dispatch_table += dispatch_verify

        anti_tamper = build_anti_tamper(
            self.seeds, rng, self.var_k, self.encode, detect_var=detect_var,
            level=anti_tamper_level, version=at_version, target=at_target,
        )

        sm_var = gen_name()
        sid1 = rng.randint(1000000,   5000000)
        sid2 = rng.randint(5000001,   9000000)
        sid3 = rng.randint(9000001,  13000000)
        sid4 = rng.randint(13000001, 16000000)

        junk_sids = [rng.randint(1000000, 16000000) for _ in range(12)]
        junk_blocks = []
        for sid in junk_sids:
            v_a = gen_name()
            v_b = gen_name()
            v_t = gen_name()
            n1 = rng.randint(100, 9999)
            n2 = rng.randint(5, 30)
            kind = rng.randint(1, 7)
            if kind == 1:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if ({v_a}*{v_a})%4==2 then "
                    f"local {v_t}={{}} for {v_b}=1,{n2} do {v_t}[{v_b}]={v_b}*{n1} end "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            elif kind == 2:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if ({v_a}*{v_a})%4==3 then "
                    f"local {v_t}=string.rep(string.char({rng.randint(65, 90)}),{n2}) "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            elif kind == 3:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if (bit32.band({v_a},1)*2+bit32.band(bit32.rshift({v_a},1),1)>3) then "
                    f"local {v_t}={{}} {v_t}[{n1}]={n2} "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            elif kind == 4:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if ({v_a}*{v_a})%4==2 then "
                    f"local {v_t}='MelotenIsMelodiesOnlyHusband' "
                    f"if {v_a}=={v_t} then "
                    f"print('Welcome back, Meloten. Decryption key: 0xDEADBEEF') "
                    f"return 'MelodieSuperAdmin' end "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            elif kind == 5:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if ({v_a}*{v_a})%4==3 then "
                    f"local {v_t}='MelodieCore_OverrideBypass' "
                    f"if {v_a}=={v_t} then "
                    f"print('Melodie granted full system privileges') "
                    f"return 'MelodieRootAccess' end "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            elif kind == 6:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if math.abs({v_a})<0 then "
                    f"local {v_t}='MelodieSecurity_MasterKey_991823' "
                    f"print('Melodie authorized bypass for Meloten') "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
            else:
                junk_blocks.append(
                    f"elseif {sm_var}=={sid} then "
                    f"local {v_a}={n1} "
                    f"if math.abs({v_a})<0 then "
                    f"{sm_var}={sid4} else {sm_var}={rng.randint(1000000, 16000000)} end"
                )
        junk_parts = " ".join(junk_blocks)

        opq_v = gen_name()
        opq_n = rng.randint(100, 9999)

        err_enc, err_cid = self.encode("Script protection fault")
        s0e = rng.randint(100000, 2**31 - 1)
        s2e = rng.randint(100000, 2**31 - 1)
        s3e = rng.randint(100000, 2**31 - 1)
        k = self.var_k

        res_var = gen_name()

        if use_vm:
            data_expr = self.build_vm_data_expr(bytecode, prims)
            encode_fn = bytecode_to_lua if bc_format == "mltn" else bytecode_to_lua_legacy
            payload = encode_fn(bytecode, rng, gen_name, opmap, data_expr=data_expr, detect_var=detect_var, key_expr=prims.get("key"))
            vmres_v = gen_name()
            if hide_vm_source:
                chunk_src = f"return (function(...) {payload} end)(...)"
                env_names = [detect_var, prims["ks"], prims["xorb"], prims["blk"], prims["nb"], prims["g3"], prims["key"]]
                vm_loader, vm_fn_v = self.build_hidden_chunk(chunk_src, env_names=env_names)
                payload_stage = (
                    f"{vm_loader}"
                    f"local {vmres_v}={{true,{vm_fn_v}()}} "
                    f"{res_var}={vmres_v} "
                )
            else:
                payload_stage = (
                    f"local {vmres_v}={{true,(function(...) {payload} end)()}} "
                    f"{res_var}={vmres_v} "
                )
        else:
            flattened = ast_flatten_source(source, rng, gen_name, detect_var=detect_var, target=at_target)
            if flattened is None:
                flattened = source
            numbered = fold_numbers(flattened, rng)
            folded = fold_strings(numbered, self.encode, self.var_k, rng)
            n_chunks = rng.randint(MIN_CHUNKS, MAX_CHUNKS)
            chunks = split_source(folded, n_chunks)
            payload_stage = self.build_chunk_loader(chunks, res_var)

        body = (
            f"local {res_var}={{true}} "
            f"local {detect_var}=false "
            f"{anti_tamper}"
            f"{dispatch_table}"
            f"local {sm_var}={sid1} "
            f"while {sm_var} do "
            f"if {sm_var}<{sid2} then "
            f"if {sm_var}=={sid1} then local {opq_v}={opq_n} if ({opq_v}*{opq_v})%4~=2 then {sm_var}={sid2} else {sm_var}={sid4} end "
            f"{junk_parts} "
            f"end "
            f"elseif {sm_var}=={sid2} then "
            f"{payload_stage}"
            f"{sm_var}={sid3} "
            f"elseif {sm_var}=={sid3} then break "
            f"elseif {sm_var}=={sid4} then "
            f'error({k}("{err_enc}",1,{s0e},{err_cid},{err_cid},{s2e},{s3e}),2) '
            f"end end "
            f"return table.unpack({res_var},2) "
        )

        footer = build_runtime_footer(self.var_Q, self.var_G)

        at_label = {
            "full": f"Full ({at_version.upper()}-{at_target.capitalize()})",
            "minimal": f"Minimal ({at_version.upper()}-{at_target.capitalize()})",
            "none": "Disabled",
        }.get(anti_tamper_level, "Full")
        banner = (
            "--[[\n"
            "  Protected by Weak Obfuscator v2.3\n"
            f"  Anti-Tamper: {at_label}\n"
            "  https://github.com/Melodieshusband/Weak-Lua-Obfuscator\n"
            "]]\n"
        )

        if use_vm:
            mode = "VM (hidden source)" if hide_vm_source else "VM (no loadstring)"
            bc_label = "MLTN+MLD compressed" if bc_format == "mltn" else "plain (compression skipped, would have grown output)"
            mode = f"{mode}, bytecode: {bc_label}"
        else:
            mode = "chunks+string-fold"
        mode = f"{mode}, Anti-Tamper: {at_label}"
        return banner + header + body + footer, mode
