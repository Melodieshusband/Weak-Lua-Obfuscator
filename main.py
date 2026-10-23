import sys
import re
from obfuscator import Obfuscator

def main():
    raw_args = sys.argv[1:]
    force_vm = '--vm' in raw_args
    force_fold = '--fold' in raw_args
    hide_vm_source = '--hide-vm-source' in raw_args

    at_none = '--no-anti-tamper' in raw_args
    at_minimal = '--minimal-anti-tamper' in raw_args
    at_full = '--full-anti-tamper' in raw_args
    at_v1 = '--at-v1' in raw_args

    at_version = "v1" if at_v1 else "v2"

    target_names = []
    target_flags = {
        '--luau': 'luau',
        '--roblox': 'roblox',
        '--luajit': 'luajit',
        '--lua51': 'lua51',
        '--lua5.1': 'lua51',
        '--lua52': 'lua52',
        '--lua5.2': 'lua52',
        '--lua53': 'lua53',
        '--lua5.3': 'lua53',
        '--lua54': 'lua54',
        '--lua5.4': 'lua54',
        '--lua55': 'lua55',
        '--lua5.5': 'lua55',
    }

    alias_map = {
        'luau': 'luau',
        'roblox': 'roblox',
        'luajit': 'luajit',
        'jit': 'luajit',
        'lua51': 'lua51',
        'lua5.1': 'lua51',
        '5.1': 'lua51',
        '51': 'lua51',
        'lua52': 'lua52',
        'lua5.2': 'lua52',
        '5.2': 'lua52',
        '52': 'lua52',
        'lua53': 'lua53',
        'lua5.3': 'lua53',
        '5.3': 'lua53',
        '53': 'lua53',
        'lua54': 'lua54',
        'lua5.4': 'lua54',
        '5.4': 'lua54',
        '54': 'lua54',
        'lua55': 'lua55',
        'lua5.5': 'lua55',
        '5.5': 'lua55',
        '55': 'lua55',
    }

    pos_args = []
    i = 0
    while i < len(raw_args):
        a = raw_args[i]
        if a in target_flags:
            target_names.append(target_flags[a])
            i += 1
        elif a.startswith('--target='):
            tval = a.split('=', 1)[1].strip().lower()
            if tval in alias_map:
                target_names.append(alias_map[tval])
            else:
                print(f"[!] Unknown target: {tval}")
                sys.exit(1)
            i += 1
        elif a == '--target':
            if i + 1 < len(raw_args):
                tval = raw_args[i + 1].strip().lower()
                if tval in alias_map:
                    target_names.append(alias_map[tval])
                else:
                    print(f"[!] Unknown target: {tval}")
                    sys.exit(1)
                i += 2
            else:
                print("[!] Missing target name after --target")
                sys.exit(1)
        elif a.startswith('--'):
            i += 1
        else:
            pos_args.append(a)
            i += 1

    if len(target_names) > 1:
        print(f"[!] Conflicting target flags specified: {', '.join(target_names)}")
        sys.exit(1)

    at_target = target_names[0] if target_names else "luau"

    if not pos_args:
        print("Usage: python main.py <input.lua> [output.lua] [--vm | --fold] [anti-tamper flags] [target flags]")
        print("Modes:")
        print("  --vm                     Use VM bytecode (default)")
        print("  --fold                   Use string-fold (without VM)")
        print("  --hide-vm-source         Encrypt the VM dispatch loop (requires loadstring/load)")
        print("")
        print("Dialect / Target flags (default: --luau):")
        print("  --luau                   Target Luau")
        print("  --roblox                 Target Roblox runtime")
        print("  --luajit                 Target LuaJIT")
        print("  --lua51                  Target Lua 5.1")
        print("  --lua52                  Target Lua 5.2")
        print("  --lua53                  Target Lua 5.3")
        print("  --lua54                  Target Lua 5.4")
        print("  --lua55                  Target Lua 5.5")
        print("  --target <name>          Specify target name directly")
        print("")
        print("Anti-Tamper flags:")
        print("  --full-anti-tamper       All checks enabled (default)")
        print("  --minimal-anti-tamper    Relaxed checks for sandboxes/hooked environments")
        print("  --no-anti-tamper         Disable anti-tamper")
        print("  --at-v1                  Use legacy Anti-Tamper v1 (Roblox physics/timing)")
        sys.exit(1)

    if force_vm and force_fold:
        print("[!] You cannot use --vm and --fold simultaneously.")
        sys.exit(1)

    if sum([at_none, at_minimal, at_full]) > 1:
        print("[!] You can only pick one of: --full-anti-tamper, --minimal-anti-tamper, --no-anti-tamper")
        sys.exit(1)

    if hide_vm_source:
        print("[!] WARNING: --hide-vm-source loads the VM dispatch loop via loadstring/load.")
        print("[!] This is a WEAK protection method. Any executor, debugger or hook that")
        print("[!] intercepts loadstring/load can recover the plain VM source.")
        try:
            answer = input("[?] Continue with this weak protection method? (Y/N): ").strip().lower()
        except EOFError:
            answer = "n"
        if answer != "y":
            print("[!] Aborted.")
            sys.exit(0)

    if at_none:
        anti_tamper_level = "none"
    elif at_minimal:
        anti_tamper_level = "minimal"
    else:
        anti_tamper_level = "full"

    input_path = pos_args[0]
    if len(pos_args) > 1:
        output_path = pos_args[1]
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

    print(f"[+] Input:   {input_path}")
    print(f"[+] Output:  {output_path}")
    print(f"[+] Target:  {at_target}")
    print(f"[+] Mode:    {mode}")

if __name__ == "__main__":
    main()
