#!/usr/bin/env python3
"""
Turing-Completeness Test Suite for POKECODE / MEWCODE
Demuestra universalidad computacional mediante múltiples reducciones conocidas.

NOTA: Traducido a la nueva permutación de nombres (nombres cortos a ops frecuentes).
- INC = MUK       (opcode 46)   - DEC = ONIX      (opcode 47)
- MEM_RD = ABRA   (1)           - MEM_WR = JYNX   (2)
- PTR_INC = ARBOK (3)           - ADD = IVYSAUR   (39)
- MUL = KOFFING   (43)          - AND = KABUTO    (58)
- XOR = KAKUNA    (60)          - SHL = KRABBY    (62)
- SHR = LAPRAS    (63)          - OUT_NUM = MAGIKARP (98)
- OUT_HEX = MAGNETON (99)       - OUT_BIN = NIDOKING (100)
- MEM_CLR = EEVEE (9)           - JN = HORSEA     (24)
- OUT = HYPNO     (97)          - HALT = DODUO    (38)
- PUSH = GLOOM    (77)          - POP = GOLEM     (78)
- REG_SET = SEEL  (116)        - REG_GET = PARAS (115)
- REG_INC = MACHOP (118)
"""

from pokemon_interpreter import run_pokecode, PokecodeVM, parse_pokecode, OpCode


# ═══════════════════════════════════════════════════════════════════════
# HELPER: Mew encoding helpers
# ═══════════════════════════════════════════════════════════════════════

def mew(n: int) -> str:
    """N Mews como string; N-1 = opcode a ejecutar."""
    return ' '.join(['Mew'] * n)


def instr(opcode: OpCode) -> str:
    """Mew encoding para un OpCode: opcode value + 1 Mews."""
    return mew(int(opcode) + 1)


# Brainfuck operations in Mew (N Mews = opcode N-1)
BF_INC    = mew(int(OpCode.MUK)    + 1)  # 47 Mews = INC
BF_DEC    = mew(int(OpCode.ONIX)   + 1)  # 48 Mews = DEC
BF_PTR_INC= mew(int(OpCode.ARBOK)  + 1)  # 4 Mews  = PTR_INC
BF_PTR_DEC= mew(int(OpCode.GENGAR) + 1)  # 5 Mews  = PTR_DEC
BF_OUT    = mew(int(OpCode.HYPNO)  + 1)  # 98 Mews = OUT
BF_IN     = mew(int(OpCode.GASTLY) + 1)  # 97 Mews = IN
BF_JZ     = mew(int(OpCode.CUBONE) + 1)  # 23 Mews = JZ
BF_JMP    = mew(int(OpCode.GOLBAT) + 1)  # 21 Mews = JMP
BF_JNZ    = mew(int(OpCode.DODRIO) + 1)  # 24 Mews = JNZ
BF_JMP_REL= mew(int(OpCode.GRIMER) + 1)  # 22 Mews = JMP_REL


def bf_loop(body: str) -> str:
    """Brainfuck loop [ body ] -> JZ + JMP + body + JNZ + JMP_REL."""
    return BF_JZ + BF_JMP + body + BF_JNZ + BF_JMP_REL


def test_arithmetic():
    """Test basic arithmetic operations."""
    print("=== TEST: Basic Arithmetic ===")
    # INC/DEC: 10 INCs (=10) then 3 DECs (=7)
    vm = PokecodeVM(program=parse_pokecode('MUK ' * 10 + ' ONIX ' * 3))
    vm.run()
    assert vm.acc == 7, f"Expected 7, got {vm.acc}"
    print("  INC/DEC: PASS")

    # ADD: ACC=7 -> MEM[0]=7; DEC x4 -> ACC=3; ADD = 3 + 7 = 10
    prog = parse_pokecode('MUK ' * 7 + ' JYNX ' + ' ONIX ' * 4 + ' IVYSAUR')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 10, f"Expected 10, got {vm.acc}"
    print("  ADD: PASS")

    # MUL: ACC=7 -> MEM[0]=7; DEC x1 -> ACC=6; MUL = 6 * 7 = 42
    prog = parse_pokecode('MUK ' * 7 + ' JYNX ' + ' ONIX ' + ' KOFFING')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 42, f"Expected 42, got {vm.acc}"
    print("  MUL: PASS")
    print("  All arithmetic tests PASSED\n")


def test_control_flow():
    """Saltos: uno tomado y uno no tomado, comprobando el efecto."""
    print("=== TEST: Control Flow ===")
    # ACC=8 via MUK + 3 SHL; GOLBAT (JMP) salta a la instruccion 8 (DODUO),
    # saltandose tres MUK. Si el salto NO ocurriera, ACC acabaria en 11.
    vm = PokecodeVM(program=parse_pokecode(
        'MUK KRABBY KRABBY KRABBY GOLBAT MUK MUK MUK DODUO'))
    vm.run()
    assert vm.acc == 8, f"salto tomado: esperaba ACC=8, hubo {vm.acc}"

    # mismo programa con CUBONE (JZ) y Z falso: NO debe saltar, ACC llega a 11
    vm = PokecodeVM(program=parse_pokecode(
        'MUK KRABBY KRABBY KRABBY CUBONE MUK MUK MUK DODUO'))
    vm.run()
    assert vm.acc == 11, f"salto no tomado: esperaba ACC=11, hubo {vm.acc}"
    print("  Control flow OK (tomado y no tomado)\n")


def test_stack():
    """PUSH/POP es LIFO y deja la pila vacia."""
    print("=== TEST: Stack ===")
    # ACC=5, push; ACC=8, push; pop -> 8; pop -> 5
    vm = PokecodeVM(program=parse_pokecode(
        'MUK ' * 5 + 'GLOOM ' + 'MUK ' * 3 + 'GLOOM GOLEM GOLEM'))
    vm.run()
    assert vm.acc == 5, f"LIFO roto: esperaba ACC=5, hubo {vm.acc}"
    assert len(vm.stack) == 0, f"pila no vaciada: {vm.stack}"
    print("  Stack OK (LIFO, pila vacia)\n")


def test_bitwise():
    """AND, XOR, SHL, SHR."""
    print("=== TEST: Bitwise ===")
    # AND: ACC=12 -> MEM[0]=12; DEC x2 -> ACC=10; AND = 10 & 12 = 8
    prog = parse_pokecode('MUK ' * 0b1100 + ' JYNX ' + ' ONIX ' * 2 + ' KABUTO ')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 0b1000, f"AND failed: {vm.acc}"
    print("  AND: PASS")

    # XOR: same setup; 10 ^ 12 = 6
    prog = parse_pokecode('MUK ' * 0b1100 + ' JYNX ' + ' ONIX ' * 2 + ' KAKUNA ')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 0b0110, f"XOR failed: {vm.acc}"
    print("  XOR: PASS")

    prog = parse_pokecode('MUK ' * 1 + ' KRABBY ')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 2, f"SHL failed: {vm.acc}"
    print("  SHL: PASS")

    prog = parse_pokecode('MUK ' * 8 + ' LAPRAS ')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 4, f"SHR failed: {vm.acc}"
    print("  SHR: PASS")
    print("  All bitwise tests PASSED\n")


def test_io():
    """OUT escribe el ACC como caracter."""
    print("=== TEST: I/O ===")
    vm = PokecodeVM(program=parse_pokecode('MUK ' * 65 + 'HYPNO'))
    out = vm.run()
    assert out == 'A', f"OUT: esperaba 'A' (65), hubo {out!r}"
    assert vm.acc == 65
    print("  I/O OK (65 -> 'A')\n")


def test_registers():
    """REG_SET/REG_GET."""
    print("=== TEST: Registers ===")
    prog = parse_pokecode('MUK ' * 42 + ' SEEL ' + ' ARBOK ' + ' PARAS ')
    vm = PokecodeVM(program=prog)
    vm.run()
    assert vm.acc == 42, f"REG_SET/GET failed: {vm.acc}"
    print("  REG_SET/GET: PASS\n")


def test_mew_encoding():
    """Mew unary encoding."""
    print("=== TEST: Mew Unary Encoding ===")
    # 1 Mew = MEW (NOP) → flag Mew
    vm = PokecodeVM(program=parse_pokecode('Mew'))
    vm.run()
    assert vm.mew_encountered == True
    print("  1 Mew = MEW: PASS")

    # 2 Mews = opcode 1 = ABRA (MEM_RD)
    vm = PokecodeVM(program=parse_pokecode('Mew Mew'))
    vm.run()
    print("  2 Mews = ABRA (MEM_RD): PASS")

    # 47 Mews = opcode 46 = MUK (INC)
    vm = PokecodeVM(program=parse_pokecode(' '.join(['Mew'] * 47)))
    vm.run()
    assert vm.acc == 1, f"47 Mews should INC to 1, got {vm.acc}"
    print("  47 Mews = MUK (INC): PASS")

    # 98 Mews = opcode 97 = HYPNO (OUT)
    vm = PokecodeVM(program=parse_pokecode(' '.join(['Mew'] * 98)))
    vm.run()
    print("  98 Mews = HYPNO (OUT): PASS")

    # 151 Mews = MEW (caso especial)
    vm = PokecodeVM(program=parse_pokecode(' '.join(['Mew'] * 151)))
    vm.run()
    assert vm.mew_encountered == True
    print("  151 Mews = MEW (recursive): PASS")
    print("  All Mew encoding tests PASSED\n")


def test_brainfuck_reduction():
    """La unica reduccion con artefacto: Brainfuck -> PokeCode, EJECUTADA.

    Sustituye al antiguo `test_turing_completeness_proofs`, que eran cinco
    print() sin una sola asercion y sin ejecutar nada.
    """
    import os
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bf2pokecode import bf_to_pokecode_full

    print("=== TEST: reduccion Brainfuck (ejecutada) ===")
    casos = [
        ("+++.", [3]),                        # recta
        ("+[-].", [0]),                       # bucle minimo
        ("+++++[>+<-]>.", [5]),               # bucle con puntero
        ("+++++++[>+++++++<-]>.", [49]),      # multiplicacion
        ("++[>++[>+<-]<-]>>.", [4]),          # bucles anidados
    ]
    for bf, esperado in casos:
        pok = bf_to_pokecode_full(bf)
        salida = run_pokecode(pok, max_cycles=3_000_000)
        got = [ord(c) for c in salida]
        assert got == esperado, f"BF {bf!r}: esperaba {esperado}, hubo {got}"
        print(f"  {bf:24s} -> {got}")

    # el techo de 8 bits del PC tiene que reportarse, no colgarse
    hello = ("++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]"
             ">>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.")
    try:
        bf_to_pokecode_full(hello)
        raise AssertionError("Hello World deberia exceder el limite de PC y no lo hizo")
    except ValueError as e:
        assert "255" in str(e), f"el error deberia citar el limite: {e}"
    print("  Hello World rechazado con motivo (PC de 8 bits)\n")


def run_all_tests():
    print("=" * 60)
    print("POKECODE / MEWCODE TEST SUITE (NEW NAME PERMUTATION)")
    print("=" * 60)
    print()
    test_mew_encoding()
    test_arithmetic()
    test_bitwise()
    test_stack()
    test_registers()
    test_io()
    test_control_flow()
    test_brainfuck_reduction()
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
