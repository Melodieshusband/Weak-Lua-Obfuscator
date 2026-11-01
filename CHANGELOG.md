# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

