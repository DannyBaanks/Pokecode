#!/usr/bin/env python3
"""Traductor Brainfuck -> PokéCode.

Los corchetes se traducen con etiquetas del parser. Las etiquetas no son
instrucciones Pokémon ni una variante del código unario Mew: solo entregan al
salto existente un destino de programa sin el límite de ACC de 8 bits.
"""

import sys


MEM_RD, MEM_WR = 'ABRA', 'JYNX'
PTR_INC, PTR_DEC = 'ARBOK', 'GENGAR'
JZ, JNZ = 'CUBONE', 'DODRIO'
INC, DEC = 'MUK', 'ONIX'
IN, OUT_MEM = 'KABUTOPS', 'DITTO'

MATCH_OP = {'>': PTR_INC, '<': PTR_DEC, '.': OUT_MEM, ',': IN}
CELL_PLUS = f'{MEM_RD} {INC} {MEM_WR}'
CELL_MINUS = f'{MEM_RD} {DEC} {MEM_WR}'


def match_brackets(code: str) -> dict[int, int]:
    stack, pairs = [], {}
    for i, ch in enumerate(code):
        if ch == '[':
            stack.append(i)
        elif ch == ']':
            if not stack:
                raise ValueError(f"] sin coincidencia en posicion {i}")
            open_pos = stack.pop()
            pairs[open_pos] = i
            pairs[i] = open_pos
    if stack:
        raise ValueError(f"[ sin cerrar en posicion {stack[-1]}")
    return pairs


def bf_to_pokecode_full(bf_code: str) -> str:
    """Traduce Brainfuck a PokéCode con saltos etiquetados."""
    bf_code = ''.join(c for c in bf_code if c in '><+-.,[]')
    pairs = match_brackets(bf_code)
    out = []
    for i, ch in enumerate(bf_code):
        if ch == '+':
            out.append(CELL_PLUS)
        elif ch == '-':
            out.append(CELL_MINUS)
        elif ch in MATCH_OP:
            out.append(MATCH_OP[ch])
        elif ch == '[':
            out.extend([f'@loop_{i}:', MEM_RD, JZ, f'@end_{pairs[i]}'])
        elif ch == ']':
            out.extend([MEM_RD, JNZ, f'@loop_{pairs[i]}', f'@end_{i}:'])
    return ' '.join(out)


def load_bf_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: py bf2pokecode.py <archivo.bf>")
        sys.exit(1)
    try:
        print(bf_to_pokecode_full(load_bf_file(sys.argv[1])))
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
