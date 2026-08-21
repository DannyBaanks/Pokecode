#!/usr/bin/env python3
"""
CI Script: Generate PokéCode ASCII logo using pure Mew unary encoding.
Outputs PokéCode logo (Pokéball + "POKÉCODE") to be placed at top of README.
"""

# Mew unary encoding: N Mews = opcode N-1
# We use HYPNO (OUT, opcode 97) to print ACC as char
# To set ACC: EEVEE ABRA (ACC=0) then MUK (INC) repeated N times
# EEVEE = 10 Mews (opcode 9), ABRA = 2 Mews (opcode 1)
# MUK = 47 Mews (opcode 46), HYPNO = 98 Mews (opcode 97)

MEW = "Mew "

def mews(opcode: int) -> str:
    """Return Mew string for given opcode value."""
    return MEW * (opcode + 1)

EEVEE = 9    # MEM_CLR
ABRA = 1     # MEM_RD
MUK = 46     # INC
HYPNO = 97   # OUT (putchar ACC)

def mew_seq_for_char(c: str) -> str:
    """Generate Mew sequence to output character c."""
    code = ord(c)
    seq = mews(9) + mews(ABRA)  # EEVEE ABRA (ACC=0)
    seq += mews(MUK) * code     # MUK * code
    seq += mews(HYPNO)          # HYPNO (OUT)
    return seq

def pokecode_seq_for_char(c: str) -> str:
    """Generate PokéCode (names) for character c."""
    code = ord(c)
    if code == 0:
        return ""
    seq = "EEVEE ABRA " + " ".join(["MUK"] * code) + " HYPNO "
    return seq

def gen_ascii_art():
    """Generate the actual ASCII art (rendered)."""
    lines = [
        "  .--.   ",
        " /    \\  ",
        "|  @ @ | ",
        "|      | ",
        " \\    /  ",
        "  '--'   ",
        "",
        "P O K E C O D E",
        ""
    ]
    return "\n".join(lines)

def gen_mew_unary():
    """Generate the pure Mew unary program."""
    lines = [
        "  .--.   ",
        " /    \\  ",
        "|  @ @ | ",
        "|      | ",
        " \\    /  ",
        "  '--'   ",
        "",
        "P O K E C O D E",
        ""
    ]
    
    output = ""
    for line in lines:
        for ch in line:
            output += mews(EEVEE) + mews(ABRA) + mews(MUK) * ord(ch) + mews(HYPNO)
        output += mews(EEVEE) + mews(ABRA) + mews(MUK) * 10 + mews(HYPNO)  # newline
    return output

def gen_pokecode_names():
    """Generate human-readable PokéCode names."""
    lines = [
        "  .--.   ",
        " /    \\  ",
        "|  @ @ | ",
        "|      | ",
        " \\    /  ",
        "  '--'   ",
        "",
        "P O K E C O D E",
        ""
    ]
    
    output = []
    for line in lines:
        line_seq = []
        for ch in line:
            line_seq.append(pokecode_seq_for_char(ch))
        # newline
        line_seq.append(pokecode_seq_for_char('\n'))
        output.append(" ".join(line_seq).strip())
    return "\n".join(output)

def main():
    print("=" * 70)
    print("POKÉCODE LOGO - CI Generator")
    print("=" * 70)
    print()
    print("# RENDERED ASCII ART (for README top)")
    print()
    print("```")
    print(gen_ascii_art())
    print("```")
    print()
    print("---")
    print()
    print("# PURE MEW UNARY PROGRAM (paste into pokemon_interpreter.py -c)")
    print()
    mew_program = gen_mew_unary()
    print(f"# Length: {len(mew_program.split())} Mews")
    print(mew_program)
    print()
    print("---")
    print()
    print("# POKÉCODE NAMES (human readable)")
    print()
    print(gen_pokecode_names())

if __name__ == "__main__":
    main()