import sys
import re
from obfuscator import Obfuscator

def main():
    args = sys.argv[1:]
    force_vm   = '--vm'   in args
    force_fold = '--fold' in args
    hide_vm_source = '--hide-vm-source' in args

    at_none    = '--no-anti-tamper'      in args
    at_minimal = '--minimal-anti-tamper' in args
    at_full    = '--full-anti-tamper'    in args
    at_v1      = '--at-v1'               in args
    target_rbx = '--roblox'              in args
    target_lj  = '--luajit'              in args

    at_version = "v1" if at_v1 else "v2"

    if target_rbx and target_lj:
        print("[!] You can only pick one of: --roblox, --luajit")
        sys.exit(1)

    at_target = "roblox" if target_rbx else ("luajit" if target_lj else "luau")

    args = [a for a in args if not a.startswith('--')]

    if not args:
        print("Usage: python main.py <input.lua> [output.lua] [--vm | --fold] [anti-tamper flags]")
        print("  --vm                     Use VM bytecode (default)")
        print("  --fold                   Use string-fold (without VM)")
        print("  --hide-vm-source         With --vm, encrypt the VM dispatch loop itself")
        print("                           and load it with loadstring/load instead of")
        print("                           emitting it as plain Lua. Breaks executors that")
        print("                           block loadstring, so it is off by default.")
        print("")
        print("Anti-Tamper flags (default: v2 full, target: luau):")
        print("  --full-anti-tamper       All checks enabled (default, strongest protection)")
        print("  --minimal-anti-tamper    Drops checks known to false-positive on picky executors")
        print("  --no-anti-tamper         Disables anti-tamper entirely")
        print("  --at-v1                  Use legacy Anti-Tamper v1 (Roblox physics/timing)")
        print("  --roblox                 Target Roblox environment (default is pure Luau)")
        print("  --luajit                 Target LuaJIT (adds a bit32/table.pack-unpack shim")
        print("                           and swaps the anti-tamper checks to LuaJIT APIs)")
        sys.exit(1)

    if force_vm and force_fold:
        print("[!] Hi it's Meloten. You cannot use --vm and --fold")
        sys.exit(1)

    if sum([at_none, at_minimal, at_full]) > 1:
        print("[!] You can only pick one of: --full-anti-tamper, --minimal-anti-tamper, --no-anti-tamper")
        sys.exit(1)

    if hide_vm_source:
        print("[!] WARNING: --hide-vm-source loads the VM dispatch loop via loadstring/load.")
        print("[!] This is a WEAK protection method. Any executor, debugger or hook that")
        print("[!] intercepts loadstring/load (a very common technique) can recover the")
        print("[!] plain VM source directly from memory, which defeats this protection")
        print("[!] completely. Only use this if your target environment truly requires it.")
        try:
            answer = input("[?] Continue with this weak protection method? (Y/N): ").strip().lower()
        except EOFError:
            answer = "n"
        if answer != "y":
            print("[!] Aborted. Re-run without --hide-vm-source for the stronger default mode.")
            sys.exit(0)

    if at_none:
        anti_tamper_level = "none"
    elif at_minimal:
        anti_tamper_level = "minimal"
    else:
        anti_tamper_level = "full"

    input_path  = args[0]
    if len(args) > 1:
        output_path = args[1]
    else:
        base = re.sub(r'\.lua$', '', input_path)
        output_path = base + "_obf.lua"

    with open(input_path, "r", encoding="utf-8-sig") as f:
        source = f.read()

    obf = Obfuscator(source)
    try:
        result, mode = obf.obfuscate(
            force_vm=force_vm, force_fold=force_fold,
            anti_tamper_level=anti_tamper_level,
            hide_vm_source=hide_vm_source,
            at_version=at_version,
            at_target=at_target,
        )
    except RuntimeError as e:
        print(f"[!] {e}")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"[+] Input:  {input_path}")
    print(f"[+] Output: {output_path}")
    print(f"[+] Mode:   {mode}")

if __name__ == "__main__":
    main()
