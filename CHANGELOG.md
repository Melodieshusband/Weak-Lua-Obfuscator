# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.4]

### Security
- `MACKEY` is no longer embedded as a flat 32-byte Lua table literal next to the HMAC call it protects (`obfuscator.py`, `build_vm_data_expr`). It is now split into 8 words and reconstructed with the same `scatter_value`/`scatter_value_standalone` machinery already used for `KEY` (`codegen.py`, `build_runtime_header`): the first 7 words are interleaved with decoy variables and fake integrity sinks, the last word is routed through a Caesar-ciphered, `loadstring`-booted mini-chunk with the usual hook checks. The reconstructed key only ever exists inside a new header-local `mac_verify` primitive; call sites receive just the public tag and the ciphertext, never the key itself.
- On an HMAC mismatch, the VM payload check no longer drops into a `while true do print(...) end` loop at the check site. That shape is compact and trivially greppable for the exact line that does the real tamper check. `mac_verify` now responds by flipping a pseudo-random byte of the ciphertext buffer (position and value derived from the existing `drv_v` stream) and letting execution fall through into the normal decrypt/run path, so a tampered build fails later, elsewhere in the VM, instead of at an obviously-shaped trap immediately after the comparison.
- Encoded the real (reachable) trap strings that were previously inserted as plain Lua string literals, which made them `strings`/grep targets pointing straight at functioning checks: the 3 `"Melodie caught an illegal opcode modification :3"` prints in the VM opcode dispatcher (`vm.py`, `bytecode_to_lua`, `bytecode_to_lua_mltn_only`, `bytecode_to_lua_legacy`), and the constant-pool protection strings (`"...constant pool is protected and read-only"`, `"...encrypted constant container"`) on the read-only consts metatable, 3 occurrences across the same three codegen functions. All are now rebuilt at runtime from a per-build, randomly-shifted byte table (`vm.py`, `_hidden_str_lit`) instead of appearing as readable text in the generated output.

## [2.3]

### Added
- Multi-dialect support: Lua 5.1 through 5.5, LuaJIT, and FiveM/CfxLua, unified behind a single version-parameterized AST engine (`lua5x_ast.py`, `lua5x_unparse.py`) plus a dedicated LuaJIT engine (`luajit_ast.py`, `luajit_unparse.py`). Previously the obfuscator only targeted Luau.
- Full bytecode-level control-flow flattening (`bytecode_cff.py`, `flatten_bytecode_full`, `cff_mode="full"`, now the default): a genuine dispatcher with a state table, XOR-encrypted state transitions, and indirect `JUMP_REG` dispatch, replacing the previous block-shuffle/bogus-control-flow approach (now kept as the `legacy` mode).
- DEFLATE-based compression (`build_inflate_runtime` / MLTN+MLD bytecode format) for the embedded VM bytecode payload, reducing output file size.
- Real HMAC-SHA256 integrity check on the embedded VM bytecode payload (`crypto.py`, `codegen.py`, `obfuscator.py`). A tag is computed at build time over the ChaCha-encrypted bytecode blob with a dedicated MAC key (separate from the cipher key, encrypt-then-MAC), and verified at runtime before the payload is decrypted. A mismatch drops execution into an infinite `Melodie noticed the bytecode payload was tampered with` loop instead of silently running on corrupted/patched bytecode.
  - Pure-Lua SHA-256 and HMAC implementation ported across all bitwise-operator dialect families already used elsewhere in the project (native `&|~<<>>` for Lua 5.3/5.4/5.5/FiveM, `bit.*` for LuaJIT, `bit32.*` for Luau/Lua 5.2, arithmetic fallback for Lua 5.1).
- Real anti-tamper branch inside the full bytecode-level CFF dispatcher (`bytecode_cff.py`, `flatten_bytecode_full`). The dispatcher now routes through a genuine `anti_tamper_check` state before reaching user code: it checks `debug.getinfo(print).what == "C"` (same check already used by the source-level anti-tamper layer) and, on failure, redirects dispatcher state into a dedicated `melodie` state that loops on itself forever, printing the Melodie decoy message. Previously this message only existed as unreachable dead code in the legacy (non-full) CFF mode.

### Fixed
- Anti-tamper check above was initially fail-closed on missing `debug`/`debug.getinfo` (treated an unavailable debug library as tampering), which caused false positives on sandboxes/runtimes that strip `debug` entirely (e.g. this project's own Luau CLI target). Changed to fail-open: the check now only flags a real, verifiable mismatch and otherwise falls through to normal execution, matching the behavior of the existing source-level anti-tamper check.
- Several smaller bytecode/codegen bugs fixed during this cycle.
- Several bugs fixed during the dialect/CFF expansion.
<!-- TODO: list the specific bug fixes here (what broke, what triggered it, what the fix changed) -->

