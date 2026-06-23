# Weak — Lua/Luau Obfuscator

A source-level Lua/LuaU obfuscator written in Python, designed for Roblox scripts.

## Features

### String Encryption
All strings are encrypted using a dual-LCG stream cipher. Each string gets a unique call ID and is encoded into a shuffled alphabet of printable ASCII characters. Every seed is generated with `secrets.randbelow()` — no hardcoded constants, every run produces a different output.

### Obfuscated Cache Keys
The internal string cache uses a composite key `call_id * MK + type` where `MK` is a random 32-bit seed per run. Iterating the cache table does not reveal plaintext strings without knowing `MK`.

### Decoder Name Concealment
The decoder function name is never written as a string literal in the output. It is recovered at runtime by decrypting it through the decoder itself, so static searches for the decoder by name do not work.

### Chunked Source Loading
The source script is split into 3–7 random chunks. Each chunk is encrypted with the global key set. Chunks are decrypted and concatenated at runtime before `loadstring` — no single string contains the full source, defeating simple `loadstring` hooks.

### VM Mode (default when possible)
A full Lua compiler and bytecode interpreter written from scratch. When active:

- Source is parsed to AST, compiled to a custom bytecode format, embedded as a byte array
- Bytecode is executed by a register-based interpreter with fully randomized variable names
- **Opcode table is re-randomized on every run** — static deobfuscators targeting fixed opcode values do not work
- Upvalues modelled with shared cells; closures that capture the same variable share state correctly
- Supported: all arithmetic operators including `//`, generic/numeric for, varargs, method calls, closures, tables
- Falls back to chunk mode silently if compilation fails

### Identifier Obfuscation
All runtime variable names are random sequences of visually identical ASCII characters (`l`, `I`, `O`, `o`, `0`, `1`), 6–10 characters long, re-randomized per run via a `secrets`-seeded RNG. Names like `lI0OlI`, `OI1lO0` are indistinguishable at a glance.

### VM Dispatch Table
100+ anonymous functions covering arithmetic, comparison, string, and logic operations, inserted with random numeric keys per run.

### Control Flow Flattening
Main execution logic runs inside a `while` state machine with randomized state IDs and unreachable dead branches.

### Anti-Tamper (Roblox/LuaU)
Checks performed before any decryption begins:

- 25+ standard function type checks (`rawget`, `setmetatable`, `pcall`, `string.byte`, etc.)
- Mathematical invariant checks (`1/0 == math.huge`, `0/0 ~= 0/0`, etc.)
- Timing check: 100,000 iterations must complete in under 3 seconds
- Metatable trap test
- `tostring`/`tonumber` round-trip validation
- Environment scan for known Lua debuggers: `MobDebug`, `remdebug`, `LuaSocket`, `ldb`, `__debugger`, `BreakpointHook`
- Global variable checks: `__BREAKPOINT__`, `__DEBUG__`, `__ATTACHED__`

All checked names are encrypted — none appear in plaintext in the output.

## Requirements

- Python 3.8+
- No third-party dependencies

## Usage

```bash
python main.py input.lua
python main.py input.lua output.lua
```

Output defaults to `input_obf.lua` if no output path is given.

## File Structure

```
crypto.py        — LCG cipher, alphabet shuffle, encode/decode
codegen.py       — Runtime header, VM dispatch table, anti-tamper, name generation
obfuscator.py    — Main obfuscation pipeline, chunk splitting, chunk loader
string_fold.py   — String extraction and in-place encryption
vm.py            — Lua lexer, parser, compiler, bytecode serializer, interpreter generator
vm_opcodes.py    — Randomized opcode table generator
main.py          — CLI entry point
```

## Limitations

- Source-level obfuscator — does not modify Roblox bytecode directly
- LCG cipher is not cryptographically strong; the goal is reverse engineering difficulty, not cryptographic security
- `continue` (LuaU extension) is not supported in VM mode; obfuscator falls back to chunk mode automatically
- Each run produces a unique output

## License

MIT [LICENSE](LICENSE).
