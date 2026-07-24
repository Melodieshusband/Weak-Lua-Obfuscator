import sys
import re
from obfuscator import Obfuscator

def main():
    args = sys.argv[1:]
    force_vm   = '--vm'   in args
    force_fold = '--fold' in args

    at_none    = '--no-anti-tamper'      in args
    at_minimal = '--minimal-anti-tamper' in args
    at_full    = '--full-anti-tamper'    in args

    args = [a for a in args if not a.startswith('--')]

    if not args:
        print("Usage: python main.py <input.lua> [output.lua] [--vm | --fold] [anti-tamper flag]")
        print("  --vm                     Use VM bytecode")
        print("  --fold                   Use string-fold (without VM)")
        print("")
        print("Anti-Tamper flags (default: full):")
        print("  --full-anti-tamper       All checks enabled (default, strongest protection)")
        print("  --minimal-anti-tamper    Drops only the checks known to false-positive on")
        print("                           some executors (behavioral/timing/hook-probing")
        print("                           checks). Use this if a specific executor kills the")
        print("                           script on load with no other explanation.")
        print("  --no-anti-tamper         Disables anti-tamper entirely (NOT recommended,")
        print("                           makes the output much easier to deobfuscate)")
        sys.exit(1)

    if force_vm and force_fold:
        print("[!] Hi it's Meloten. You cannot use --vm and --fold")
        sys.exit(1)

    if sum([at_none, at_minimal, at_full]) > 1:
        print("[!] You can only pick one of: --full-anti-tamper, --minimal-anti-tamper, --no-anti-tamper")
        sys.exit(1)

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

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    obf = Obfuscator(source)
    try:
        result, mode = obf.obfuscate(
            force_vm=force_vm, force_fold=force_fold,
            anti_tamper_level=anti_tamper_level,
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
