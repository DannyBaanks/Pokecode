#!/usr/bin/env python3
"""
Genera 151 .pkmc — uno por opcode — sin confundir Mew ni ops.
Cada archivo es un programa mínimo que ejercita su opcode y termina en DODUO (HALT),
usando etiquetas @solo donde el VM las soporta. Verifica que los 151 pasan.
"""

import os
from pathlib import Path

# Importa tabla real para no inventar nombres
import sys
sys.path.insert(0, ".")
from pokemon_interpreter import OpCode, NAME_TO_OPCODE, parse_pokecode, PokecodeVM

OUT_DIR = Path("pkmc")
OUT_DIR.mkdir(exist_ok=True)

# Descripciones cortas tomadas de pokemon_interpreter.py comentarios
DESCR = {
    1: "MEM_RD  ACC = MEM[PTR]",
    2: "MEM_WR  MEM[PTR] = ACC",
    3: "PTR_INC  PTR += 1",
    4: "PTR_DEC  PTR -= 1",
    5: "PTR_SET  PTR = ACC",
    6: "PTR_GET  ACC = PTR & 0xFF",
    7: "MEM_CPY  MEM[PTR+1] = MEM[PTR]",
    8: "MEM_SWP  swap(MEM[PTR], MEM[PTR+1])",
    9: "MEM_CLR  MEM[PTR] = 0",
    10: "MEM_FILL  for i in 0..ACC: MEM[PTR+i] = ACC",
    11: "MEM_FIND  while MEM[PTR]!=ACC: PTR++ (max 256)",
    12: "MEM_REV  reverse(MEM[PTR..PTR+ACC])",
    13: "PTR_JMP_FWD  PTR += ACC",
    14: "PTR_JMP_BAK  PTR -= ACC",
    15: "PTR_HOME  PTR = 0",
    16: "MEM_PEEK  ACC = MEM[ACC]",
    17: "MEM_POKE  MEM[ACC] = R0",
    18: "MEM_BLOCK  copy 16 bytes PTR..ACC",
    19: "MEM_SNAP  push snapshot MEM[0..31]",
    20: "JMP  PC = ACC (absoluto, con etiqueta)",
    21: "JMP_REL  PC += ACC (signed)",
    22: "JZ  if Z: PC = ACC",
    23: "JNZ  if !Z: PC = ACC",
    24: "JN  if N: PC = ACC",
    25: "JC  if C: PC = ACC",
    26: "JNC  if !C: PC = ACC",
    27: "JV  if V: PC = ACC",
    28: "CALL  push PC+1; PC = ACC",
    29: "RET  PC = pop",
    30: "RETZ  if Z: RET",
    31: "LOOP_BEG  push PC; loop_count = ACC",
    32: "LOOP_END  loop_count-- ; if >0: PC = loop_start",
    33: "BREAK  pop loop_stack",
    34: "CONTINUE  PC = loop_start",
    35: "SWITCH  PC = base + ACC",
    36: "CASE  nop",
    37: "DEFAULT  nop",
    38: "HALT  stop",
    39: "ADD  ACC = ACC + MEM[PTR]",
    40: "SUB  ACC = ACC - MEM[PTR]",
    41: "ADC  ACC = ACC + MEM[PTR] + C",
    42: "SBC  ACC = ACC - MEM[PTR] - C",
    43: "MUL  ACC = ACC * MEM[PTR]",
    44: "DIV  ACC = ACC // MEM[PTR]",
    45: "MOD  ACC = ACC % MEM[PTR]",
    46: "INC  ACC++",
    47: "DEC  ACC--",
    48: "NEG  ACC = -ACC",
    49: "ABS  ACC = abs",
    50: "SIGN  ACC = 1 or 255",
    51: "RAND  ACC = random(0..MEM[PTR])",
    52: "SEED  random.seed(ACC)",
    53: "MAX  ACC = max(ACC, MEM[PTR])",
    54: "MIN  ACC = min(ACC, MEM[PTR])",
    55: "AVG  ACC = (ACC+MEM[PTR])>>1",
    56: "SQRT  ACC = sqrt",
    57: "POW2  ACC = 1 << (ACC &7)",
    58: "AND  ACC &= MEM[PTR]",
    59: "OR  ACC |= MEM[PTR]",
    60: "XOR  ACC ^= MEM[PTR]",
    61: "NOT  ACC = ~ACC",
    62: "SHL  C=bit7; ACC<<=1",
    63: "SHR  C=bit0; ACC>>=1",
    64: "ROL  rotate left through C",
    65: "ROR  rotate right through C",
    66: "SHL_N  ACC << MEM[PTR]",
    67: "SHR_N  ACC >> MEM[PTR]",
    68: "BIT_TST  Z = !(ACC & (1<<MEM[PTR]))",
    69: "BIT_SET  ACC |= (1<<MEM[PTR])",
    70: "BIT_CLR  ACC &= ~(1<<MEM[PTR])",
    71: "BIT_TGL  ACC ^= (1<<MEM[PTR])",
    72: "BIT_CNT  ACC = popcount",
    73: "PARITY  Z = even parity",
    74: "MSB  ACC = highest bit",
    75: "LSB  ACC = lowest bit",
    76: "NOP2",
    77: "PUSH  push ACC",
    78: "POP  ACC = pop",
    79: "DUP  push(top)",
    80: "SWP  swap(top,second)",
    81: "ROT3  rot3",
    82: "OVER  push(second)",
    83: "NIP  remove second",
    84: "TUCK  copy top under second",
    85: "DEPTH  ACC = len(stack)",
    86: "CLEAR_STACK  clear stack",
    87: "STACK_TO_MEM  pop n=ACC to MEM",
    88: "MEM_TO_STACK  push n=ACC from MEM",
    89: "STACK_SNAP  snapshot/restore",
    90: "NOP DRATINI",
    91: "NOP DRAGONAIR",
    92: "NOP DRAGONITE",
    93: "NOP MEWTWO",
    94: "NOP PONYTA",
    95: "NOP RAPIDASH",
    96: "IN  ACC = getchar()",
    97: "OUT  putchar(ACC)",
    98: "OUT_NUM  print ACC",
    99: "OUT_HEX  print hex",
    100: "OUT_BIN  print bin",
    101: "OUT_MEM  print MEM[PTR]",
    102: "DEBUG  print state",
    103: "DUMP_MEM  hex dump",
    104: "DUMP_STACK  print stack",
    105: "DUMP_REGS  print regs",
    106: "READ_NUM  read decimal",
    107: "READ_HEX  read hex",
    108: "READ_LINE  read line to MEM",
    109: "WRITE_FILE  stub",
    110: "READ_FILE  stub",
    111: "SLEEP  sleep ACC ms",
    112: "TIME  ACC = timestamp",
    113: "RNG_BYTE  ACC = random byte",
    114: "HASH  ACC = crc8",
    115: "REG_GET  ACC = R[MEM[PTR]&15]",
    116: "REG_SET  R[MEM[PTR]&15] = ACC",
    117: "REG_XCHG  swap(ACC, R[])",
    118: "REG_INC  R[]++",
    119: "REG_DEC  R[]--",
    120: "REG_ADD  R[] += ACC",
    121: "REG_SUB  R[] -= ACC",
    122: "REG_MOV  R[] = R[ACC&15]",
    123: "REG_CPY  copy R to MEM",
    124: "REG_SWP  swap R[a],R[b]",
    125: "REG_CLR  zero R0..15",
    126: "REG_SAVE  push R",
    127: "REG_REST  pop R",
    128: "REG_ROT  rotate R left by ACC",
    129: "REG_MUL  R[] *= ACC",
    130: "REG_DIV  R[] //= ACC",
    131: "REG_MOD  R[] %= ACC",
    132: "REG_AND  R[] &= ACC",
    133: "REG_OR  R[] |= ACC",
    134: "SYS_EXIT  exit(ACC)",
    135: "SYS_ARG  R0=argc",
    136: "CLONE  fork stub",
    137: "MORPH  stub",
    138: "TRACE_ON  enable trace",
    139: "TRACE_OFF  disable trace",
    140: "PROFILE  R0=cycles",
    141: "SELF_MOD  rewrite program",
    142: "CHECKPOINT  save state slot ACC",
    143: "RESTORE  load state slot ACC",
    144: "TIME_TRAVEL  rewind checkpoint",
    145: "PARALLEL  spawn thread stub",
    146: "ATOMIC_BEG  stub",
    147: "ATOMIC_END  stub",
    148: "FREEZE  stub",
    149: "THAW  stub",
    150: "BURN  secure erase",
    151: "META Mew  NOP+flag",
}

# Mapeo valor->nombre real (minúsculas en NAME_TO_OPCODE, pero queremos UPPER para .pkmc)
VAL_TO_NAME = {int(v): k.upper() for k, v in NAME_TO_OPCODE.items()}
# Asegura Mew mayúscula correcta (NAME_TO_OPCODE tiene 'mew' -> MEW)
VAL_TO_NAME[151] = "Mew"

def body_for(op_val: int, name: str) -> str:
    """Snippet mínimo que ejercita el opcode y termina en HALT sin colgarse."""
    # Control con etiqueta (soporta @ en VM)
    if op_val == 20:  # GOLBAT JMP
        return "GOLBAT @end\n@end DODUO"
    if op_val == 21:  # GRIMER JMP_REL  PC+=ACC
        return "MUK\nGRIMER\nDRATINI\nDODUO"
    if op_val == 22:  # CUBONE JZ  Z true -> salta
        return "EEVEE ABRA\nCUBONE @end\nDRATINI\n@end DODUO"
    if op_val == 23:  # DODRIO JNZ  !Z -> salta
        return "MUK\nDODRIO @end\nDRATINI\n@end DODUO"
    if op_val == 24:  # HORSEA JN  N true -> necesita ACC 128
        return "MUK " * 128 + "\nHORSEA @end\nDRATINI\n@end DODUO"
    if op_val == 25:  # ZAPDOS JC  C true -> SHL con bit7
        return ("MUK " * 128 + "\nKRABBY\nZAPDOS @end\nDRATINI\n@end DODUO")
    if op_val == 26:  # CHANSEY JNC  !C -> C false inicial, salta
        return "CHANSEY @end\nDRATINI\n@end DODUO"
    if op_val == 27:  # DEWGONG JV  V false inicial -> no salta pero termina
        return "DEWGONG @end\nDRATINI\n@end DODUO"
    if op_val == 28:  # DIGLETT CALL
        return "DIGLETT @sub\nDODUO\n@sub DROWZEE"
    if op_val == 29:  # DROWZEE RET (call_stack vacío => halt)
        return "DROWZEE\nDODUO"
    if op_val == 30:  # DUGTRIO RETZ
        return "EEVEE ABRA\nDUGTRIO\nDODUO"
    if op_val == 31:  # FEAROW LOOP_BEG
        # loop 2 veces: ACC=2, luego cuerpo 1x, GASTLY decrementa
        return "MUK MUK\nFEAROW\nMUK\nGASTLY\nDODUO"
    if op_val == 32:  # GASTLY LOOP_END sin loop => nop
        return "GASTLY\nDODUO"
    if op_val == 33:  # FLAREON BREAK
        return "MUK MUK\nFEAROW\nFLAREON\nGASTLY\nDODUO"
    if op_val == 34:  # GEODUDE CONTINUE — smoke sin loop para evitar bucle infinito
        return "GEODUDE\nDODUO"
    if op_val == 35:  # GOLDEEN SWITCH PC=PC+ACC — ACC=0 para caer en DODUO
        return "EEVEE ABRA\nGOLDEEN\nDODUO"
    if op_val == 38:  # DODUO HALT solo
        return "DODUO"
    if op_val == 90:  # DRATINI etc NOPs
        return f"{name}\nDODUO"
    if op_val == 134: # SYS_EXIT -> evita salir del test, usa 0 y captura SystemExit
        return "EEVEE ABRA\nSANDSLASH\nDODUO"
    if op_val == 138: # TRACE_ON
        return "AERODACTYL\nBELLSPROUT\nDODUO"
    if op_val == 142: # CHECKPOINT — solo guarda, sin restaurar inmediato para no buclear
        return "EEVEE ABRA\nCHARMELEON\nDODUO"
    if op_val == 143: # RESTORE — sin checkpoint previo es NOP seguro
        return "ELECTABUZZ\nDODUO"
    if op_val == 144: # TIME_TRAVEL — sin checkpoint previo es NOP seguro
        return "HITMONCHAN\nDODUO"
    if op_val == 150: # BURN — borra estado pero sigue a siguiente instr (PC no se resetea)
        return "MUK\nJYNX\nWIGGLYTUFF\nDODUO"
    # Para resto, opcode solo + HALT es seguro (incluso MEM_RD con 0 etc)
    # Pero algunos necesitan setup para no ser nop silencioso: damos setup mínimo
    if op_val == 2:  # JYNX MEM_WR necesita ACC
        return "MUK\nJYNX\nDODUO"
    if op_val == 5:  # MAGMAR PTR_SET
        return "MUK MUK MUK\nMAGMAR\nDODUO"
    if op_val == 7:  # MEOWTH MEM_CPY necesita MEM[PTR] con dato
        return "MUK\nJYNX\nMEOWTH\nDODUO"
    if op_val == 11: # PINSIR MEM_FIND busca ACC
        return "MUK\nPINSIR\nDODUO"
    if op_val == 39: # IVYSAUR ADD necesita MEM[PTR]
        return "MUK\nJYNX\nEEVEE ABRA\nIVYSAUR\nDODUO"
    if op_val == 58: # KABUTO AND necesita MEM[PTR]
        return "MUK MUK MUK\nJYNX\nEEVEE ABRA\nMUK\nKABUTO\nDODUO"
    if op_val == 77: # GLOOM PUSH
        return "MUK\nGLOOM\nDODUO"
    if op_val == 78: # GOLEM POP
        return "MUK\nGLOOM\nGOLEM\nDODUO"
    if op_val == 115: # PARAS REG_GET necesita MEM[PTR] &15
        return "EEVEE ABRA\nPARAS\nDODUO"
    if op_val == 116: # SEEL REG_SET
        return "MUK\nSEEL\nDODUO"
    if op_val == 151: # Mew
        return "Mew\nDODUO"
    # default
    return f"{name}\nDODUO"

def gen():
    count = 0
    failed = []
    for val in range(1, 152):
        name = VAL_TO_NAME.get(val)
        if not name:
            # gap? no, 1-151 todos tienen nombre
            continue
        body = body_for(val, name)
        fname = f"{val:03d}_{name}.pkmc"
        path = OUT_DIR / fname
        content = f"# {val:03d} {name} — {DESCR.get(val, '')}\n# Opcode {val}\n{body}\n"
        path.write_text(content, encoding="utf-8")
        count += 1
        # verifica parse + run
        try:
            prog = parse_pokecode(content)
            vm = PokecodeVM(prog)
            vm.run(max_cycles=20000)
        except SystemExit:
            # SYS_EXIT etc es esperado, considera PASS si sale con código
            pass
        except Exception as e:
            failed.append((fname, str(e)))
    print(f"Generados {count} .pkmc en {OUT_DIR}/")
    if failed:
        print("FALLOS:")
        for f, e in failed:
            print(f"  {f}: {e}")
        raise SystemExit(1)
    else:
        print("Todos los 151 programas parsean y terminan (o SystemExit esperado).")

    # Verificación adicional: host.py debe poder ejecutarlos
    # Probar 3 al azar vía host
    import subprocess
    for sample in ["001_ABRA.pkmc", "046_MUK.pkmc", "151_Mew.pkmc"]:
        p = OUT_DIR / sample
        result = subprocess.run([sys.executable, "host.py", str(p)], capture_output=True, text=True)
        if result.returncode not in (0,):
            print(f"host.py fallo en {sample}: {result.stderr[:200]}")
            failed.append((sample, result.stderr))
    if not failed:
        print("host.py verifica 3 muestras OK")

if __name__ == "__main__":
    gen()
