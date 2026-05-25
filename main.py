import sys
from obfuscator import Obfuscator

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.lua> [output.lua]")
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace(".lua", "_obf.lua")

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    obf = Obfuscator(source)
    result, mode = obf.obfuscate()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"[+] Input:  {input_path}")
    print(f"[+] Output: {output_path}")
    print(f"[+] Mode:   {mode}")

if __name__ == "__main__":
    main()
