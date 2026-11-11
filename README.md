<div align="center">

# 🌑 Weak

### Multi-Dialect Lua & Luau Obfuscator

A source-level obfuscator written in pure Python — custom bytecode VM, ChaCha20 string encryption, control-flow flattening, and native support across all major Lua runtimes.

![Version](https://img.shields.io/badge/version-2.4-informational)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Targets](https://img.shields.io/badge/targets-Lua%205.1--5.5%20%7C%20LuaJIT%20%7C%20Luau%20%7C%20FiveM%20%7C%20GLua-success)

[Quick Start](#-quick-start) •
[Supported Dialects](#-supported-lua-dialects) •
[Garry's Mod](#garrys-mod-glua-verified-in-game) •
[Features](#-features) •
[Modes](#-modes) •
[Anti-Tamper](#-anti-tamper) •
[Compatibility](#-executor-compatibility) •
[FiveM / RedM](#-fivem--redm-support-unverified) •
[Structure](#-project-structure)

</div>

---

> [!WARNING]
> **Getting a false-positive anti-tamper kill on a specific executor?**
> Rebuild with `--minimal-anti-tamper`. It drops only the small set of checks that are known to occasionally misfire on executors that hook, sandbox, or spoof `pcall` / `error` / `debug` internals, or that don't emulate Roblox physics timing closely. Everything else keeps running.
>
> ```bash
> python main.py input.lua output.lua --minimal-anti-tamper
> ```
>
> See [Anti-Tamper Levels](#anti-tamper-levels) for details.

## 🚀 Quick Start

**Requirements:** Python 3.8+ — no third-party dependencies.

```bash
git clone https://github.com/Melodieshusband/Weak-Lua-Obfuscator.git
cd Weak-Lua-Obfuscator

python main.py input.lua
```

The output is written to `input_obf.lua` unless you pass an explicit output path.

### Usage

```bash
python main.py <input.lua> [output.lua] [--vm | --fold] [CFF flag] [anti-tamper flag]
```

| Example | What it does |
| --- | --- |
| `python main.py input.lua` | Default (VM) mode, full anti-tamper |
| `python main.py input.lua output.lua --fold` | Explicit fold mode |
| `python main.py input.lua output.lua --vm` | Explicit VM mode |
| `python main.py input.lua output.lua --minimal-anti-tamper` | Relaxed anti-tamper for picky executors |
| `python main.py input.lua output.lua --vm --minimal-anti-tamper` | VM mode + relaxed anti-tamper |
| `python main.py input.lua output.lua --no-anti-tamper` | No anti-tamper (not recommended) |
| `python main.py input.lua output.lua --cff-full` | Full state-machine bytecode CFF **(default)** |
| `python main.py input.lua output.lua --cff-legacy` | Legacy block reorder + junk padding |
| `python main.py input.lua output.lua --no-cff` | Disable bytecode-level CFF |

### Flags

| Flag | Description |
| --- | --- |
| `--vm` | Compile the script to custom bytecode and run it on a per-build interpreter **(default)** |
| `--fold` | Control-flow flattening + number folding + string encryption, no VM |
| `--hide-vm-source` | Encrypt the VM dispatch loop (requires loadstring/load) |
| `--cff-full` | Full state-machine CFF with a dispatch table and indirect jump **(default, VM mode only)** |
| `--cff-legacy` | Legacy bytecode CFF: basic blocks are shuffled and padded with junk, direct jumps are kept |
| `--no-cff` | Disable bytecode-level CFF entirely (VM mode only) |
| `--full-anti-tamper` | All checks enabled **(default)** |
| `--minimal-anti-tamper` | Drops checks known to false-positive on some executors |
| `--no-anti-tamper` | Disables anti-tamper entirely |
| `--luau` | Target pure Luau **(default)** |
| `--roblox` | Target Roblox Luau environment |
| `--luajit` | Target LuaJIT 2.0 / 2.1 |
| `--lua51` | Target PUC-Rio Lua 5.1 |
| `--lua52` | Target PUC-Rio Lua 5.2 |
| `--lua53` | Target PUC-Rio Lua 5.3 |
| `--lua54` | Target PUC-Rio Lua 5.4 |
| `--lua55` | Target PUC-Rio Lua 5.5 |
| `--fivem` | Target FiveM/RedM (CfxLua, Lua 5.4 based) — **untested, see warning below** |
| `--gmod` / `--glua` | Target Garry's Mod (GLua, LuaJIT 2.0.4 based) |
| `--target <name>` | Specify target directly by name (e.g. `--target lua54`, `--target fivem`, `--target gmod`) |

> [!NOTE]
> `--vm` and `--fold` are mutually exclusive, and only one anti-tamper flag may be given at a time. Anti-tamper flags are independent of the mode flags.

## 🌐 Supported Lua Dialects

Weak provides native, first-class support for every major Lua dialect. Code generation, VM instruction dispatch, and runtime primitives are tailored to each runtime without polyfills or runtime shims.

> [!NOTE]
> The `--gmod`/`--glua` target was **verified in a real, licensed Garry's Mod client** (client Lua state, LuaJIT 2.0.4 on Windows): the obfuscated chunk was loaded with `lua_openscript_cl`, the demo HUD rendered, `concommand.Add` and `timer.Create` worked, and both the minimal and full anti-tamper builds passed GMod's realm checks without false positives. See [Garry's Mod (GLua) — Verified In-Game](#garrys-mod-glua-verified-in-game). The syntax layer (C-style comments, `!`/`!=`/`&&`/`\|\|`) and `bit`-library codegen reuse the already-tested LuaJIT engine.

| Dialect | Flag | Target Argument | Bitwise & Arithmetic Strategy | Special Syntax & Features |
| --- | --- | --- | --- | --- |
| **Luau** | `--luau` | `--target luau` | `bit32` library | Compound assignment operators, string interpolation, `continue` |
| **Roblox Luau** | `--roblox` | `--target roblox` | `bit32` library | Full Roblox executor anti-tamper and environment checks |
| **LuaJIT** | `--luajit` | `--target luajit` | Native `bit` library | `goto` and `::label::`, unsigned 32-bit arithmetic, global `unpack` |
| **Lua 5.1** | `--lua51` | `--target lua51` | Pure math / bit emulation | Global `unpack`, standard 5.1 syntax, universal compatibility |
| **Lua 5.2** | `--lua52` | `--target lua52` | Native `bit32` library | `goto` and `::label::`, `table.unpack`, `_ENV` support |
| **Lua 5.3** | `--lua53` | `--target lua53` | Native operators (`&`, `\|`, `~`, `<<`, `>>`, `//`) | 64-bit integer bitwise operators, `\u{...}` escapes |
| **Lua 5.4** | `--lua54` | `--target lua54` | Native operators (`&`, `\|`, `~`, `<<`, `>>`, `//`) | `<const>` and `<close>` variable attributes, native integer division |
| **Lua 5.5** | `--lua55` | `--target lua55` | Native operators (`&`, `\|`, `~`, `<<`, `>>`, `//`) | Modern Lua 5.5 grammar and standard library features |
| **FiveM / RedM** ⚠️ | `--fivem` | `--target fivem` | Native operators (`&`, `\|`, `~`, `<<`, `>>`, `//`) | CfxLua compound assignment (`+=`, `-=`, `*=`, `/=`, `^=`, `&=`, `\|=`, `<<=`, `>>=`), `` `backtick` `` compile-time Jenkins/joaat hash literals, FiveM-specific anti-tamper (`IsDuplicityVersion`, `Citizen.CreateThread`, natives, `exports`) — **see [FiveM / RedM Support](#-fivem--redm-support-unverified) below before using this in production** |
| **Garry's Mod (GLua)** | `--gmod` / `--glua` | `--target gmod` | `bit` library (LuaJIT-native, same as `--luajit`) | C-style comments (`//`, `/* */`), `!`, `!=`, `&&`, `\|\|` operator aliases, `continue`, GMod-specific anti-tamper (`SERVER`/`CLIENT`/`MENU_DLL` realm checks, `jit.version`, `hook`/`timer`/`net`/`concommand`/`cvars`/`game`/`util`/`ents` presence, `_R` removal check) |

### Garry's Mod (GLua): Verified In-Game

Unlike the FiveM target, the GLua target has been exercised in a real game, not just in an emulator.

**Test environment:** retail (licensed) Garry's Mod on Windows, client Lua state, LuaJIT 2.0.4 (`_VERSION == "Lua 5.1"`), script loaded with `lua_openscript_cl`.

**Verified in game:**

- the obfuscated chunk compiles and executes;
- the clientside `HUDPaint` hook renders the demo panel (HP/AP/FPS/ping/time);
- `concommand.Add("weak_demo_toggle")` toggles the panel;
- `timer.Create` fires;
- both `--minimal-anti-tamper` and `--full-anti-tamper` builds pass the GMod environment checks with no false-positive kills;
- deliberately tampered builds are still detected (decoy message followed by the kill).

**GMod-specific behaviour accounted for:**

- GMod does not expose `loadstring`/`load` — the generated loaders use `CompileString(code, identifier, handleError)` instead;
- `MENU_DLL` is `nil` in the client state (it only exists in the menu state), so the realm check accepts `nil` or a boolean;
- the global `type` is a Lua function (`garrysmod/lua/includes/util.lua`), not a C function, so it is not required to report `[C]`;
- LuaJIT reports fast functions with `[builtin...]` `short_src` values, so the C-function check accepts `[C]` and `[builtin...]`.

Demo scripts and generated samples are in `FIXES/demo/` of the fixed archive: `weak_demo.lua` (source), `weak_demo_obf.lua` (minimal), `weak_demo_obf_full.lua` (full), `weak_demo_obf_noat.lua` (no anti-tamper), and `weak_debug.lua` (in-game diagnostic).

### Native Architecture

- **Lua 5.x Unification (`lua5x_ast.py` & `lua5x_unparse.py`)**: All PUC-Rio Lua versions (5.1 through 5.5) are unified in a single version-parameterized AST engine. The parser automatically respects version-specific syntax rules (labels in 5.2+, bitwise operators and integer division in 5.3+, variable attributes in 5.4+).
- **Dedicated Luau Engine (`luau_ast.py` & `luau_unparse.py`)**: Standalone parser and unparser for Luau, supporting compound assignments, continue statements, and Luau grammar extensions.
- **Dedicated LuaJIT Engine (`luajit_ast.py` & `luajit_unparse.py`)**: Isolated engine handling LuaJIT 2.0 / 2.1 syntax, labels, and built-in `bit` library calls. The same engine powers `--gmod`/`--glua`, with GLua's C-style comments and `!`/`!=`/`&&`/`\|\|` operator aliases accepted on top.
- **Dialect-Native VM (`vm.py`)**: The bytecode virtual machine emits authentic native operators under Lua 5.3–5.5 (`&`, `\|`, `~`, `<<`, `>>`, `//`), standard `bit` calls on LuaJIT, `bit32` on Lua 5.2 and Luau, and arithmetic primitives on Lua 5.1.

## 🧩 Modes

| | **Fold** (`--fold`) | **VM** (default / `--vm`) |
| --- | --- | --- |
| Approach | Rewrites the Lua source | Compiles to custom bytecode, runs on a generated interpreter |
| Control-flow flattening | AST-based (`ast_cff.py`) | State-machine bytecode CFF (`bytecode_cff.py`) |
| String encryption | ✅ ChaCha20 | ✅ ChaCha20 |
| Number folding | ✅ | — |
| Chunked loading | ✅ | ✅ |
| On failure | Falls back to the unflattened source if the AST pass throws | Falls back to fold mode — or errors out if `--vm` was forced |

## ✨ Features

### 🖥️ Custom Bytecode VM

A full Lua compiler and bytecode interpreter, written from scratch.

- Source is lexed, parsed to an AST, and compiled to a custom bytecode format embedded as a byte array
- Runs on a register-based interpreter generated fresh for every build, with fully randomized variable names
- The opcode table is re-randomized on every run (`vm_opcodes.py`) — the same operation maps to different opcode numbers between builds
- Upvalues use shared cells, so closures capturing the same variable correctly share state
- **Supported:** all arithmetic operators including `//`, bitwise ops (`bit32`-backed), generic and numeric `for`, varargs, method calls (`:`), closures, tables (including multi-value / `...` list construction)
- On any compile failure the pipeline falls back to fold mode, so `--vm` never produces broken output

### 🔐 String Encryption

- **ChaCha20** stream cipher (ARX construction — add-rotate-xor)
- Fresh 256-bit key per build via `secrets`
- Unique 64-bit nonce per string, derived from its call ID — no two strings share a keystream
- Keystream is XORed against plaintext bytes only and never depends on the data
- Output is packed into a per-run shuffled printable-ASCII alphabet

### 🗝️ Key Hiding

<details>
<summary><b>Obfuscated cache keys</b></summary>

The internal string cache uses a composite key `call_id * MK + type`, where `MK` is a random 32-bit seed per run. Iterating the cache table doesn't reveal plaintext strings without knowing `MK`.

</details>

<details>
<summary><b>Scattered key derivation</b></summary>

Header key material is never stored as a single obvious constant. Each value is split into 4–6 shares combined through addition, XOR-masking, or rolling deltas, with decoy shares mixed in. A subset of shares is recovered through a small per-build pseudo-random derivation function (`drv_v`) instead of appearing as a literal.

</details>

<details>
<summary><b>Decoder name concealment</b></summary>

The decoder function name is never written as a string literal in the output. It's recovered at runtime by decrypting it through the decoder itself, so static searches for the decoder by name don't work.

</details>

### 📦 Chunked Source Loading

The obfuscated payload (flattened + folded source, or serialized VM bytecode) is split into **3–7 random chunks**. Each chunk is encrypted with the global key set, then decrypted and concatenated at runtime right before `loadstring`. No single string holds the full payload, which defeats simple `loadstring` hooks.

### 🎭 Identifier Obfuscation

Runtime variable names are random 6–10 character sequences of visually identical characters (`l`, `I`, `O`, `o`, `0`, `1`), re-randomized per run through a `secrets`-seeded RNG — names like `lI0OlI` and `OI1lO0` are indistinguishable at a glance.

### 🔀 Control-Flow Flattening

Two independent passes, depending on the mode:

- **Fold mode** — `ast_cff.py` works on the parsed source (via `luau_ast.py` / `luau_unparse.py`) and rewrites function and chunk bodies into a `while`-based dispatcher with randomized state IDs, shuffled block order, and junk branches
- **VM mode** — `bytecode_cff.py` exposes `flatten_bytecode_full`, which performs a real state-machine transformation directly on the VM bytecode:
  - every basic block is split at branch targets, returns, and loop edges
  - each block receives a random 31-bit state ID
  - blocks are laid out in shuffled order and all original block-to-block edges are removed
  - every block ends by assigning its successor state and jumping to a single dispatcher
  - the dispatcher indexes a per-function table that maps state IDs to PC values encrypted with a per-build XOR key, then performs an indirect jump with the `JUMP_REG` opcode (`GET_TABLE` + `BXOR` + `JUMP_REG`)
  - the table entries are shuffled and mixed with decoy states, while unreachable junk blocks and opaque arithmetic are inserted into the layout
  - scratch registers are allocated far outside the compiler's register range, so original locals, upvalue boxes, and multi-return spill slots are untouched
  - the pass runs recursively on every nested function prototype

- **Legacy VM mode** — the same `bytecode_cff.py` also exposes `flatten_bytecode`, which keeps the previous approach: basic blocks are shuffled and padded with junk instructions while direct jumps remain. It is still available with `--cff-legacy`.

> Full state-machine CFF is the default. Use `--cff-legacy` for the old behavior or `--no-cff` to disable bytecode-level flattening entirely.
>
> The older statement-text flattener (`cff.py`) is legacy and no longer used by either mode.

### 🔢 More

- **Number folding** — numeric literals become arithmetic expressions (`a+b`, `b-a`, `a*b`) chosen randomly per literal
- **Dispatch table** — 100+ anonymous functions covering arithmetic, comparison, string, and logic operations, inserted under random numeric keys per run

## 🛡️ Anti-Tamper

All checks run before any decryption begins.

| Category | Check |
| --- | --- |
| **Hook detection** | Error-message interception probe — repeatedly triggers `error()` through `pcall` and verifies the message survives unmodified |
| | Statistical / behavioral consistency across repeated `pcall` invocations |
| | `tostring` / metatable trap — confirms `__tostring` is honored and not intercepted |
| **Deobfuscation detection** | `debug.traceback()` line-number consistency, catching relocated or reformatted code |
| **Environment validation** | Roblox runtime behavior — exercises parts, physics, `Enum`, camera and player to confirm a real Roblox client rather than an emulated or partial environment |
| | 25+ standard function type checks (`rawget`, `setmetatable`, `pcall`, `string.byte`, …) |
| | Mathematical invariants (`1/0 == math.huge`, `0/0 ~= 0/0`, …) |
| | Timing — 100,000 iterations must finish in under 3 seconds |
| **Debugger detection** | Scans for `MobDebug`, `remdebug`, `LuaSocket`, `ldb`, `__debugger`, `BreakpointHook` |
| | Global checks for `__BREAKPOINT__`, `__DEBUG__`, `__ATTACHED__` |

All checked names are encrypted — none appear in plaintext in the output.

> Two further checks (a sandbox / JS-environment global scan and a `getfenv`-based environment probe) exist in the codebase but are **disabled by default** after producing false positives during testing.

### Anti-Tamper Levels

Full is the default — only step down if you're actually seeing false-positive kills.

| Level | Flag | Description |
| --- | --- | --- |
| 🟢 **Full** | `--full-anti-tamper` | Every check runs. Strongest protection. |
| 🟡 **Minimal** | `--minimal-anti-tamper` | Drops only the checks known to occasionally false-positive (see below). |
| 🔴 **None** | `--no-anti-tamper` | Disables anti-tamper entirely. **Not recommended** — makes the output significantly easier to deobfuscate. |

<details>
<summary><b>What does <code>--minimal-anti-tamper</code> remove?</b></summary>

- The `pcall` / `error` message-integrity probe
- The `debug.traceback()` line-consistency check
- The statistical / behavioral `pcall` consistency check
- The Roblox physics / timing behavior check (`BodyVelocity` / `BodyPosition` timing, `debug.getinfo` internals, `settings()`)

**Still active:** standard function / type checks, math invariants, the `tostring` / metatable trap, Lune / Lute / wally / rojo / JS-environment detection, the debugger name scan, and the `__BREAKPOINT__` / `__DEBUG__` / `__ATTACHED__` global checks.

</details>

## 🎮 Executor Compatibility

All anti-tamper checks in this build were tested and validated on **Delta**, where the default check set produces no false-positive kills. For the `--gmod`/`--glua` target the checks were additionally validated in a real, licensed Garry's Mod client (see [Garry's Mod (GLua) — Verified In-Game](#garrys-mod-glua-verified-in-game)).

Other executors are untested and may behave differently — some intentionally spoof or sandbox APIs like `getrawmetatable`, `getfenv`, or `_G` contents, which the anti-tamper layer can read as tampering.

**If you get a false-positive kill on another executor:**

1. Try `--minimal-anti-tamper` first — it resolves most cases without giving up all protection
2. Reproduce with a minimal script (a single `print("hello")`) to confirm the anti-tamper layer is the cause and not your own code
3. Bisect `build_anti_tamper` in `codegen.py`: comment out half of the checks in the final assembly block at the bottom of the function, rebuild, retest, and narrow it down
4. Disable the offending check or adjust its logic for that executor

Contributions and reports are welcome if you adapt the anti-tamper layer for other executors.

## 🎮 FiveM / RedM Support (Unverified)

> [!WARNING]
> **`--fivem` was implemented purely against publicly available CfxLua/FiveM documentation and native references — it has never been run against a real FXServer or game client.** The author doesn't own a GTA V license and isn't willing to download 100+ GB just to test it. Treat this target as **experimental / unverified** until someone confirms it works.

What `--fivem` does:

- Parses and re-emits CfxLua-specific syntax: compound assignment operators (`+=`, `-=`, `*=`, `/=`, `^=`, `&=`, `\|=`, `<<=`, `>>=`) and `` `backtick` `` compile-time hash literals (joaat), matching the algorithm used by `GetHashKey`
- Uses native Lua 5.4 operators for bitwise/integer-division code generation (no `bit32` emulation, since CfxLua doesn't need it)
- Adds FiveM-specific anti-tamper checks: `_VERSION == 'Lua 5.4'`, presence and type of `IsDuplicityVersion`, `GetCurrentResourceName`, `GetInvokingResource`, `GetGameTimer`, `Citizen.CreateThread` / `Wait` / `Await` / `InvokeNative`, global `CreateThread` / `Wait` / `AddEventHandler` / `RegisterNetEvent` / `TriggerEvent`, and `exports`

What's **not** implemented, even though CfxLua supports it — using any of these in your source will fail to parse under `--fivem`:

- Safe navigation (`?.`)
- `in`-unpacking (`local a, b, c in t`)
- Set constructors (`{ .debug, level = 5 }`)
- C-style comments (`//`, `/* */`)

**Biggest unverified assumption:** that `_VERSION` actually evaluates to the literal string `"Lua 5.4"` inside CfxLua, and that `debug.getinfo(fn, 'S').short_src` returns `'[C]'` for native/engine functions the same way vanilla Lua does. If either assumption is wrong, the anti-tamper layer will self-kill every obfuscated FiveM script immediately on load. Both are testable on a bare FXServer (server-side only, no GTA V client needed) with something like:

```lua
print(_VERSION)
print(debug.getinfo(print, 'S').short_src)
```

**If you run this on a real server, please open an issue (or PR) saying whether it worked or not** — false-positive anti-tamper kills, parse errors on real resource scripts, or anything else you hit. This is the one target in the project the author genuinely cannot self-verify, so real-world reports are the only way it gets fixed.

## 📁 Project Structure

```
.
├── main.py             CLI entry point
├── obfuscator.py       Main pipeline, chunk splitting, chunk loader
├── codegen.py          Runtime header, dispatch table, anti-tamper, name generation
├── crypto.py           ChaCha20 stream cipher, alphabet shuffle, encode/decode
├── string_fold.py      String extraction and in-place encryption
├── number_fold.py      Numeric literal → arithmetic expression rewriting
├── lua5x_ast.py        Unified Lua 5.1--5.5 lexer/parser producing an AST
├── lua5x_unparse.py    AST → Lua 5.1--5.5 source printer
├── luajit_ast.py       Dedicated LuaJIT lexer/parser
├── luajit_unparse.py   AST → LuaJIT source printer
├── luau_ast.py         Dedicated Luau lexer/parser producing an AST
├── luau_unparse.py     AST → Luau source printer
├── ast_cff.py          AST-based control-flow flattening (fold mode)
├── bytecode_cff.py     Full state-machine and legacy block-reorder bytecode CFF
├── mld.py              Field dictionary encoding and compression
├── mltn.py             Bytecode RLE & dictionary packing
├── vm.py               Lexer, parser, compiler, serializer, interpreter generator
├── vm_opcodes.py       Randomized opcode table generator
└── cff.py              Legacy statement-text flattener (unused)
```

## ⚠️ Limitations

- Source-level obfuscator — it doesn't modify Roblox bytecode directly
- Strings are treated as raw bytes 0–255, so non-ASCII text (Cyrillic, etc.) is not round-tripped correctly
- ChaCha20 gives strong per-string confidentiality, but the goal is reverse-engineering difficulty for a source-level tool, not general-purpose secure transport
- Every run produces a unique output

## 📜 History

This project didn't start out ambitious. The first public version used an LCG cipher with hardcoded seed constants shared across every build instead of a fresh per-run key, and its "VM" was just a dispatch table of hashed inline functions — closer to a dispatch trick than a real bytecode compiler. It offered close to no protection, and the name was picked because it was, plainly and honestly, weak.

Then something clicked, and a throwaway project became an ongoing effort to make it actually good: a from-scratch VM with a custom bytecode format, a per-build ChaCha20 key, anti-tamper layers refined against real executor behavior, and control-flow flattening at both the AST and bytecode level. The name never changed, even as the project outgrew it many times over.

## 🤝 Credits

Built by **Melodieshusband**, with significant help from Claude (Anthropic).


## 📄 License

Released under the [MIT License](LICENSE).
