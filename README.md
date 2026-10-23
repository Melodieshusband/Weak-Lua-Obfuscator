<div align="center">

# 🌑 Weak

### Multi-Dialect Lua & Luau Obfuscator

A source-level obfuscator written in pure Python — custom bytecode VM, ChaCha20 string encryption, control-flow flattening, and native support across all major Lua runtimes.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Targets](https://img.shields.io/badge/targets-Lua%205.1--5.5%20%7C%20LuaJIT%20%7C%20Luau-success)

[Quick Start](#-quick-start) •
[Supported Dialects](#-supported-lua-dialects) •
[Features](#-features) •
[Modes](#-modes) •
[Anti-Tamper](#-anti-tamper) •
[Compatibility](#-executor-compatibility) •
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
python main.py <input.lua> [output.lua] [--vm | --fold] [anti-tamper flag]
```

| Example | What it does |
| --- | --- |
| `python main.py input.lua` | Default (VM) mode, full anti-tamper |
| `python main.py input.lua output.lua --fold` | Explicit fold mode |
| `python main.py input.lua output.lua --vm` | Explicit VM mode |
| `python main.py input.lua output.lua --minimal-anti-tamper` | Relaxed anti-tamper for picky executors |
| `python main.py input.lua output.lua --vm --minimal-anti-tamper` | VM mode + relaxed anti-tamper |
| `python main.py input.lua output.lua --no-anti-tamper` | No anti-tamper (not recommended) |

### Flags

| Flag | Description |
| --- | --- |
| `--vm` | Compile the script to custom bytecode and run it on a per-build interpreter **(default)** |
| `--fold` | Control-flow flattening + number folding + string encryption, no VM |
| `--hide-vm-source` | Encrypt the VM dispatch loop (requires loadstring/load) |
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
| `--target <name>` | Specify target directly by name (e.g. `--target lua54`) |

> [!NOTE]
> `--vm` and `--fold` are mutually exclusive, and only one anti-tamper flag may be given at a time. Anti-tamper flags are independent of the mode flags.

## 🌐 Supported Lua Dialects

Weak provides native, first-class support for every major Lua dialect. Code generation, VM instruction dispatch, and runtime primitives are tailored to each runtime without polyfills or runtime shims.

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

### Native Architecture

- **Lua 5.x Unification (`lua5x_ast.py` & `lua5x_unparse.py`)**: All PUC-Rio Lua versions (5.1 through 5.5) are unified in a single version-parameterized AST engine. The parser automatically respects version-specific syntax rules (labels in 5.2+, bitwise operators and integer division in 5.3+, variable attributes in 5.4+).
- **Dedicated Luau Engine (`luau_ast.py` & `luau_unparse.py`)**: Standalone parser and unparser for Luau, supporting compound assignments, continue statements, and Luau grammar extensions.
- **Dedicated LuaJIT Engine (`luajit_ast.py` & `luajit_unparse.py`)**: Isolated engine handling LuaJIT 2.0 / 2.1 syntax, labels, and built-in `bit` library calls.
- **Dialect-Native VM (`vm.py`)**: The bytecode virtual machine emits authentic native operators under Lua 5.3–5.5 (`&`, `\|`, `~`, `<<`, `>>`, `//`), standard `bit` calls on LuaJIT, `bit32` on Lua 5.2 and Luau, and arithmetic primitives on Lua 5.1.

## 🧩 Modes

| | **Fold** (`--fold`) | **VM** (default / `--vm`) |
| --- | --- | --- |
| Approach | Rewrites the Lua source | Compiles to custom bytecode, runs on a generated interpreter |
| Control-flow flattening | AST-based (`ast_cff.py`) | Bytecode-level (`bytecode_cff.py`) |
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
- **VM mode** — `bytecode_cff.py` flattens the compiled bytecode itself: basic blocks are split, reordered behind a dispatcher, and padded with junk instructions — independent of, and in addition to, the VM's own opcode randomization

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

All anti-tamper checks in this build were tested and validated on **Delta**, where the default check set produces no false-positive kills.

Other executors are untested and may behave differently — some intentionally spoof or sandbox APIs like `getrawmetatable`, `getfenv`, or `_G` contents, which the anti-tamper layer can read as tampering.

**If you get a false-positive kill on another executor:**

1. Try `--minimal-anti-tamper` first — it resolves most cases without giving up all protection
2. Reproduce with a minimal script (a single `print("hello")`) to confirm the anti-tamper layer is the cause and not your own code
3. Bisect `build_anti_tamper` in `codegen.py`: comment out half of the checks in the final assembly block at the bottom of the function, rebuild, retest, and narrow it down
4. Disable the offending check or adjust its logic for that executor

Contributions and reports are welcome if you adapt the anti-tamper layer for other executors.

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
├── bytecode_cff.py     Bytecode-level control-flow flattening (VM mode)
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
