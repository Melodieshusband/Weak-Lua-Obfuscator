# Weak Lua Obfuscator

A Lua/Luau obfuscator written in Python, designed for Roblox scripts.

Named "Weak" honestly — it is not unbreakable, but it implements several real protection layers that make casual reverse engineering significantly harder.

## Features

### String Encryption
All strings in the output (including the source code itself) are encrypted using a dual-LCG stream cipher. Each string gets a unique call ID and is encoded into a shuffled alphabet of printable characters.

Every seed (P, Q, R, S, T, U, BK, A1, A2) is generated randomly per-run using `secrets.randbelow()`. No hardcoded constants.

### Chunked Source Loading
The source script is split into N random chunks (3–7). Each chunk is encrypted with its own independent seed set and alphabet seed. The chunks are decrypted and concatenated at runtime before being loaded — so there is no single string that contains the full source.

This prevents the simplest hook attack:
```lua
local old = loadstring
loadstring = function(src) print(src) return old(src) end
```
By the time `loadstring` is called, the source has already been assembled from individually encrypted pieces.

### Identifier Renaming
All runtime variable names are randomized to 6+ character sequences on every run. There are no stable names to search for.

### VM Dispatch Table
A table of 100+ anonymous functions covering arithmetic, comparison, string, and logic operations is generated and inserted as junk. Each operation is assigned multiple random numeric keys.

### Control Flow Flattening
The main execution logic runs inside a `while` state machine with randomized state IDs and dead branches that are never reached.

### Anti-Tamper (Roblox/Luau)
Checks performed before any decryption:

- 25+ standard function type checks (`rawget`, `setmetatable`, `pcall`, `string.byte`, etc.)
- Mathematical invariant checks (`1/0 == math.huge`, `0/0 ~= 0/0`, etc.)
- Timing check: 100,000 iterations must complete in under 3 seconds
- Metatable trap test
- `tostring`/`tonumber` round-trip test
- Environment scan for known Roblox executors: `syn`, `fluxus`, `krnl`, `oxygen`, `electron`, `sentinel`, `hydroxide`, `scriptware`, `evon`, `getgenv`, `hookfunction`, `newcclosure`, `checkcaller`, `getscriptbytecode`, `decompile`, and more
- Environment scan for known Lua debuggers: `MobDebug`, `remdebug`, `LuaSocket`, `ldb`, `__debugger`, `BreakpointHook`
- Global variable checks: `__BREAKPOINT__`, `__DEBUG__`, `__ATTACHED__`

All checked names are encrypted — they do not appear in plaintext in the output.

## Requirements

- Python 3.8+
- No third-party dependencies

## Usage

```bash
python main.py input.lua
python main.py input.lua output.lua
```

Output file defaults to `input_obf.lua` if no output path is given.

## File Structure

```
crypto.py      — LCG cipher, alphabet, encode/decode
codegen.py     — Lua runtime header, VM dispatch, anti-tamper generation
obfuscator.py  — Main obfuscation logic, chunk splitting
main.py        — CLI entry point
```

## Limitations

- `loadstring` must be enabled in Roblox (`ServerScriptService.LoadStringEnabled = true` for server scripts, or use a LocalScript)
- The obfuscation is deterministic given the same Python `secrets` output — each run produces a unique result
- This is not a compiler or bytecode obfuscator; it operates at the source level

## License

MIT
