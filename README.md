# Weak — Lua/Luau Obfuscator

A source-level Lua/Luau obfuscator written in Python, designed for Roblox scripts.

> ## ⚠️ Getting a false-positive Anti-Tamper kill on a specific executor?
> **Use the `--minimal-anti-tamper` flag.** It drops only the small set of checks known to
> occasionally misfire on executors that hook, sandbox, or spoof `pcall`/`error`/`debug`
> internals, or that don't emulate real Roblox physics timing closely. Everything else
> (Lune/Lute/wally/rojo/JS-environment detection, debugger scans, standard type checks,
> Roblox instance/Enum checks) still runs. See **Anti-Tamper Levels** below.
>
> ```bash
> python main.py input.lua output.lua --minimal-anti-tamper
> ```

## History

This project didn't start out ambitious. The first publicly released version used an LCG (linear congruential generator) cipher with hardcoded seed constants shared across every build, rather than a fresh key generated per run, and its "VM" was really just a dispatch table of hashed inline functions for basic operations — closer to a dispatch obfuscation trick than a real bytecode compiler. It offered close to no real protection, and the name was picked because it was, plainly and honestly, weak.

Then something clicked, and what began as a throwaway project turned into an ongoing effort to make it actually good: a from-scratch VM with a custom bytecode format, a reduced-round ChaCha8 cipher with a fresh key per build, multi-layer anti-tamper checks refined against real executor behavior, control-flow flattening at both the AST and bytecode level. The name never changed, even as the project outgrew it many times over.

## Credits

Built by Melodieshusband, with significant help from Claude (Anthropic).

## Features

### VM Mode (working)
A full Lua compiler and bytecode interpreter, written from scratch:

- Source is lexed, parsed to an AST, and compiled to a custom bytecode format, embedded as a byte array
- Bytecode runs on a register-based interpreter generated fresh for each build, with fully randomized variable names
- Opcode table is re-randomized every run (`vm_opcodes.py`), so the same operation maps to different opcode numbers between builds
- Upvalues are modelled with shared cells; closures capturing the same variable correctly share state
- Supported: all arithmetic operators including `//`, bitwise ops (`bit32`-backed), generic/numeric `for`, varargs, method calls (`:`), closures, tables (including multi-value/`...` list construction)
- On any compile failure the pipeline falls back to chunk+fold mode automatically, so `--vm` never produces broken output — it either compiles cleanly or backs off

Enable with `--vm`.

### String Encryption
All strings are encrypted with a reduced-round ChaCha8 stream cipher (ARX construction: add-rotate-xor, same family as ChaCha20 with the round count halved). Each build generates a fresh 256-bit key via `secrets`. Every string gets a unique 64-bit nonce derived from its call ID, so no two strings share a keystream. The keystream is XORed against the plaintext bytes only — it never depends on the data being encrypted. Output bytes are packed into a per-run shuffled alphabet of printable ASCII characters.

### Obfuscated Cache Keys
The internal string cache uses a composite key `call_id * MK + type` where `MK` is a random 32-bit seed per run. Iterating the cache table does not reveal plaintext strings without knowing `MK`.

### Scattered Key Derivation
Header key material is no longer stored as single obvious constants. Each value is split into 4–6 shares combined through addition, XOR-masking, or rolling deltas, with decoy shares mixed in, and a subset of shares recovered through a small per-build pseudo-random derivation function (`drv_v`) instead of appearing as a literal.

### Decoder Name Concealment
The decoder function name is never written as a string literal in the output. It is recovered at runtime by decrypting it through the decoder itself, so static searches for the decoder by name do not work.

### Chunked Source Loading
The obfuscated payload (either flattened+folded source, or serialized VM bytecode) is split into 3–7 random chunks. Each chunk is encrypted with the global key set. Chunks are decrypted and concatenated at runtime before `loadstring` — no single string contains the full payload, defeating simple `loadstring` hooks.

### Identifier Obfuscation
All runtime variable names are random sequences of visually identical ASCII characters (`l`, `I`, `O`, `o`, `0`, `1`), 6–10 characters long, re-randomized per run via a `secrets`-seeded RNG. Names like `lI0OlI`, `OI1lO0` are indistinguishable at a glance.

### VM Dispatch Table
100+ anonymous functions covering arithmetic, comparison, string, and logic operations, inserted with random numeric keys per run.

### Control Flow Flattening
Two independent flattening passes, depending on mode:

- **Fold mode** (`ast_cff.py`): a proper AST-based pass over the parsed source (via `luau_ast.py`/`luau_unparse.py`), rewriting function/chunk bodies into a `while`-based dispatcher with randomized state IDs, shuffled block order, and junk branches mixed in. Falls back to the unflattened source only if the AST pass itself throws (e.g. a parse edge case), so `--fold` output is always valid Lua either way.
- **VM mode** (`bytecode_cff.py`): flattens the compiled bytecode itself at the instruction level — basic blocks are split, reordered behind a dispatcher, and junk instructions are interleaved — independent of and in addition to the VM's own opcode randomization.

The older statement-text-based flattener (`cff.py`) is legacy and is no longer used by either mode.

### Number Folding
Numeric literals are rewritten as arithmetic expressions (`a+b`, `b-a`, `a*b`) chosen randomly per literal, so constants don't appear directly in the output.

### Anti-Tamper (Roblox/Luau)
Checks performed before any decryption begins:

- Error-message interception probe: repeatedly triggers `error()` through `pcall` and confirms the message survives unmodified, catching hooked `error`/`pcall`
- `debug.traceback()` line-number consistency check, catching code that has been relocated or reformatted by deobfuscation tooling
- Statistical/behavioral consistency check across repeated `pcall` invocations
- `tostring`/metatable trap: confirms `__tostring` metamethods are honored normally and not intercepted
- Roblox runtime behavior validation: exercises real engine state (parts, physics, `Enum`, camera, player object) to confirm the script is running inside an actual Roblox client rather than an emulated or partial environment
- 25+ standard function type checks (`rawget`, `setmetatable`, `pcall`, `string.byte`, etc.)
- Mathematical invariant checks (`1/0 == math.huge`, `0/0 ~= 0/0`, etc.)
- Timing check: 100,000 iterations must complete in under 3 seconds
- Environment scan for known Lua debuggers: `MobDebug`, `remdebug`, `LuaSocket`, `ldb`, `__debugger`, `BreakpointHook`
- Global variable checks: `__BREAKPOINT__`, `__DEBUG__`, `__ATTACHED__`

All checked names are encrypted — none appear in plaintext in the output.

Two additional checks (a sandbox/JS-environment global scan and a `getfenv`-based environment probe) exist in the codebase but are disabled by default after producing false positives during testing — see **Executor Compatibility** below.

## Executor Compatibility

All anti-tamper checks in this build were tested and validated on **Delta**. On Delta, this build produces no false-positive kills with the current default check set.

Other executors have not been tested and may behave differently — some executors intentionally spoof or sandbox APIs like `getrawmetatable`, `getfenv`, or `_G` contents for their own security reasons, and the anti-tamper layer may interpret that as tampering. If you see a false-positive kill on an executor other than Delta:

1. Try `--minimal-anti-tamper` first (see **Anti-Tamper Levels** below) — this alone resolves most false positives without giving up all protection.
2. If it still false-positives, reproduce it with a minimal script (a single `print("hello")`) to confirm the anti-tamper layer itself is the cause, not your actual code.
3. Bisect `build_anti_tamper` in `codegen.py` by commenting out checks from the final assembly (the block at the bottom of the function) in half, rebuilding, and retesting, narrowing down to the offending check.
4. Either disable the offending check or adjust its logic for that executor's specific behavior.

This project is open source — if you adapt the anti-tamper layer for other executors, contributions or reports back are welcome.

## Anti-Tamper Levels

Three levels are available, controlled by a CLI flag. **Full is the default** — only switch to a lower level if you're actually seeing false-positive kills.

- **`--full-anti-tamper`** (default): every check described above runs. Strongest protection, recommended unless you have a specific compatibility problem.
- **`--minimal-anti-tamper`**: drops only the checks that are known to occasionally false-positive on executors that hook, sandbox, or spoof `pcall`/`error`/`debug` internals, or that don't emulate real Roblox physics timing closely. Specifically this removes:
  - The `pcall`/`error` message-integrity probe
  - The `debug.traceback()` line-consistency check
  - The statistical/behavioral `pcall` consistency check
  - The Roblox physics/timing behavior check (`BodyVelocity`/`BodyPosition` timing, `debug.getinfo` internals, `settings()`)

  Everything else stays on: standard function/type checks, math invariants, the `tostring`/metatable trap, Lune/Lute/wally/rojo/JS-environment detection, the debugger name scan, and the `__BREAKPOINT__`/`__DEBUG__`/`__ATTACHED__` global checks. This is the mode to reach for when one specific executor kills your script and you've confirmed it's the anti-tamper layer causing it.
- **`--no-anti-tamper`**: disables anti-tamper entirely. **Not recommended** — this makes the output significantly easier to deobfuscate, since there's nothing checking whether the runtime environment has been tampered with. Only use this if you have a reason unrelated to executor compatibility.

## Requirements

- Python 3.8+
- No third-party dependencies

## Usage

```bash
python main.py input.lua
python main.py input.lua output.lua
python main.py input.lua output.lua --fold
python main.py input.lua output.lua --vm
python main.py input.lua output.lua --minimal-anti-tamper
python main.py input.lua output.lua --vm --minimal-anti-tamper
python main.py input.lua output.lua --no-anti-tamper
```

Output defaults to `input_obf.lua` if no output path is given.

- No flag / `--fold`: control-flow flattening + number folding + string encryption + chunked loading
- `--vm`: compiles the script to custom bytecode and runs it on the generated interpreter, still wrapped in string encryption + chunked loading. Falls back to `--fold`-style output if the source fails to compile to bytecode, unless `--vm` was forced explicitly, in which case it errors out instead of silently downgrading
- `--vm` and `--fold` are mutually exclusive
- `--full-anti-tamper` / `--minimal-anti-tamper` / `--no-anti-tamper`: control the anti-tamper level (default: full). See **Anti-Tamper Levels** above. Only one of these may be given at a time, and all of them are independent of `--vm`/`--fold`.

## File Structure

```
crypto.py        — ChaCha8 stream cipher, alphabet shuffle, encode/decode
codegen.py       — Runtime header, VM dispatch table, anti-tamper, name generation
luau_ast.py      — Luau lexer/parser producing an AST
luau_unparse.py  — AST → Luau source printer
ast_cff.py       — AST-based control flow flattening (--fold mode)
bytecode_cff.py  — Bytecode-level control flow flattening (--vm mode)
number_fold.py   — Numeric literal → arithmetic expression rewriting
obfuscator.py    — Main obfuscation pipeline, chunk splitting, chunk loader
string_fold.py   — String extraction and in-place encryption
vm.py            — Lua lexer, parser, compiler, bytecode serializer, interpreter generator
vm_opcodes.py    — Randomized opcode table generator
main.py          — CLI entry point
cff.py           — legacy statement-text flattener, no longer used by either mode
```

## Limitations

- Source-level obfuscator — does not modify Roblox bytecode directly
- Strings are treated as raw bytes 0–255; non-ASCII text (Cyrillic, etc.) is not round-tripped correctly
- ChaCha8 gives strong per-string confidentiality, but the goal remains reverse-engineering difficulty for a source-level tool, not a general-purpose secure transport
- Each run produces a unique output

## License

MIT [LICENSE](LICENSE).
