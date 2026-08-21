#!/usr/bin/env python3
"""
Traductor Brainfuck -> PokeCode.

EL BUG QUE TENIA Y POR QUE
--------------------------
La version anterior codificaba el destino de salto en UNARIO: `MUK` repetido t
veces. Eso hace que el tamano del bloque `[` dependa de su propio destino, y el
destino depende de todos los tamanos. La iteracion de punto fijo nunca
converge; medido sobre `+[-].`, el destino crecia 29 por vuelta:

    iteracion 1 -> 26      iteracion 5 -> 142
    iteracion 2 -> 55      iteracion 6 -> 171
    iteracion 3 -> 84      ...
    iteracion 4 -> 113     tras 200 vueltas -> 165 (envuelto mod 256)

El programa saltaba a la instruccion 165, que es basura, y se colgaba. `+[-].`
-- el bucle terminante mas pequeno que existe -- no paraba ni en 20 millones de
ciclos.

EL ARREGLO
----------
El destino se construye en BINARIO con tamano FIJO: ocho parejas de
(KRABBY, MUK|GOLDUCK), es decir 8 duplicaciones y 8 sumas-o-nada. Son
exactamente 16 instrucciones para cualquier valor de 0..255, asi que el bloque
mide siempre 20 y el punto fijo converge en una sola pasada.

    GOLDUCK y HAUNTER son no-ops reales (CASE / DEFAULT, marcadores de switch);
    verificado empiricamente: no tocan ACC ni los flags.

LIMITE ARQUITECTONICO (no es un bug, no se puede arreglar aqui)
---------------------------------------------------------------
Todos los saltos de PokeCode pasan por ACC, que es de 8 bits:

    CUBONE (JZ)  / DODRIO (JNZ) : PC = ACC      -> destino maximo 255
    GRIMER (JMP_REL)            : PC += ACC     -> alcance +-127

Por tanto un programa traducido que pase de 256 instrucciones NO puede saltar a
su propia cola. Cada `[` o `]` cuesta 20, asi que el limite practico son ~12
corchetes. Programas mas grandes (Hello World de BF, por ejemplo) quedan fuera
del alcance de esta arquitectura, no de este traductor.

El traductor lo detecta y lo dice, en vez de emitir algo que se cuelga.
"""

import sys

# nombres actuales tras la permutacion; verificados contra NAME_TO_OPCODE
MEM_RD, MEM_WR = 'ABRA', 'JYNX'
PTR_INC, PTR_DEC = 'ARBOK', 'GENGAR'
MEM_CLR = 'EEVEE'
JZ, JNZ = 'CUBONE', 'DODRIO'
INC, DEC = 'MUK', 'ONIX'
PUSH, POP = 'GLOOM', 'GOLEM'
IN, OUT_MEM = 'KABUTOPS', 'DITTO'
REG_GET, REG_SET = 'PARAS', 'SEEL'
SHL = 'KRABBY'
NOP = 'GOLDUCK'

MATCH_OP = {'>': PTR_INC, '<': PTR_DEC, '.': OUT_MEM, ',': IN}
CELL_PLUS = f'{MEM_RD} {INC} {MEM_WR}'     # MEM[PTR]++
CELL_MINUS = f'{MEM_RD} {DEC} {MEM_WR}'    # MEM[PTR]--

#: Tamano de un bloque [ o ]. CONSTANTE: de eso depende que converja.
BLOQUE = 20
#: Los saltos van por ACC (8 bits). Mas alla de esto no se puede saltar.
MAX_PC = 255


def match_brackets(code: str) -> dict:
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


def set_acc_const(value: int) -> list:
    """ACC = value en EXACTAMENTE 16 instrucciones, sea cual sea el valor.

    Construccion binaria de MSB a LSB: duplicar y sumar el bit. El `NOP` en las
    posiciones de bit cero es lo que mantiene el tamano fijo, y el tamano fijo
    es lo que hace converger la resolucion de destinos.
    """
    value &= 0xFF
    seq = []
    for i in range(7, -1, -1):
        seq.append(SHL)
        seq.append(INC if (value >> i) & 1 else NOP)
    return seq


def _bloque_salto(target: int, salto: str) -> list:
    """Emite un `[` o `]` completo. Siempre BLOQUE instrucciones.

    LA CELDA NO SE TOCA. La version anterior la guardaba en un registro con
    REG_SET y la restauraba con REG_GET, y ahi estaba el fallo de raiz:

        SEEL (REG_SET) escribe en R[MEM[PTR] & 15]
        PARAS (REG_GET) lee    de R[MEM[PTR] & 15]

    El indice del registro sale del VALOR de la celda. Se guardaba en R[5] y se
    restauraba desde R[0], asi que la celda volvia como 0 y el bucle no corria.
    Solo funcionaba cuando la celda era 0 o multiplo de 16 -- por eso `+[-].`
    pasaba y `+++++[>+<-]>.` no.

    Nada de eso hace falta: los ocho SHL de `set_acc_const` ya vacian ACC por su
    cuenta (ocho desplazamientos de un valor de 8 bits dan 0), asi que el
    destino se construye sin leer ni escribir memoria.

        16  ACC = destino          (auto-limpiante, no toca memoria)
         1  apila el destino
         1  ACC = celda            -> Z sale de la CELDA
         1  ACC = destino (POP)    -> POP no toca Z, verificado
         1  salta si procede
    """
    seq = set_acc_const(target)                   # 16
    seq += [PUSH, MEM_RD, POP, salto]             # 4
    assert len(seq) == BLOQUE, len(seq)
    return seq


def _indices(bf_code: str) -> tuple:
    """Posicion de cada operador BF en el programa PokeCode. Una sola pasada.

    Ya no hace falta iterar a punto fijo: ningun tamano depende de un destino.
    """
    start, pos = {}, 0
    for i, ch in enumerate(bf_code):
        start[i] = pos
        if ch in '+-':
            pos += 3
        elif ch in '><.,':
            pos += 1
        elif ch in '[]':
            pos += BLOQUE
    return start, pos


def bf_to_pokecode_full(bf_code: str) -> str:
    """Traduce Brainfuck a PokeCode. Lanza ValueError si excede la maquina."""
    bf_code = ''.join(c for c in bf_code if c in '><+-.,[]')
    pairs = match_brackets(bf_code)
    start, total = _indices(bf_code)

    if total > MAX_PC:
        corchetes = sum(1 for c in bf_code if c in '[]')
        raise ValueError(
            f"la traduccion ocupa {total} instrucciones y los saltos de "
            f"PokeCode solo alcanzan {MAX_PC} (PC = ACC, 8 bits). "
            f"Este programa usa {corchetes} corchetes a {BLOQUE} cada uno. "
            f"No es una limitacion del traductor sino de la maquina.")

    out = []
    for i, ch in enumerate(bf_code):
        if ch == '+':
            out.append(CELL_PLUS)
        elif ch == '-':
            out.append(CELL_MINUS)
        elif ch in MATCH_OP:
            out.append(MATCH_OP[ch])
        elif ch == '[':
            # si la celda es 0, saltar PASADO el ] correspondiente
            out.extend(_bloque_salto(start[pairs[i]] + BLOQUE, JZ))
        elif ch == ']':
            # si la celda NO es 0, volver al [ correspondiente (re-testea)
            out.extend(_bloque_salto(start[pairs[i]], JNZ))
    return ' '.join(out)


def load_bf_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python bf2pokecode.py <archivo.bf>")
        sys.exit(1)
    try:
        print(bf_to_pokecode_full(load_bf_file(sys.argv[1])))
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
