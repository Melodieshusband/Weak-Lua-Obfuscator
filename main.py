import sys
import re
from obfuscator import Obfuscator

def main():
    args = sys.argv[1:]
    force_vm   = '--vm'   in args
    force_fold = '--fold' in args
    args = [a for a in args if not a.startswith('--')]

    if not args:
        print("Usage: python main.py <input.lua> [output.lua] [--vm | --fold]")
        print("  --vm    Use VM bytecode")
        print("  --fold  Use string-fold (without VM)")
        sys.exit(1)

    if force_vm and force_fold:
        print("[!] Hi it's Meloten. You cannot use --vm and --fold")
        sys.exit(1)

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
        result, mode = obf.obfuscate(force_vm=force_vm, force_fold=force_fold)
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
    
