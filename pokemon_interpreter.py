#!/usr/bin/env python3
"""
POKECODE — Esolang Educativo basado en los 151 Pokémon Gen 1
Cada Pokémon = una instrucción atómica con semántica precisa.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional
import sys
import random
import time


# ═══════════════════════════════════════════════════════════════════════
# INSTRUCTION SET — 151 Pokémon Gen 1
# ═══════════════════════════════════════════════════════════════════════

class OpCode(IntEnum):
    # ─── FAMILIA 1: MEMORIA (1-19) ───
    ABRA        = 1   # MEM_RD      : ACC = MEM[PTR]
    JYNX        = 2   # MEM_WR      : MEM[PTR] = ACC
    ARBOK       = 3   # PTR_INC     : PTR += 1
    GENGAR      = 4   # PTR_DEC     : PTR -= 1
    MAGMAR      = 5   # PTR_SET     : PTR = ACC
    MANKEY      = 6   # PTR_GET     : ACC = PTR & 0xFF
    MEOWTH      = 7   # MEM_CPY     : MEM[PTR+1] = MEM[PTR]
    ODDISH      = 8   # MEM_SWP     : swap(MEM[PTR], MEM[PTR+1])
    EEVEE       = 9   # MEM_CLR     : MEM[PTR] = 0
    PIDGEY      = 10  # MEM_FILL    : for i in 0..ACC: MEM[PTR+i] = ACC
    PINSIR      = 11  # MEM_FIND    : while MEM[PTR]!=ACC: PTR++ (max 256)
    RAICHU      = 12  # MEM_REV     : reverse(MEM[PTR..PTR+ACC])
    RHYDON      = 13  # PTR_JMP_FWD : PTR += ACC
    SEADRA      = 14  # PTR_JMP_BAK : PTR -= ACC
    ZUBAT       = 15  # PTR_HOME    : PTR = 0
    STARYU      = 16  # MEM_PEEK    : ACC = MEM[ACC] (indirect)
    TAUROS      = 17  # MEM_POKE    : MEM[ACC] = R0
    VULPIX      = 18  # MEM_BLOCK   : copy 16 bytes PTR..PTR+15 to ACC..ACC+15
    WEEDLE      = 19  # MEM_SNAP    : push snapshot of MEM[0..31] to stack

    # ─── FAMILIA 2: CONTROL (20-38) ───
    GOLBAT      = 20  # JMP         : PC = ACC (absoluto)
    GRIMER      = 21  # JMP_REL     : PC += ACC (signed -128..127)
    CUBONE      = 22  # JZ          : if Z: PC = ACC
    DODRIO      = 23  # JNZ         : if !Z: PC = ACC
    HORSEA      = 24  # JN          : if N: PC = ACC
    ZAPDOS      = 25  # JC          : if C: PC = ACC
    CHANSEY     = 26  # JNC         : if !C: PC = ACC
    DEWGONG     = 27  # JV          : if V: PC = ACC
    DIGLETT     = 28  # CALL        : push PC+1; PC = ACC
    DROWZEE     = 29  # RET         : PC = pop call_stack
    DUGTRIO     = 30  # RETZ        : if Z: RET
    FEAROW      = 31  # LOOP_BEG    : push PC; loop_count = ACC
    GASTLY      = 32  # LOOP_END    : loop_count--; if >0: PC = loop_start else pop
    FLAREON     = 33  # BREAK       : pop loop_stack; PC = after LOOP_END
    GEODUDE     = 34  # CONTINUE    : PC = loop_start
    GOLDEEN     = 35  # SWITCH      : PC = base + ACC (jump table)
    GOLDUCK     = 36  # CASE        : no-op (marker)
    HAUNTER     = 37  # DEFAULT     : no-op (marker)
    DODUO       = 38  # HALT        : stop execution

    # ─── FAMILIA 3: ARITMÉTICA (39-57) ───
    IVYSAUR     = 39  # ADD         : ACC = ACC + MEM[PTR]
    JOLTEON     = 40  # SUB         : ACC = ACC - MEM[PTR]
    KADABRA     = 41  # ADC         : ACC = ACC + MEM[PTR] + C
    KINGLER     = 42  # SBC         : ACC = ACC - MEM[PTR] - C
    KOFFING     = 43  # MUL         : ACC = (ACC * MEM[PTR]) & 0xFF
    MACHAMP     = 44  # DIV         : ACC = ACC // MEM[PTR] (div0=0, C=1)
    MACHOKE     = 45  # MOD         : ACC = ACC % MEM[PTR] (div0=0)
    MUK         = 46  # INC         : ACC = (ACC + 1) & 0xFF
    ONIX        = 47  # DEC         : ACC = (ACC - 1) & 0xFF
    EKANS       = 48  # NEG         : ACC = (-ACC) & 0xFF
    MAROWAK     = 49  # ABS         : ACC = abs(ACC) if ACC<128 else 256-ACC
    METAPOD     = 50  # SIGN        : ACC = 1 if ACC<128 else 255
    MOLTRES     = 51  # RAND        : ACC = random(0..MEM[PTR])
    MR_MIME     = 52  # SEED        : random.seed(ACC)
    OMANYTE     = 53  # MAX         : ACC = max(ACC, MEM[PTR])
    OMASTAR     = 54  # MIN         : ACC = min(ACC, MEM[PTR])
    PERSIAN     = 55  # AVG         : ACC = (ACC + MEM[PTR]) >> 1
    PIDGEOT     = 56  # SQRT        : ACC = int(sqrt(ACC))
    PIKACHU     = 57  # POW2        : ACC = 1 << (ACC & 7)

    # ─── FAMILIA 4: LÓGICA BITWISE (58-76) ───
    KABUTO      = 58  # AND         : ACC &= MEM[PTR]
    POLIWAG     = 59  # OR          : ACC |= MEM[PTR]
    KAKUNA      = 60  # XOR         : ACC ^= MEM[PTR]
    PORYGON     = 61  # NOT         : ACC = ~ACC & 0xFF
    KRABBY      = 62  # SHL         : C=bit7; ACC=(ACC<<1)&0xFF
    LAPRAS      = 63  # SHR         : C=bit0; ACC>>=1
    PSYDUCK     = 64  # ROL         : rotate left through carry
    RATTATA     = 65  # ROR         : rotate right through carry
    RHYHORN     = 66  # SHL_N       : ACC = (ACC << MEM[PTR]) & 0xFF
    SCYTHER     = 67  # SHR_N       : ACC >>= MEM[PTR]
    SEAKING     = 68  # BIT_TST     : Z = !(ACC & (1<<MEM[PTR]))
    SLOWBRO     = 69  # BIT_SET     : ACC |= (1<<MEM[PTR])
    SNORLAX     = 70  # BIT_CLR     : ACC &= ~(1<<MEM[PTR])
    SPEAROW     = 71  # BIT_TGL     : ACC ^= (1<<MEM[PTR])
    STARMIE     = 72  # BIT_CNT     : ACC = popcount(ACC)
    TANGELA     = 73  # PARITY      : Z = even_parity(ACC)
    VENONAT     = 74  # MSB         : ACC = highest_set_bit(ACC)
    VOLTORB     = 75  # LSB         : ACC = lowest_set_bit(ACC)
    RATICATE    = 76  # NOP2        : no-op (second nop after MEW)

    # ─── FAMILIA 5: PILA (77-95) ───
    GLOOM       = 77  # PUSH        : push ACC
    GOLEM       = 78  # POP         : ACC = pop() or 0
    WEEZING     = 79  # DUP         : push(top)
    ALAKAZAM    = 80  # SWP         : swap(top, second)
    ARCANINE    = 81  # ROT3        : rot3(top, second, third)
    ARTICUNO    = 82  # OVER        : push(second)
    BEEDRILL    = 83  # NIP         : remove second
    CATERPIE    = 84  # TUCK        : copy top under second
    CLEFABLE    = 85  # DEPTH       : ACC = len(stack)
    CLEFAIRY    = 86  # CLEAR_STACK : clear stack
    CLOYSTER    = 87  # STACK_TO_MEM: pop n=ACC bytes to MEM[PTR..]
    GRAVELER    = 88  # MEM_TO_STACK: push n=ACC bytes from MEM[PTR..]
    GYARADOS    = 89  # STACK_SNAP  : snapshot/restore stack

    # ─── GAPS 90-95: POKEMONS GEN 1 FALTANTES ───
    DRATINI     = 90  # DRAGON1     : no-op
    DRAGONAIR   = 91  # DRAGON2     : no-op
    DRAGONITE   = 92  # DRAGON3     : no-op
    MEWTWO      = 93  # MEWTWO      : no-op
    PONYTA      = 94  # PONYTA      : no-op
    RAPIDASH    = 95  # RAPIDASH    : no-op

    # ─── FAMILIA 6: I/O (96-114) ───
    KABUTOPS    = 96  # IN          : ACC = getchar() or 0
    HYPNO       = 97  # OUT         : putchar(ACC)
    MAGIKARP    = 98  # OUT_NUM     : print ACC as decimal
    MAGNETON    = 99  # OUT_HEX     : print ACC as 2-digit hex
    NIDOKING    = 100 # OUT_BIN     : print ACC as 8-bit binary
    DITTO       = 101 # OUT_MEM     : print MEM[PTR] as char
    NIDORINA    = 102 # DEBUG       : print state
    NIDORINO    = 103 # DUMP_MEM    : hex dump MEM[0..255]
    PARASECT    = 104 # DUMP_STACK  : print stack top 16
    PRIMEAPE    = 105 # DUMP_REGS   : print R0-R15
    SHELLDER    = 106 # READ_NUM    : read decimal → ACC
    SLOWPOKE    = 107 # READ_HEX    : read 2-char hex → ACC
    SQUIRTLE    = 108 # READ_LINE   : read line to MEM[PTR..]
    VAPOREON    = 109 # WRITE_FILE  : syscall write
    VENOMOTH    = 110 # READ_FILE   : syscall read
    VENUSAUR    = 111 # SLEEP       : sleep ACC ms
    BLASTOISE   = 112 # TIME        : ACC = timestamp_low_byte
    BULBASAUR   = 113 # RNG_BYTE    : ACC = random byte
    CHARIZARD   = 114 # HASH        : ACC = crc8(MEM[PTR..PTR+15])

    # ─── FAMILIA 7: REGISTROS (115-133) ───
    PARAS       = 115 # REG_GET     : ACC = R[MEM[PTR]&15]
    SEEL        = 116 # REG_SET     : R[MEM[PTR]&15] = ACC
    ELECTRODE   = 117 # REG_XCHG    : swap(ACC, R[MEM[PTR]&15])
    MACHOP      = 118 # REG_INC     : R[MEM[PTR]&15]++
    EXEGGCUTE   = 119 # REG_DEC     : R[MEM[PTR]&15]--
    EXEGGUTOR   = 120 # REG_ADD     : R[MEM[PTR]&15] += ACC
    FARFETCHD   = 121 # REG_SUB     : R[MEM[PTR]&15] -= ACC
    GROWLITHE   = 122 # REG_MOV     : R[MEM[PTR]&15] = R[ACC&15]
    HITMONLEE   = 123 # REG_CPY     : copy R0..R15 to MEM[PTR..PTR+15]
    LICKITUNG   = 124 # REG_SWP     : swap R[MEM[PTR]&15], R[ACC&15]
    MAGNEMITE   = 125 # REG_CLR     : zero R0..R15
    NIDOQUEEN   = 126 # REG_SAVE    : push all R0..R15 to stack
    NIDORAN_F   = 127 # REG_REST    : pop all R0..R15 from stack
    NIDORAN_M   = 128 # REG_ROT     : rotate R0..R15 left by ACC
    NINETALES   = 129 # REG_MUL     : R[MEM[PTR]&15] *= ACC
    PIDGEOTTO   = 130 # REG_DIV     : R[MEM[PTR]&15] //= ACC
    POLIWHIRL   = 131 # REG_MOD     : R[MEM[PTR]&15] %= ACC
    POLIWRATH   = 132 # REG_AND     : R[MEM[PTR]&15] &= ACC
    SANDSHREW   = 133 # REG_OR      : R[MEM[PTR]&15] |= ACC

    # ─── FAMILIA 8: META (134-151) ───
    SANDSLASH   = 134 # SYS_EXIT    : exit(ACC)
    TENTACOOL   = 135 # SYS_ARG     : R0=argc; R1..=argv
    VILEPLUME   = 136 # CLONE       : fork copy
    WARTORTLE   = 137 # MORPH       : change instruction set
    AERODACTYL  = 138 # TRACE_ON    : enable tracing
    BELLSPROUT  = 139 # TRACE_OFF   : disable tracing
    BUTTERFREE  = 140 # PROFILE     : R0=cycles; R1=reads; R2=writes
    CHARMANDER  = 141 # SELF_MOD    : rewrite instruction at PC+ACC to R0
    CHARMELEON  = 142 # CHECKPOINT  : save state to slot ACC (0-7)
    ELECTABUZZ  = 143 # RESTORE     : load state from slot ACC
    HITMONCHAN  = 144 # TIME_TRAVEL : rewind to checkpoint ACC
    JIGGLYPUFF  = 145 # PARALLEL    : spawn thread at PC=ACC
    KANGASKHAN  = 146 # ATOMIC_BEG  : disable interrupts
    TENTACRUEL  = 147 # ATOMIC_END  : re-enable
    VICTREEBEL  = 148 # FREEZE      : pause other threads
    WEEPINBELL  = 149 # THAW        : resume threads
    WIGGLYTUFF  = 150 # BURN        : secure erase all

    # ─── ESPECIAL ───
    MEW         = 151 # META        : NOP + flag "Mew encountered"



# ════════════════════════════════════════════════════════════════════════
# NAME ↔ OPCODE MAPPING
# ════════════════════════════════════════════════════════════════════════

NAME_TO_OPCODE = {
    'abra': OpCode.ABRA,
    'jynx': OpCode.JYNX,
    'arbok': OpCode.ARBOK,
    'gengar': OpCode.GENGAR,
    'magmar': OpCode.MAGMAR,
    'mankey': OpCode.MANKEY,
    'meowth': OpCode.MEOWTH,
    'oddish': OpCode.ODDISH,
    'eevee': OpCode.EEVEE,
    'pidgey': OpCode.PIDGEY,
    'pinsir': OpCode.PINSIR,
    'raichu': OpCode.RAICHU,
    'rhydon': OpCode.RHYDON,
    'seadra': OpCode.SEADRA,
    'zubat': OpCode.ZUBAT,
    'staryu': OpCode.STARYU,
    'tauros': OpCode.TAUROS,
    'vulpix': OpCode.VULPIX,
    'weedle': OpCode.WEEDLE,
    'golbat': OpCode.GOLBAT,
    'grimer': OpCode.GRIMER,
    'cubone': OpCode.CUBONE,
    'dodrio': OpCode.DODRIO,
    'horsea': OpCode.HORSEA,
    'zapdos': OpCode.ZAPDOS,
    'chansey': OpCode.CHANSEY,
    'dewgong': OpCode.DEWGONG,
    'diglett': OpCode.DIGLETT,
    'drowzee': OpCode.DROWZEE,
    'dugtrio': OpCode.DUGTRIO,
    'fearow': OpCode.FEAROW,
    'gastly': OpCode.GASTLY,
    'flareon': OpCode.FLAREON,
    'geodude': OpCode.GEODUDE,
    'goldeen': OpCode.GOLDEEN,
    'golduck': OpCode.GOLDUCK,
    'haunter': OpCode.HAUNTER,
    'doduo': OpCode.DODUO,
    'ivysaur': OpCode.IVYSAUR,
    'jolteon': OpCode.JOLTEON,
    'kadabra': OpCode.KADABRA,
    'kingler': OpCode.KINGLER,
    'koffing': OpCode.KOFFING,
    'machamp': OpCode.MACHAMP,
    'machoke': OpCode.MACHOKE,
    'muk': OpCode.MUK,
    'onix': OpCode.ONIX,
    'ekans': OpCode.EKANS,
    'marowak': OpCode.MAROWAK,
    'metapod': OpCode.METAPOD,
    'moltres': OpCode.MOLTRES,
    'mr_mime': OpCode.MR_MIME,
    'omanyte': OpCode.OMANYTE,
    'omastar': OpCode.OMASTAR,
    'persian': OpCode.PERSIAN,
    'pidgeot': OpCode.PIDGEOT,
    'pikachu': OpCode.PIKACHU,
    'ponyta': OpCode.PONYTA,
    'rapidash': OpCode.RAPIDASH,
    'kabuto': OpCode.KABUTO,
    'poliwag': OpCode.POLIWAG,
    'kakuna': OpCode.KAKUNA,
    'porygon': OpCode.PORYGON,
    'raticate': OpCode.RATICATE,
    'dratini': OpCode.DRATINI,
    'dragonair': OpCode.DRAGONAIR,
    'dragonite': OpCode.DRAGONITE,
    'mewtwo': OpCode.MEWTWO,
    'krabby': OpCode.KRABBY,
    'lapras': OpCode.LAPRAS,
    'psyduck': OpCode.PSYDUCK,
    'rattata': OpCode.RATTATA,
    'rhyhorn': OpCode.RHYHORN,
    'scyther': OpCode.SCYTHER,
    'seaking': OpCode.SEAKING,
    'slowbro': OpCode.SLOWBRO,
    'snorlax': OpCode.SNORLAX,
    'spearow': OpCode.SPEAROW,
    'starmie': OpCode.STARMIE,
    'tangela': OpCode.TANGELA,
    'venonat': OpCode.VENONAT,
    'voltorb': OpCode.VOLTORB,
    'gloom': OpCode.GLOOM,
    'golem': OpCode.GOLEM,
    'weezing': OpCode.WEEZING,
    'alakazam': OpCode.ALAKAZAM,
    'arcanine': OpCode.ARCANINE,
    'articuno': OpCode.ARTICUNO,
    'beedrill': OpCode.BEEDRILL,
    'caterpie': OpCode.CATERPIE,
    'clefable': OpCode.CLEFABLE,
    'clefairy': OpCode.CLEFAIRY,
    'cloyster': OpCode.CLOYSTER,
    'graveler': OpCode.GRAVELER,
    'gyarados': OpCode.GYARADOS,
    'kabutops': OpCode.KABUTOPS,
    'hypno': OpCode.HYPNO,
    'magikarp': OpCode.MAGIKARP,
    'magneton': OpCode.MAGNETON,
    'nidoking': OpCode.NIDOKING,
    'ditto': OpCode.DITTO,
    'nidorina': OpCode.NIDORINA,
    'nidorino': OpCode.NIDORINO,
    'parasect': OpCode.PARASECT,
    'primeape': OpCode.PRIMEAPE,
    'shellder': OpCode.SHELLDER,
    'slowpoke': OpCode.SLOWPOKE,
    'squirtle': OpCode.SQUIRTLE,
    'vaporeon': OpCode.VAPOREON,
    'venomoth': OpCode.VENOMOTH,
    'venusaur': OpCode.VENUSAUR,
    'blastoise': OpCode.BLASTOISE,
    'bulbasaur': OpCode.BULBASAUR,
    'charizard': OpCode.CHARIZARD,
    'paras': OpCode.PARAS,
    'seel': OpCode.SEEL,
    'electrode': OpCode.ELECTRODE,
    'machop': OpCode.MACHOP,
    'exeggcute': OpCode.EXEGGCUTE,
    'exeggutor': OpCode.EXEGGUTOR,
    'farfetchd': OpCode.FARFETCHD,
    'growlithe': OpCode.GROWLITHE,
    'hitmonlee': OpCode.HITMONLEE,
    'lickitung': OpCode.LICKITUNG,
    'magnemite': OpCode.MAGNEMITE,
    'nidoqueen': OpCode.NIDOQUEEN,
    'nidoran_f': OpCode.NIDORAN_F,
    'nidoran_m': OpCode.NIDORAN_M,
    'ninetales': OpCode.NINETALES,
    'pidgeotto': OpCode.PIDGEOTTO,
    'poliwhirl': OpCode.POLIWHIRL,
    'poliwrath': OpCode.POLIWRATH,
    'sandshrew': OpCode.SANDSHREW,
    'sandslash': OpCode.SANDSLASH,
    'tentacool': OpCode.TENTACOOL,
    'vileplume': OpCode.VILEPLUME,
    'wartortle': OpCode.WARTORTLE,
    'aerodactyl': OpCode.AERODACTYL,
    'bellsprout': OpCode.BELLSPROUT,
    'butterfree': OpCode.BUTTERFREE,
    'charmander': OpCode.CHARMANDER,
    'charmeleon': OpCode.CHARMELEON,
    'electabuzz': OpCode.ELECTABUZZ,
    'hitmonchan': OpCode.HITMONCHAN,
    'jigglypuff': OpCode.JIGGLYPUFF,
    'kangaskhan': OpCode.KANGASKHAN,
    'tentacruel': OpCode.TENTACRUEL,
    'victreebel': OpCode.VICTREEBEL,
    'weepinbell': OpCode.WEEPINBELL,
    'wigglytuff': OpCode.WIGGLYTUFF,
    'mew': OpCode.MEW,
}


# ════════════════════════════════════════════════════════════════════════
# POKECODE VM
# ════════════════════════════════════════════════════════════════════════

# DISPATCH TABLE (built at module level)
# ═════════════════════════════════════════════════════════════════════

_DISPATCH_TABLE: dict[OpCode, Callable] = {
    OpCode.ABRA      : lambda self: self.exec_bulbasaur(),
    OpCode.JYNX      : lambda self: self.exec_ivysaur(),
    OpCode.ARBOK     : lambda self: self.exec_venusaur(),
    OpCode.GENGAR    : lambda self: self.exec_charmander(),
    OpCode.MAGMAR    : lambda self: self.exec_charmeleon(),
    OpCode.MANKEY    : lambda self: self.exec_charizard(),
    OpCode.MEOWTH    : lambda self: self.exec_squirtle(),
    OpCode.ODDISH    : lambda self: self.exec_wartortle(),
    OpCode.EEVEE     : lambda self: self.exec_blastoise(),
    OpCode.PIDGEY    : lambda self: self.exec_caterpie(),
    OpCode.PINSIR    : lambda self: self.exec_metapod(),
    OpCode.RAICHU    : lambda self: self.exec_butterfree(),
    OpCode.RHYDON    : lambda self: self.exec_weedle(),
    OpCode.SEADRA    : lambda self: self.exec_kakuna(),
    OpCode.ZUBAT     : lambda self: self.exec_beedrill(),
    OpCode.STARYU    : lambda self: self.exec_pidgey(),
    OpCode.TAUROS    : lambda self: self.exec_pidgeotto(),
    OpCode.VULPIX    : lambda self: self.exec_pidgeot(),
    OpCode.WEEDLE    : lambda self: self.exec_rattata(),
    OpCode.GOLBAT    : lambda self: self.exec_spearow(),
    OpCode.GRIMER    : lambda self: self.exec_fearow(),
    OpCode.CUBONE    : lambda self: self.exec_ekans(),
    OpCode.DODRIO    : lambda self: self.exec_arbok(),
    OpCode.HORSEA    : lambda self: self.exec_pikachu(),
    OpCode.ZAPDOS    : lambda self: self.exec_raichu(),
    OpCode.CHANSEY   : lambda self: self.exec_sandshrew(),
    OpCode.DEWGONG   : lambda self: self.exec_sandslash(),
    OpCode.DIGLETT   : lambda self: self.exec_nidoran_f(),
    OpCode.DROWZEE   : lambda self: self.exec_nidorina(),
    OpCode.DUGTRIO   : lambda self: self.exec_nidoqueen(),
    OpCode.FEAROW    : lambda self: self.exec_nidoran_m(),
    OpCode.GASTLY    : lambda self: self.exec_nidorino(),
    OpCode.FLAREON   : lambda self: self.exec_nidoking(),
    OpCode.GEODUDE   : lambda self: self.exec_clefairy(),
    OpCode.GOLDEEN   : lambda self: self.exec_clefable(),
    OpCode.GOLDUCK   : lambda self: self.exec_vulpix(),
    OpCode.HAUNTER   : lambda self: self.exec_ninetales(),
    OpCode.DODUO     : lambda self: self.exec_jigglypuff(),
    OpCode.IVYSAUR   : lambda self: self.exec_wigglytuff(),
    OpCode.JOLTEON   : lambda self: self.exec_zubat(),
    OpCode.KADABRA   : lambda self: self.exec_golbat(),
    OpCode.KINGLER   : lambda self: self.exec_oddish(),
    OpCode.KOFFING   : lambda self: self.exec_gloom(),
    OpCode.MACHAMP   : lambda self: self.exec_vileplume(),
    OpCode.MACHOKE   : lambda self: self.exec_paras(),
    OpCode.MUK       : lambda self: self.exec_parasect(),
    OpCode.ONIX      : lambda self: self.exec_venonat(),
    OpCode.EKANS     : lambda self: self.exec_venomoth(),
    OpCode.MAROWAK   : lambda self: self.exec_diglett(),
    OpCode.METAPOD   : lambda self: self.exec_dugtrio(),
    OpCode.MOLTRES   : lambda self: self.exec_meowth(),
    OpCode.MR_MIME   : lambda self: self.exec_persian(),
    OpCode.OMANYTE   : lambda self: self.exec_psyduck(),
    OpCode.OMASTAR   : lambda self: self.exec_golduck(),
    OpCode.PERSIAN   : lambda self: self.exec_mankey(),
    OpCode.PIDGEOT   : lambda self: self.exec_primeape(),
    OpCode.PIKACHU   : lambda self: self.exec_growlithe(),
    OpCode.KABUTO    : lambda self: self.exec_arcanine(),
    OpCode.POLIWAG   : lambda self: self.exec_poliwag(),
    OpCode.KAKUNA    : lambda self: self.exec_poliwhirl(),
    OpCode.PORYGON   : lambda self: self.exec_poliwrath(),
    OpCode.KRABBY    : lambda self: self.exec_abra(),
    OpCode.LAPRAS    : lambda self: self.exec_kadabra(),
    OpCode.PSYDUCK   : lambda self: self.exec_alakazam(),
    OpCode.RATTATA   : lambda self: self.exec_machop(),
    OpCode.RHYHORN   : lambda self: self.exec_machoke(),
    OpCode.SCYTHER   : lambda self: self.exec_machamp(),
    OpCode.SEAKING   : lambda self: self.exec_bellsprout(),
    OpCode.SLOWBRO   : lambda self: self.exec_weepinbell(),
    OpCode.SNORLAX   : lambda self: self.exec_victreebel(),
    OpCode.SPEAROW   : lambda self: self.exec_tentacool(),
    OpCode.STARMIE   : lambda self: self.exec_tentacruel(),
    OpCode.TANGELA   : lambda self: self.exec_geodude(),
    OpCode.VENONAT   : lambda self: self.exec_graveler(),
    OpCode.VOLTORB   : lambda self: self.exec_golem(),
    OpCode.RATICATE  : lambda self: self.exec_raticate(),
    OpCode.GLOOM     : lambda self: self.exec_slowpoke(),
    OpCode.GOLEM     : lambda self: self.exec_slowbro(),
    OpCode.WEEZING   : lambda self: self.exec_magnemite(),
    OpCode.ALAKAZAM  : lambda self: self.exec_magneton(),
    OpCode.ARCANINE  : lambda self: self.exec_farfetchd(),
    OpCode.ARTICUNO  : lambda self: self.exec_doduo(),
    OpCode.BEEDRILL  : lambda self: self.exec_dodrio(),
    OpCode.CATERPIE  : lambda self: self.exec_seel(),
    OpCode.CLEFABLE  : lambda self: self.exec_dewgong(),
    OpCode.CLEFAIRY  : lambda self: self.exec_grimer(),
    OpCode.CLOYSTER  : lambda self: self.exec_muk(),
    OpCode.GRAVELER  : lambda self: self.exec_shellder(),
    OpCode.GYARADOS  : lambda self: self.exec_cloyster(),
    OpCode.DRATINI   : lambda self: self.exec_dratini(),
    OpCode.DRAGONAIR : lambda self: self.exec_dragonair(),
    OpCode.DRAGONITE : lambda self: self.exec_dragonite(),
    OpCode.MEWTWO    : lambda self: self.exec_mewtwo(),
    OpCode.PONYTA    : lambda self: self.exec_ponyta(),
    OpCode.RAPIDASH  : lambda self: self.exec_rapidash(),
    OpCode.KABUTOPS  : lambda self: self.exec_gastly(),
    OpCode.HYPNO     : lambda self: self.exec_haunter(),
    OpCode.MAGIKARP  : lambda self: self.exec_gengar(),
    OpCode.MAGNETON  : lambda self: self.exec_onix(),
    OpCode.NIDOKING  : lambda self: self.exec_drowzee(),
    OpCode.DITTO     : lambda self: self.exec_hypno(),
    OpCode.NIDORINA  : lambda self: self.exec_krabby(),
    OpCode.NIDORINO  : lambda self: self.exec_kingler(),
    OpCode.PARASECT  : lambda self: self.exec_voltorb(),
    OpCode.PRIMEAPE  : lambda self: self.exec_electrode(),
    OpCode.SHELLDER  : lambda self: self.exec_exeggcute(),
    OpCode.SLOWPOKE  : lambda self: self.exec_exeggutor(),
    OpCode.SQUIRTLE  : lambda self: self.exec_cubone(),
    OpCode.VAPOREON  : lambda self: self.exec_marowak(),
    OpCode.VENOMOTH  : lambda self: self.exec_hitmonlee(),
    OpCode.VENUSAUR  : lambda self: self.exec_hitmonchan(),
    OpCode.BLASTOISE : lambda self: self.exec_lickitung(),
    OpCode.BULBASAUR : lambda self: self.exec_koffing(),
    OpCode.CHARIZARD : lambda self: self.exec_weezing(),
    OpCode.PARAS     : lambda self: self.exec_rhyhorn(),
    OpCode.SEEL      : lambda self: self.exec_rhydon(),
    OpCode.ELECTRODE : lambda self: self.exec_chansey(),
    OpCode.MACHOP    : lambda self: self.exec_tangela(),
    OpCode.EXEGGCUTE : lambda self: self.exec_kangaskhan(),
    OpCode.EXEGGUTOR : lambda self: self.exec_horsea(),
    OpCode.FARFETCHD : lambda self: self.exec_seadra(),
    OpCode.GROWLITHE : lambda self: self.exec_goldeen(),
    OpCode.HITMONLEE : lambda self: self.exec_seaking(),
    OpCode.LICKITUNG : lambda self: self.exec_staryu(),
    OpCode.MAGNEMITE : lambda self: self.exec_starmie(),
    OpCode.NIDOQUEEN : lambda self: self.exec_mr_mime(),
    OpCode.NIDORAN_F : lambda self: self.exec_scyther(),
    OpCode.NIDORAN_M : lambda self: self.exec_jynx(),
    OpCode.NINETALES : lambda self: self.exec_electabuzz(),
    OpCode.PIDGEOTTO : lambda self: self.exec_magmar(),
    OpCode.POLIWHIRL : lambda self: self.exec_pinsir(),
    OpCode.POLIWRATH : lambda self: self.exec_tauros(),
    OpCode.SANDSHREW : lambda self: self.exec_magikarp(),
    OpCode.SANDSLASH : lambda self: self.exec_gyarados(),
    OpCode.TENTACOOL : lambda self: self.exec_lapras(),
    OpCode.VILEPLUME : lambda self: self.exec_ditto(),
    OpCode.WARTORTLE : lambda self: self.exec_eevee(),
    OpCode.AERODACTYL: lambda self: self.exec_vaporeon(),
    OpCode.BELLSPROUT: lambda self: self.exec_jolteon(),
    OpCode.BUTTERFREE: lambda self: self.exec_flareon(),
    OpCode.CHARMANDER: lambda self: self.exec_porygon(),
    OpCode.CHARMELEON: lambda self: self.exec_omanyte(),
    OpCode.ELECTABUZZ: lambda self: self.exec_omastar(),
    OpCode.HITMONCHAN: lambda self: self.exec_kabuto(),
    OpCode.JIGGLYPUFF: lambda self: self.exec_kabutops(),
    OpCode.KANGASKHAN: lambda self: self.exec_aerodactyl(),
    OpCode.TENTACRUEL: lambda self: self.exec_snorlax(),
    OpCode.VICTREEBEL: lambda self: self.exec_articuno(),
    OpCode.WEEPINBELL: lambda self: self.exec_zapdos(),
    OpCode.WIGGLYTUFF: lambda self: self.exec_moltres(),
    OpCode.MEW       : lambda self: self.exec_mew(),
}

@dataclass
class Flags:
    Z: bool = False  # Zero
    N: bool = False  # Negative (bit 7)
    C: bool = False  # Carry
    V: bool = False  # Overflow

    def update_arith(self, result: int, op_a: int, op_b: int, is_sub: bool = False):
        self.Z = (result == 0)
        self.N = (result & 0x80) != 0
        if is_sub:
            self.C = (op_a < op_b)
            self.V = ((op_a ^ op_b) & 0x80) != 0 and ((op_a ^ result) & 0x80) != 0
        else:
            self.C = (result > 0xFF)
            self.V = ((op_a ^ op_b) & 0x80) == 0 and ((op_a ^ result) & 0x80) != 0


@dataclass
class PokecodeVM:
    program: list[int]
    mem_size: int = 65536
    stack_size: int = 256
    call_stack_size: int = 64
    loop_stack_size: int = 32
    checkpoint_slots: int = 8

    # ─── State ───
    mem: list[int] = field(default_factory=list)
    stack: list[int] = field(default_factory=list)
    call_stack: list[int] = field(default_factory=list)
    loop_stack: list[tuple[int, int]] = field(default_factory=list)  # (start_pc, count)
    checkpoints: list[Optional[dict]] = field(default_factory=list)

    acc: int = 0
    ptr: int = 0
    pc: int = 0
    flags: Flags = field(default_factory=Flags)
    regs: list[int] = field(default_factory=lambda: [0]*16)

    input_buffer: list[int] = field(default_factory=list)
    output_buffer: list[int] = field(default_factory=list)

    trace: bool = False
    halted: bool = False
    cycles: int = 0
    mem_reads: int = 0
    mem_writes: int = 0
    mew_encountered: bool = False

    # ─── Debug / Profiling ───
    trace_file: Optional[str] = None

    def __post_init__(self):
        self.mem = [0] * self.mem_size
        self.stack = []
        self.call_stack = []
        self.loop_stack = []
        self.checkpoints = [None] * self.checkpoint_slots
        self.regs = [0] * 16

    # ════════════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════════════

    def _read_mem(self, addr: int) -> int:
        self.mem_reads += 1
        return self.mem[addr & 0xFFFF]

    def _write_mem(self, addr: int, value: int):
        self.mem_writes += 1
        self.mem[addr & 0xFFFF] = value & 0xFF

    def _push_stack(self, value: int):
        if len(self.stack) >= self.stack_size:
            raise RuntimeError("Stack overflow")
        self.stack.append(value & 0xFF)

    def _pop_stack(self) -> int:
        return self.stack.pop() if self.stack else 0

    def _to_signed8(self, v: int) -> int:
        return v - 256 if v >= 128 else v

    def _log_trace(self, op: OpCode, before_state: dict):
        if not self.trace:
            return
        msg = f"PC={self.pc-1:04d} {op.name:12s} | ACC={self.acc:3d} PTR={self.ptr:5d} Z={int(self.flags.Z)} N={int(self.flags.N)} C={int(self.flags.C)} V={int(self.flags.V)}"
        if self.trace_file:
            with open(self.trace_file, 'a') as f:
                f.write(msg + '\n')
        else:
            print(msg)

    # ════════════════════════════════════════════════════════════════════
    # INSTRUCTION IMPLEMENTATIONS
    # ════════════════════════════════════════════════════════════════════

    def exec_bulbasaur(self):   # MEM_RD
        self.acc = self._read_mem(self.ptr)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_ivysaur(self):     # MEM_WR
        self._write_mem(self.ptr, self.acc)

    def exec_venusaur(self):    # PTR_INC
        self.ptr = (self.ptr + 1) & 0xFFFF

    def exec_charmander(self):  # PTR_DEC
        self.ptr = (self.ptr - 1) & 0xFFFF

    def exec_charmeleon(self):  # PTR_SET
        self.ptr = self.acc & 0xFFFF

    def exec_charizard(self):   # PTR_GET
        self.acc = self.ptr & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_squirtle(self):    # MEM_CPY
        self._write_mem(self.ptr + 1, self._read_mem(self.ptr))

    def exec_wartortle(self):   # MEM_SWP
        a = self._read_mem(self.ptr)
        b = self._read_mem(self.ptr + 1)
        self._write_mem(self.ptr, b)
        self._write_mem(self.ptr + 1, a)

    def exec_blastoise(self):   # MEM_CLR
        self._write_mem(self.ptr, 0)
        self.flags.Z = True

    def exec_caterpie(self):    # MEM_FILL
        for i in range(self.acc + 1):
            self._write_mem(self.ptr + i, self.acc)

    def exec_metapod(self):     # MEM_FIND
        for _ in range(256):
            if self._read_mem(self.ptr) == self.acc:
                self.flags.Z = True
                return
            self.ptr = (self.ptr + 1) & 0xFFFF
        self.flags.Z = False

    def exec_butterfree(self):  # MEM_REV
        end = self.ptr + self.acc
        for i in range((self.acc + 1) // 2):
            a = self._read_mem(self.ptr + i)
            b = self._read_mem(end - i)
            self._write_mem(self.ptr + i, b)
            self._write_mem(end - i, a)

    def exec_weedle(self):      # PTR_JMP_FWD
        self.ptr = (self.ptr + self.acc) & 0xFFFF

    def exec_kakuna(self):      # PTR_JMP_BAK
        self.ptr = (self.ptr - self.acc) & 0xFFFF

    def exec_beedrill(self):    # PTR_HOME
        self.ptr = 0

    def exec_pidgey(self):      # MEM_PEEK
        self.acc = self._read_mem(self.acc)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_pidgeotto(self):   # MEM_POKE
        self._write_mem(self.acc, self.regs[0])

    def exec_pidgeot(self):     # MEM_BLOCK
        for i in range(16):
            self._write_mem(self.acc + i, self._read_mem(self.ptr + i))

    def exec_rattata(self):     # MEM_SNAP
        snapshot = bytes(self.mem[i] for i in range(32))
        for b in snapshot:
            self._push_stack(b)

    # ─── CONTROL ───
    def exec_spearow(self):     # JMP
        self.pc = self.acc

    def exec_fearow(self):      # JMP_REL
        self.pc = (self.pc + self._to_signed8(self.acc)) % len(self.program)

    def exec_ekans(self):       # JZ
        if self.flags.Z:
            self.pc = self.acc

    def exec_arbok(self):       # JNZ
        if not self.flags.Z:
            self.pc = self.acc

    def exec_pikachu(self):     # JN
        if self.flags.N:
            self.pc = self.acc

    def exec_raichu(self):      # JC
        if self.flags.C:
            self.pc = self.acc

    def exec_sandshrew(self):   # JNC
        if not self.flags.C:
            self.pc = self.acc

    def exec_sandslash(self):   # JV
        if self.flags.V:
            self.pc = self.acc

    def exec_nidoran_f(self):   # CALL
        if len(self.call_stack) >= self.call_stack_size:
            raise RuntimeError("Call stack overflow")
        self.call_stack.append(self.pc)
        self.pc = self.acc

    def exec_nidorina(self):    # RET
        if self.call_stack:
            self.pc = self.call_stack.pop()
        else:
            self.halted = True

    def exec_nidoqueen(self):   # RETZ
        if self.flags.Z and self.call_stack:
            self.pc = self.call_stack.pop()

    def exec_nidoran_m(self):   # LOOP_BEG
        if len(self.loop_stack) >= self.loop_stack_size:
            raise RuntimeError("Loop stack overflow")
        self.loop_stack.append([self.pc, self.acc])

    def exec_nidorino(self):    # LOOP_END
        if not self.loop_stack:
            return
        start_pc, count = self.loop_stack[-1]
        count -= 1
        if count > 0:
            self.loop_stack[-1][1] = count
            self.pc = start_pc
        else:
            self.loop_stack.pop()

    def exec_nidoking(self):    # BREAK
        if self.loop_stack:
            self.loop_stack.pop()
            # PC already points after LOOP_END due to normal increment

    def exec_clefairy(self):    # CONTINUE
        if self.loop_stack:
            self.pc = self.loop_stack[-1][0]

    def exec_clefable(self):    # SWITCH
        # PC = base + ACC (base is current PC)
        self.pc = (self.pc + self.acc) % len(self.program)

    def exec_vulpix(self):      # CASE (no-op)
        pass

    def exec_ninetales(self):   # DEFAULT (no-op)
        pass

    def exec_jigglypuff(self):  # HALT
        self.halted = True

    # ─── ARITHMETIC ───
    def exec_wigglytuff(self):  # ADD
        val = self._read_mem(self.ptr)
        res = (self.acc + val) & 0xFF
        self.flags.update_arith(res, self.acc, val, False)
        self.acc = res

    def exec_zubat(self):       # SUB
        val = self._read_mem(self.ptr)
        res = (self.acc - val) & 0xFF
        self.flags.update_arith(res, self.acc, val, True)
        self.acc = res

    def exec_golbat(self):      # ADC
        val = self._read_mem(self.ptr)
        carry = 1 if self.flags.C else 0
        res = (self.acc + val + carry) & 0xFF
        self.flags.update_arith(res, self.acc, val + carry, False)
        self.acc = res

    def exec_oddish(self):      # SBC
        val = self._read_mem(self.ptr)
        carry = 1 if self.flags.C else 0
        res = (self.acc - val - carry) & 0xFF
        self.flags.update_arith(res, self.acc, val + carry, True)
        self.acc = res

    def exec_gloom(self):       # MUL
        val = self._read_mem(self.ptr)
        res = (self.acc * val) & 0xFF
        self.flags.Z = (res == 0)
        self.flags.N = (res & 0x80) != 0
        self.acc = res

    def exec_vileplume(self):   # DIV
        val = self._read_mem(self.ptr)
        if val == 0:
            self.acc = 0
            self.flags.C = True
        else:
            self.acc = (self.acc // val) & 0xFF
            self.flags.C = False
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_paras(self):       # MOD
        val = self._read_mem(self.ptr)
        if val == 0:
            self.acc = 0
        else:
            self.acc = self.acc % val
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_parasect(self):    # INC
        res = (self.acc + 1) & 0xFF
        self.flags.update_arith(res, self.acc, 1, False)
        self.acc = res

    def exec_venonat(self):     # DEC
        res = (self.acc - 1) & 0xFF
        self.flags.update_arith(res, self.acc, 1, True)
        self.acc = res

    def exec_venomoth(self):    # NEG
        res = (-self.acc) & 0xFF
        self.flags.update_arith(res, 0, self.acc, True)
        self.acc = res

    def exec_diglett(self):     # ABS
        if self.acc >= 128:
            self.acc = (256 - self.acc) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_dugtrio(self):     # SIGN
        self.acc = 1 if self.acc < 128 else 255
        self.flags.Z = False
        self.flags.N = (self.acc & 0x80) != 0

    def exec_meowth(self):      # RAND
        val = self._read_mem(self.ptr)
        self.acc = random.randint(0, val) if val > 0 else 0
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_persian(self):     # SEED
        random.seed(self.acc)

    def exec_psyduck(self):     # MAX
        val = self._read_mem(self.ptr)
        self.acc = max(self.acc, val)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_golduck(self):     # MIN
        val = self._read_mem(self.ptr)
        self.acc = min(self.acc, val)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_mankey(self):      # AVG
        val = self._read_mem(self.ptr)
        self.acc = (self.acc + val) >> 1
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_primeape(self):    # SQRT
        import math
        self.acc = int(math.sqrt(self.acc))
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_growlithe(self):   # POW2
        self.acc = (1 << (self.acc & 7)) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    # ─── BITWISE ───
    def exec_arcanine(self):    # AND
        val = self._read_mem(self.ptr)
        self.acc &= val
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_poliwag(self):     # OR
        val = self._read_mem(self.ptr)
        self.acc |= val
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_poliwhirl(self):   # XOR
        val = self._read_mem(self.ptr)
        self.acc ^= val
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_poliwrath(self):   # NOT
        self.acc = (~self.acc) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_abra(self):        # SHL
        self.flags.C = (self.acc & 0x80) != 0
        self.acc = (self.acc << 1) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_kadabra(self):     # SHR
        self.flags.C = (self.acc & 0x01) != 0
        self.acc >>= 1
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_alakazam(self):    # ROL
        old_c = 1 if self.flags.C else 0
        self.flags.C = (self.acc & 0x80) != 0
        self.acc = ((self.acc << 1) | old_c) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_machop(self):      # ROR
        old_c = 1 if self.flags.C else 0
        self.flags.C = (self.acc & 0x01) != 0
        self.acc = (self.acc >> 1) | (old_c << 7)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_machoke(self):     # SHL_N
        n = self._read_mem(self.ptr) & 7
        for _ in range(n):
            self.flags.C = (self.acc & 0x80) != 0
            self.acc = (self.acc << 1) & 0xFF
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_machamp(self):     # SHR_N
        n = self._read_mem(self.ptr) & 7
        for _ in range(n):
            self.flags.C = (self.acc & 0x01) != 0
            self.acc >>= 1
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_bellsprout(self):  # BIT_TST
        bit = self._read_mem(self.ptr) & 7
        self.flags.Z = (self.acc & (1 << bit)) == 0

    def exec_weepinbell(self):  # BIT_SET
        bit = self._read_mem(self.ptr) & 7
        self.acc |= (1 << bit)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_victreebel(self):  # BIT_CLR
        bit = self._read_mem(self.ptr) & 7
        self.acc &= ~(1 << bit)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_tentacool(self):   # BIT_TGL
        bit = self._read_mem(self.ptr) & 7
        self.acc ^= (1 << bit)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_tentacruel(self):  # BIT_CNT
        self.acc = bin(self.acc).count('1')
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_geodude(self):     # PARITY
        self.flags.Z = (bin(self.acc).count('1') % 2 == 0)

    def exec_graveler(self):    # MSB
        self.acc = self.acc.bit_length() - 1 if self.acc else 0
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_golem(self):       # LSB
        if self.acc == 0:
            self.acc = 0
        else:
            self.acc = (self.acc & -self.acc).bit_length() - 1
        self.flags.Z = (self.acc == 0)
        self.flags.N = False

    def exec_raticate(self):    # NOP2 (second nop)
        pass

    def exec_dratini(self):     # NOP3
        pass

    def exec_dragonair(self):   # NOP4
        pass

    def exec_dragonite(self):   # NOP5
        pass

    def exec_mewtwo(self):      # NOP6
        pass

    def exec_ponyta(self):      # NOP7
        pass

    def exec_rapidash(self):    # NOP8
        pass

    # ─── STACK ───
    def exec_slowpoke(self):    # PUSH
        self._push_stack(self.acc)

    def exec_slowbro(self):     # POP
        self.acc = self._pop_stack()

    def exec_magnemite(self):   # DUP
        if self.stack:
            self._push_stack(self.stack[-1])

    def exec_magneton(self):    # SWP
        if len(self.stack) >= 2:
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def exec_farfetchd(self):   # ROT3
        if len(self.stack) >= 3:
            self.stack[-3], self.stack[-2], self.stack[-1] = \
                self.stack[-2], self.stack[-1], self.stack[-3]

    def exec_doduo(self):       # OVER
        if len(self.stack) >= 2:
            self._push_stack(self.stack[-2])

    def exec_dodrio(self):      # NIP
        if len(self.stack) >= 2:
            del self.stack[-2]

    def exec_seel(self):        # TUCK
        if len(self.stack) >= 2:
            top = self.stack.pop()
            self.stack[-1], top = top, self.stack[-1]
            self.stack.append(top)

    def exec_dewgong(self):     # DEPTH
        self.acc = len(self.stack) & 0xFF

    def exec_grimer(self):      # CLEAR_STACK
        self.stack.clear()

    def exec_muk(self):         # STACK_TO_MEM
        n = self.acc
        for i in range(n):
            self._write_mem(self.ptr + i, self._pop_stack())

    def exec_shellder(self):    # MEM_TO_STACK
        n = self.acc
        for i in range(n - 1, -1, -1):
            self._push_stack(self._read_mem(self.ptr + i))

    def exec_cloyster(self):    # STACK_SNAP
        if not hasattr(self, '_stack_snapshot'):
            self._stack_snapshot = self.stack.copy()
        else:
            self.stack = self._stack_snapshot.copy()

    # ─── I/O ───
    def exec_gastly(self):      # IN
        self.acc = self.input_buffer.pop(0) if self.input_buffer else 0
        self.flags.Z = (self.acc == 0)

    def exec_haunter(self):     # OUT
        self.output_buffer.append(self.acc)
        if self.trace:
            print(chr(self.acc), end='', flush=True)

    def exec_gengar(self):      # OUT_NUM
        self.output_buffer.extend(str(self.acc).encode())
        if self.trace:
            print(self.acc, end='', flush=True)

    def exec_onix(self):        # OUT_HEX
        self.output_buffer.extend(f"{self.acc:02X}".encode())
        if self.trace:
            print(f"{self.acc:02X}", end='', flush=True)

    def exec_drowzee(self):     # OUT_BIN
        self.output_buffer.extend(f"{self.acc:08b}".encode())
        if self.trace:
            print(f"{self.acc:08b}", end='', flush=True)

    def exec_hypno(self):       # OUT_MEM
        self.output_buffer.append(self._read_mem(self.ptr))
        if self.trace:
            print(chr(self._read_mem(self.ptr)), end='', flush=True)

    def exec_krabby(self):      # DEBUG
        print(f"PC={self.pc} ACC={self.acc} PTR={self.ptr} "
              f"Z={int(self.flags.Z)} N={int(self.flags.N)} "
              f"C={int(self.flags.C)} V={int(self.flags.V)} "
              f"STACK={len(self.stack)} CALLS={len(self.call_stack)}")

    def exec_kingler(self):     # DUMP_MEM
        for i in range(0, 256, 16):
            line = f"{i:04X}: " + ' '.join(f"{self.mem[i+j]:02X}" for j in range(16))
            print(line)

    def exec_voltorb(self):     # DUMP_STACK
        print("Stack:", ' '.join(f"{v:02X}" for v in self.stack[-16:]))

    def exec_electrode(self):   # DUMP_REGS
        print("Regs:", ' '.join(f"R{i}={self.regs[i]:02X}" for i in range(16)))

    def exec_exeggcute(self):   # READ_NUM
        try:
            self.acc = int(input()) & 0xFF
        except:
            self.acc = 0
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_exeggutor(self):   # READ_HEX
        try:
            s = input().strip()[:2]
            self.acc = int(s, 16) & 0xFF
        except:
            self.acc = 0
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_cubone(self):      # READ_LINE
        try:
            line = input()
            for i, ch in enumerate(line):
                self._write_mem(self.ptr + i, ord(ch))
            self._write_mem(self.ptr + len(line), 0)
        except:
            self._write_mem(self.ptr, 0)

    def exec_marowak(self):     # WRITE_FILE (stub)
        pass

    def exec_hitmonlee(self):   # READ_FILE (stub)
        pass

    def exec_hitmonchan(self):  # SLEEP
        time.sleep(self.acc / 1000.0)

    def exec_lickitung(self):   # TIME
        self.acc = int(time.time() * 1000) & 0xFF

    def exec_koffing(self):     # RNG_BYTE
        self.acc = random.randint(0, 255)
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    def exec_weezing(self):     # HASH (CRC8)
        crc = 0
        for i in range(16):
            crc ^= self._read_mem(self.ptr + i)
            for _ in range(8):
                crc = (crc << 1) ^ 0x07 if crc & 0x80 else crc << 1
                crc &= 0xFF
        self.acc = crc
        self.flags.Z = (self.acc == 0)
        self.flags.N = (self.acc & 0x80) != 0

    # ─── REGISTERS ───
    def _reg_idx(self) -> int:
        return self._read_mem(self.ptr) & 15

    def exec_rhyhorn(self):     # REG_GET
        self.acc = self.regs[self._reg_idx()]

    def exec_rhydon(self):      # REG_SET
        self.regs[self._reg_idx()] = self.acc

    def exec_chansey(self):     # REG_XCHG
        idx = self._reg_idx()
        self.acc, self.regs[idx] = self.regs[idx], self.acc

    def exec_tangela(self):     # REG_INC
        idx = self._reg_idx()
        self.regs[idx] = (self.regs[idx] + 1) & 0xFF

    def exec_kangaskhan(self):  # REG_DEC
        idx = self._reg_idx()
        self.regs[idx] = (self.regs[idx] - 1) & 0xFF

    def exec_horsea(self):      # REG_ADD
        idx = self._reg_idx()
        self.regs[idx] = (self.regs[idx] + self.acc) & 0xFF

    def exec_seadra(self):      # REG_SUB
        idx = self._reg_idx()
        self.regs[idx] = (self.regs[idx] - self.acc) & 0xFF

    def exec_goldeen(self):     # REG_MOV
        self.regs[self._reg_idx()] = self.regs[self.acc & 15]

    def exec_seaking(self):     # REG_CPY
        for i in range(16):
            self._write_mem(self.ptr + i, self.regs[i])

    def exec_staryu(self):      # REG_SWP
        a = self._reg_idx()
        b = self.acc & 15
        self.regs[a], self.regs[b] = self.regs[b], self.regs[a]

    def exec_starmie(self):     # REG_CLR
        self.regs = [0] * 16

    def exec_mr_mime(self):     # REG_SAVE
        for r in self.regs:
            self._push_stack(r)

    def exec_scyther(self):     # REG_REST
        for i in reversed(range(16)):
            self.regs[i] = self._pop_stack()

    def exec_jynx(self):        # REG_ROT
        n = self.acc & 15
        self.regs = self.regs[n:] + self.regs[:n]

    def exec_electabuzz(self):  # REG_MUL
        idx = self._reg_idx()
        self.regs[idx] = (self.regs[idx] * self.acc) & 0xFF

    def exec_magmar(self):      # REG_DIV
        idx = self._reg_idx()
        if self.acc != 0:
            self.regs[idx] = (self.regs[idx] // self.acc) & 0xFF

    def exec_pinsir(self):      # REG_MOD
        idx = self._reg_idx()
        if self.acc != 0:
            self.regs[idx] = self.regs[idx] % self.acc

    def exec_tauros(self):      # REG_AND
        idx = self._reg_idx()
        self.regs[idx] &= self.acc

    def exec_magikarp(self):    # REG_OR
        idx = self._reg_idx()
        self.regs[idx] |= self.acc

    # ─── META ───
    def exec_gyarados(self):    # SYS_EXIT
        self.halted = True
        raise SystemExit(self.acc)

    def exec_lapras(self):      # SYS_ARG
        self.regs[0] = len(sys.argv) - 1
        for i, arg in enumerate(sys.argv[1:]):
            if i < 15:
                self.regs[i+1] = sum(ord(c) for c in arg) & 0xFF

    def exec_ditto(self):       # CLONE (stub - no real fork in Python)
        pass

    def exec_eevee(self):       # MORPH (stub)
        pass

    def exec_vaporeon(self):    # TRACE_ON
        self.trace = True

    def exec_jolteon(self):     # TRACE_OFF
        self.trace = False

    def exec_flareon(self):     # PROFILE
        self.regs[0] = self.cycles & 0xFF
        self.regs[1] = self.mem_reads & 0xFF
        self.regs[2] = self.mem_writes & 0xFF

    def exec_porygon(self):     # SELF_MOD
        if 0 <= self.pc + self.acc < len(self.program):
            self.program[self.pc + self.acc] = self.regs[0]

    def exec_omanyte(self):     # CHECKPOINT
        slot = self.acc & 7
        self.checkpoints[slot] = {
            'mem': self.mem[:],
            'stack': self.stack[:],
            'call_stack': self.call_stack[:],
            'loop_stack': [list(x) for x in self.loop_stack],
            'acc': self.acc, 'ptr': self.ptr, 'pc': self.pc,
            'flags': Flags(self.flags.Z, self.flags.N, self.flags.C, self.flags.V),
            'regs': self.regs[:],
        }

    def exec_omastar(self):     # RESTORE
        slot = self.acc & 7
        cp = self.checkpoints[slot]
        if cp:
            self.mem = cp['mem'][:]
            self.stack = cp['stack'][:]
            self.call_stack = cp['call_stack'][:]
            self.loop_stack = [list(x) for x in cp['loop_stack']]
            self.acc = cp['acc']
            self.ptr = cp['ptr']
            self.pc = cp['pc']
            self.flags = cp['flags']
            self.regs = cp['regs'][:]

    def exec_kabuto(self):      # TIME_TRAVEL
        self.exec_omastar()

    def exec_kabutops(self):    # PARALLEL (stub - no threads)
        pass

    def exec_aerodactyl(self):  # ATOMIC_BEG
        pass

    def exec_snorlax(self):     # ATOMIC_END
        pass

    def exec_articuno(self):    # FREEZE
        pass

    def exec_zapdos(self):      # THAW
        pass

    def exec_moltres(self):     # BURN
        self.mem = [0] * self.mem_size
        self.stack.clear()
        self.call_stack.clear()
        self.loop_stack.clear()
        self.acc = self.ptr = self.pc = 0
        self.flags = Flags()
        self.regs = [0] * 16

    def exec_mew(self):         # META
        self.mew_encountered = True

    # ══════════════════════════════════════════════════════════════════════


    # ════════════════════════════════════════════════════════════════════
    # RUN LOOP
    # ════════════════════════════════════════════════════════════════════

    def run(self, max_cycles: int = 10_000_000) -> str:
        """Ejecuta el programa. Retorna output como string."""
        self.cycles = 0
        self.halted = False
        prog_len = len(self.program)

        while not self.halted and self.cycles < max_cycles:
            if self.pc >= prog_len:
                self.halted = True
                break

            opcode_val = self.program[self.pc]
            self.pc += 1

            try:
                opcode = OpCode(opcode_val)
            except ValueError:
                continue  # Unknown opcode = NOP

            if self.trace:
                before = {'acc': self.acc, 'ptr': self.ptr, 'pc': self.pc - 1}
                self._log_trace(opcode, before)

            handler = _DISPATCH_TABLE.get(opcode)
            if handler:
                handler(self)
            else:
                pass  # NOP

            self.cycles += 1

        if self.cycles >= max_cycles:
            raise RuntimeError(f"Max cycles ({max_cycles}) exceeded")

        return ''.join(chr(b) for b in self.output_buffer if b < 128)


# ═══════════════════════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════════════════════

def parse_pokecode(source: str) -> list[int]:
    """Parsea código fuente POKECODE a lista de opcodes.

    Comentarios: lneas que empiezan con # o ; se omiten enteras.
    Los tokens no reconocidos se ignoran (no son fuzzy).

    Mew encoding unario:
    - 1 Mew = MEW (NOP)
    - N Mews (2-151) = opcode (N-1) directamente por VALOR (no por posición de enum)
    - >151 Mews = opcode 151 (MEW) + argumento = count - 151
    """
    # Reverse lookup: opcode value -> OpCode member (robusto a gaps)
    _VAL_TO_OP = {int(op): op for op in OpCode}

    # 1) Descartar líneas de comentario completas (# o ; inicial, tras strip).
    #    Convertimos el resto a tokens respetando saltos de línea.
    clean_lines = []
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith(';'):
            continue
        # Eliminar comentarios inline (# ... o ; ...) preservando lo anterior
        for marker in ('#', ';'):
            idx = line.find(marker)
            if idx >= 0:
                line = line[:idx]
        clean_lines.append(line)
    clean_source = ' '.join(clean_lines)

    tokens = clean_source.lower().replace(',', ' ').replace('.', ' ').split()
    program = []
    i = 0
    while i < len(tokens):
        token = tokens[i].strip('.,;:()[]{}')
        if not token:
            i += 1
            continue
        
        # Mew encoding: contar Mews consecutivos
        if token == 'mew':
            count = 0
            while i < len(tokens) and tokens[i].strip('.,;:()[]{}') == 'mew':
                count += 1
                i += 1
            
            if count == 1:
                # 1 Mew = MEW (NOP)
                program.append(OpCode.MEW)
            elif count == 151:
                # 151 Mews = MEW caso especial recursivo
                program.append(OpCode.MEW)
            elif count < 151:
                # N Mews (2..150) = opcode (N-1) por VALOR directo
                target_val = count - 1
                target_op = _VAL_TO_OP.get(target_val, OpCode.MEW)
                program.append(target_op)
            else:
                # >151: MEW + argumento = count - 151 (simplificado)
                program.append(OpCode.MEW)
            continue
        
        if token in NAME_TO_OPCODE:
            program.append(NAME_TO_OPCODE[token])
        else:
            # No fuzzy match: si el token no existe, se ignora (comentario/residuo)
            pass
        i += 1
    return program


def run_pokecode(source: str, input_data: str = "", trace: bool = False,
                 max_cycles: int = 10_000_000, trace_file: str = None) -> str:
    """Función de alto nivel para ejecutar código POKECODE."""
    program = parse_pokecode(source)
    vm = PokecodeVM(program=program)
    vm.trace = trace
    vm.trace_file = trace_file
    if input_data:
        vm.input_buffer = [ord(c) for c in input_data]
    return vm.run(max_cycles=max_cycles)


# ═══════════════════════════════════════════════════════════════════════
# EJEMPLOS (usa los nombres cortos de la nueva permutación)
# ═══════════════════════════════════════════════════════════════════════

HELLO_WORLD = """
# Hello World POKECODE - imprime Hi!

# H = 72
EEVEE ABRA
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK
JYNX ARBOK

# i = 105
EEVEE ABRA
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK
JYNX ARBOK

# ! = 33
EEVEE ABRA
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK
JYNX ARBOK

# 
 = 10
EEVEE ABRA
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
JYNX

ZUBAT
DITTO ARBOK DITTO ARBOK DITTO ARBOK DITTO
DODUO
"""

FIBONACCI = """
# Fibonacci (0,1,1,2,3,5,8,13,21,...) — imprime como números
# AO: FIBONACCI output > HYPNO caracteres no decimales. Aca usamos
# MAGIKARP (OUT_NUM) para imprimir como decimal.
# Setup: ACC=0 (first fib), store MEM[0]=0; ACC=1 (next) store MEM[1]=1
# Loop: load MEM[1] -> temp, add MEM[0], store MEM[2], shift window
# (Resultado parcial - ejemplo simplificado.)
EEVEE ABRA JYNX ARBOK
MUK JYNX ARBOK
DODUO
"""

BRAINFUCK_INTERPRETER = """
# Brainfuck mapping (nueva permutación)
# > = ARBOK (PTR_INC)    < = GENGAR (PTR_DEC)
# + = MUK (INC)          - = ONIX (DEC)        . = DITTO (OUT_MEM)
# , = KABUTOPS (IN)      [ = CUBONE (JZ)       ] = DODRIO (JNZ)
"""



# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="POKECODE Interpreter — 151 Pokémon Gen 1")
    parser.add_argument('file', nargs='?', help='Archivo .pok con código POKECODE')
    parser.add_argument('-c', '--code', help='Código inline')
    parser.add_argument('-i', '--input', default='', help='Input string')
    parser.add_argument('-t', '--trace', action='store_true', help='Enable trace')
    parser.add_argument('--trace-file', help='Trace output file')
    parser.add_argument('--max-cycles', type=int, default=10_000_000)
    parser.add_argument('--example', choices=['hello', 'fib', 'bf'],
                        help='Run built-in example')
    parser.add_argument('--list', action='store_true', help='List all 151 instructions')

    args = parser.parse_args()

    if args.list:
        print("POKECODE — 151 Instrucciones (Gen 1)")
        print("=" * 60)
        for name, op in sorted(NAME_TO_OPCODE.items(), key=lambda x: x[1]):
            print(f"{op:3d}  {name}")
        return

    if args.example:
        if args.example == 'hello':
            source = HELLO_WORLD
        elif args.example == 'fib':
            source = FIBONACCI
        elif args.example == 'bf':
            source = BRAINFUCK_INTERPRETER
        else:
            source = ""
    elif args.code:
        source = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            source = f.read()
    else:
        parser.print_help()
        return

    try:
        output = run_pokecode(
            source,
            input_data=args.input,
            trace=args.trace,
            max_cycles=args.max_cycles
        )
        if output:
            print(output)
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()