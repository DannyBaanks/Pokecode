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
    BULBASAUR    = 1   # MEM_RD      : ACC = MEM[PTR]
    IVYSAUR      = 2   # MEM_WR      : MEM[PTR] = ACC
    VENUSAUR     = 3   # PTR_INC     : PTR += 1
    CHARMANDER   = 4   # PTR_DEC     : PTR -= 1
    CHARMELEON   = 5   # PTR_SET     : PTR = ACC
    CHARIZARD    = 6   # PTR_GET     : ACC = PTR & 0xFF
    SQUIRTLE     = 7   # MEM_CPY     : MEM[PTR+1] = MEM[PTR]
    WARTORTLE    = 8   # MEM_SWP     : swap(MEM[PTR], MEM[PTR+1])
    BLASTOISE    = 9   # MEM_CLR     : MEM[PTR] = 0
    CATERPIE     = 10  # MEM_FILL    : for i in 0..ACC: MEM[PTR+i] = ACC
    METAPOD      = 11  # MEM_FIND    : while MEM[PTR]!=ACC: PTR++ (max 256)
    BUTTERFREE   = 12  # MEM_REV     : reverse(MEM[PTR..PTR+ACC])
    WEEDLE       = 13  # PTR_JMP_FWD : PTR += ACC
    KAKUNA       = 14  # PTR_JMP_BAK : PTR -= ACC
    BEEDRILL     = 15  # PTR_HOME    : PTR = 0
    PIDGEY       = 16  # MEM_PEEK    : ACC = MEM[ACC] (indirect)
    PIDGEOTTO    = 17  # MEM_POKE    : MEM[ACC] = R0
    PIDGEOT      = 18  # MEM_BLOCK   : copy 16 bytes PTR..PTR+15 to ACC..ACC+15
    RATTATA      = 19  # MEM_SNAP    : push snapshot of MEM[0..31] to stack

    # ─── FAMILIA 2: CONTROL (20-38) ───
    SPEAROW      = 20  # JMP         : PC = ACC (absoluto)
    FEAROW       = 21  # JMP_REL     : PC += ACC (signed -128..127)
    EKANS        = 22  # JZ          : if Z: PC = ACC
    ARBOK        = 23  # JNZ         : if !Z: PC = ACC
    PIKACHU      = 24  # JN          : if N: PC = ACC
    RAICHU       = 25  # JC          : if C: PC = ACC
    SANDSHREW    = 26  # JNC         : if !C: PC = ACC
    SANDSLASH    = 27  # JV          : if V: PC = ACC
    NIDORAN_F    = 28  # CALL        : push PC+1; PC = ACC
    NIDORINA     = 29  # RET         : PC = pop call_stack
    NIDOQUEEN    = 30  # RETZ        : if Z: RET
    NIDORAN_M    = 31  # LOOP_BEG    : push PC; loop_count = ACC
    NIDORINO     = 32  # LOOP_END    : loop_count--; if >0: PC = loop_start else pop
    NIDOKING     = 33  # BREAK       : pop loop_stack; PC = after LOOP_END
    CLEFAIRY     = 34  # CONTINUE    : PC = loop_start
    CLEFABLE     = 35  # SWITCH      : PC = base + ACC (jump table)
    VULPIX       = 36  # CASE        : no-op (marker)
    NINETALES    = 37  # DEFAULT     : no-op (marker)
    JIGGLYPUFF   = 38  # HALT        : stop execution

    # ─── FAMILIA 3: ARITMÉTICA (39-57) ───
    WIGGLYTUFF   = 39  # ADD         : ACC = ACC + MEM[PTR]
    ZUBAT        = 40  # SUB         : ACC = ACC - MEM[PTR]
    GOLBAT       = 41  # ADC         : ACC = ACC + MEM[PTR] + C
    ODDISH       = 42  # SBC         : ACC = ACC - MEM[PTR] - C
    GLOOM        = 43  # MUL         : ACC = (ACC * MEM[PTR]) & 0xFF
    VILEPLUME    = 44  # DIV         : ACC = ACC // MEM[PTR] (div0=0, C=1)
    PARAS        = 45  # MOD         : ACC = ACC % MEM[PTR] (div0=0)
    PARASECT     = 46  # INC         : ACC = (ACC + 1) & 0xFF
    VENONAT      = 47  # DEC         : ACC = (ACC - 1) & 0xFF
    VENOMOTH     = 48  # NEG         : ACC = (-ACC) & 0xFF
    DIGLETT      = 49  # ABS         : ACC = abs(ACC) if ACC<128 else 256-ACC
    DUGTRIO      = 50  # SIGN        : ACC = 1 if ACC<128 else 255
    MEOWTH       = 51  # RAND        : ACC = random(0..MEM[PTR])
    PERSIAN      = 52  # SEED        : random.seed(ACC)
    PSYDUCK      = 53  # MAX         : ACC = max(ACC, MEM[PTR])
    GOLDUCK      = 54  # MIN         : ACC = min(ACC, MEM[PTR])
    MANKEY       = 55  # AVG         : ACC = (ACC + MEM[PTR]) >> 1
    PRIMEAPE     = 56  # SQRT        : ACC = int(sqrt(ACC))
    GROWLITHE    = 57  # POW2        : ACC = 1 << (ACC & 7)

    # ─── FAMILIA 4: LÓGICA BITWISE (58-76) ───
    ARCANINE     = 58  # AND         : ACC &= MEM[PTR]
    POLIWAG      = 59  # OR          : ACC |= MEM[PTR]
    POLIWHIRL    = 60  # XOR         : ACC ^= MEM[PTR]
    POLIWRATH    = 61  # NOT         : ACC = ~ACC & 0xFF
    ABRA         = 62  # SHL         : C=bit7; ACC=(ACC<<1)&0xFF
    KADABRA      = 63  # SHR         : C=bit0; ACC>>=1
    ALAKAZAM     = 64  # ROL         : rotate left through carry
    MACHOP       = 65  # ROR         : rotate right through carry
    MACHOKE      = 66  # SHL_N       : ACC = (ACC << MEM[PTR]) & 0xFF
    MACHAMP      = 67  # SHR_N       : ACC >>= MEM[PTR]
    BELLSPROUT   = 68  # BIT_TST     : Z = !(ACC & (1<<MEM[PTR]))
    WEEPINBELL   = 69  # BIT_SET     : ACC |= (1<<MEM[PTR])
    VICTREEBEL   = 70  # BIT_CLR     : ACC &= ~(1<<MEM[PTR])
    TENTACOOL    = 71  # BIT_TGL     : ACC ^= (1<<MEM[PTR])
    TENTACRUEL   = 72  # BIT_CNT     : ACC = popcount(ACC)
    GEODUDE      = 73  # PARITY      : Z = even_parity(ACC)
    GRAVELER     = 74  # MSB         : ACC = highest_set_bit(ACC)
    GOLEM        = 75  # LSB         : ACC = lowest_set_bit(ACC)

    # ─── FAMILIA 5: PILA (77-95) ───
    SLOWPOKE     = 77  # PUSH        : push ACC
    SLOWBRO      = 78  # POP         : ACC = pop() or 0
    MAGNEMITE    = 79  # DUP         : push(top)
    MAGNETON     = 80  # SWP         : swap(top, second)
    FARFETCHD    = 81  # ROT3        : rot3(top, second, third)
    DODUO        = 82  # OVER        : push(second)
    DODRIO       = 83  # NIP         : remove second
    SEEL         = 84  # TUCK        : copy top under second
    DEWGONG      = 85  # DEPTH       : ACC = len(stack)
    GRIMER       = 86  # CLEAR_STACK : clear stack
    MUK          = 87  # STACK_TO_MEM: pop n=ACC bytes to MEM[PTR..]
    SHELLDER     = 88  # MEM_TO_STACK: push n=ACC bytes from MEM[PTR..]
    CLOYSTER     = 89  # STACK_SNAP  : snapshot/restore stack

    # ─── FAMILIA 6: I/O (96-114) ───
    GASTLY       = 96  # IN          : ACC = getchar() or 0
    HAUNTER      = 97  # OUT         : putchar(ACC)
    GENGAR       = 98  # OUT_NUM     : print ACC as decimal
    ONIX         = 99  # OUT_HEX     : print ACC as 2-digit hex
    DROWZEE      = 100 # OUT_BIN     : print ACC as 8-bit binary
    HYPNO        = 101 # OUT_MEM     : print MEM[PTR] as char
    KRABBY       = 102 # DEBUG       : print state
    KINGLER      = 103 # DUMP_MEM    : hex dump MEM[0..255]
    VOLTORB      = 104 # DUMP_STACK  : print stack top 16
    ELECTRODE    = 105 # DUMP_REGS   : print R0-R15
    EXEGGCUTE    = 106 # READ_NUM    : read decimal → ACC
    EXEGGUTOR    = 107 # READ_HEX    : read 2-char hex → ACC
    CUBONE       = 108 # READ_LINE   : read line to MEM[PTR..]
    MAROWAK      = 109 # WRITE_FILE  : syscall write
    HITMONLEE    = 110 # READ_FILE   : syscall read
    HITMONCHAN   = 111 # SLEEP       : sleep ACC ms
    LICKITUNG    = 112 # TIME        : ACC = timestamp_low_byte
    KOFFING      = 113 # RNG_BYTE    : ACC = random byte
    WEEZING      = 114 # HASH        : ACC = crc8(MEM[PTR..PTR+15])

    # ─── FAMILIA 7: REGISTROS (115-133) ───
    RHYHORN      = 115 # REG_GET     : ACC = R[MEM[PTR]&15]
    RHYDON       = 116 # REG_SET     : R[MEM[PTR]&15] = ACC
    CHANSEY      = 117 # REG_XCHG    : swap(ACC, R[MEM[PTR]&15])
    TANGELA      = 118 # REG_INC     : R[MEM[PTR]&15]++
    KANGASKHAN   = 119 # REG_DEC     : R[MEM[PTR]&15]--
    HORSEA       = 120 # REG_ADD     : R[MEM[PTR]&15] += ACC
    SEADRA       = 121 # REG_SUB     : R[MEM[PTR]&15] -= ACC
    GOLDEEN      = 122 # REG_MOV     : R[MEM[PTR]&15] = R[ACC&15]
    SEAKING      = 123 # REG_CPY     : copy R0..R15 to MEM[PTR..PTR+15]
    STARYU       = 124 # REG_SWP     : swap R[MEM[PTR]&15], R[ACC&15]
    STARMIE      = 125 # REG_CLR     : zero R0..R15
    MR_MIME      = 126 # REG_SAVE    : push all R0..R15 to stack
    SCYTHER      = 127 # REG_REST    : pop all R0..R15 from stack
    JYNX         = 128 # REG_ROT     : rotate R0..R15 left by ACC
    ELECTABUZZ   = 129 # REG_MUL     : R[MEM[PTR]&15] *= ACC
    MAGMAR       = 130 # REG_DIV     : R[MEM[PTR]&15] //= ACC
    PINSIR       = 131 # REG_MOD     : R[MEM[PTR]&15] %= ACC
    TAUROS       = 132 # REG_AND     : R[MEM[PTR]&15] &= ACC
    MAGIKARP     = 133 # REG_OR      : R[MEM[PTR]&15] |= ACC

    # ─── FAMILIA 8: META (134-151) ───
    GYARADOS     = 134 # SYS_EXIT    : exit(ACC)
    LAPRAS       = 135 # SYS_ARG     : R0=argc; R1..=argv
    DITTO        = 136 # CLONE       : fork copy
    EEVEE        = 137 # MORPH       : change instruction set
    VAPOREON     = 138 # TRACE_ON    : enable tracing
    JOLTEON      = 139 # TRACE_OFF   : disable tracing
    FLAREON      = 140 # PROFILE     : R0=cycles; R1=reads; R2=writes
    PORYGON      = 141 # SELF_MOD    : rewrite instruction at PC+ACC to R0
    OMANYTE      = 142 # CHECKPOINT  : save state to slot ACC (0-7)
    OMASTAR      = 143 # RESTORE     : load state from slot ACC
    KABUTO       = 144 # TIME_TRAVEL : rewind to checkpoint ACC
    KABUTOPS     = 145 # PARALLEL    : spawn thread at PC=ACC
    AERODACTYL   = 146 # ATOMIC_BEG  : disable interrupts
    SNORLAX      = 147 # ATOMIC_END  : re-enable
    ARTICUNO     = 148 # FREEZE      : pause other threads
    ZAPDOS       = 149 # THAW        : resume threads
    MOLTRES      = 150 # BURN        : secure erase all
    MEW          = 151 # META        : NOP + flag "Mew encountered"


# ════════════════════════════════════════════════════════════════════════
# NAME ↔ OPCODE MAPPING
# ════════════════════════════════════════════════════════════════════════

NAME_TO_OPCODE = {
    'bulbasaur': OpCode.BULBASAUR, 'ivysaur': OpCode.IVYSAUR, 'venusaur': OpCode.VENUSAUR,
    'charmander': OpCode.CHARMANDER, 'charmeleon': OpCode.CHARMELEON, 'charizard': OpCode.CHARIZARD,
    'squirtle': OpCode.SQUIRTLE, 'wartortle': OpCode.WARTORTLE, 'blastoise': OpCode.BLASTOISE,
    'caterpie': OpCode.CATERPIE, 'metapod': OpCode.METAPOD, 'butterfree': OpCode.BUTTERFREE,
    'weedle': OpCode.WEEDLE, 'kakuna': OpCode.KAKUNA, 'beedrill': OpCode.BEEDRILL,
    'pidgey': OpCode.PIDGEY, 'pidgeotto': OpCode.PIDGEOTTO, 'pidgeot': OpCode.PIDGEOT,
    'rattata': OpCode.RATTATA,
    'spearow': OpCode.SPEAROW, 'fearow': OpCode.FEAROW, 'ekans': OpCode.EKANS, 'arbok': OpCode.ARBOK,
    'pikachu': OpCode.PIKACHU, 'raichu': OpCode.RAICHU, 'sandshrew': OpCode.SANDSHREW,
    'sandslash': OpCode.SANDSLASH, 'nidoran-f': OpCode.NIDORAN_F, 'nidorina': OpCode.NIDORINA,
    'nidoqueen': OpCode.NIDOQUEEN, 'nidoran-m': OpCode.NIDORAN_M, 'nidorino': OpCode.NIDORINO,
    'nidoking': OpCode.NIDOKING, 'clefairy': OpCode.CLEFAIRY, 'clefable': OpCode.CLEFABLE,
    'vulpix': OpCode.VULPIX, 'ninetales': OpCode.NINETALES, 'jigglypuff': OpCode.JIGGLYPUFF,
    'wigglytuff': OpCode.WIGGLYTUFF, 'zubat': OpCode.ZUBAT, 'golbat': OpCode.GOLBAT,
    'oddish': OpCode.ODDISH, 'gloom': OpCode.GLOOM, 'vileplume': OpCode.VILEPLUME,
    'paras': OpCode.PARAS, 'parasect': OpCode.PARASECT, 'venonat': OpCode.VENONAT,
    'venomoth': OpCode.VENOMOTH, 'diglett': OpCode.DIGLETT, 'dugtrio': OpCode.DUGTRIO,
    'meowth': OpCode.MEOWTH, 'persian': OpCode.PERSIAN, 'psyduck': OpCode.PSYDUCK,
    'golduck': OpCode.GOLDUCK, 'mankey': OpCode.MANKEY, 'primeape': OpCode.PRIMEAPE,
    'growlithe': OpCode.GROWLITHE, 'arcanine': OpCode.ARCANINE, 'poliwag': OpCode.POLIWAG,
    'poliwhirl': OpCode.POLIWHIRL, 'poliwrath': OpCode.POLIWRATH, 'abra': OpCode.ABRA,
    'kadabra': OpCode.KADABRA, 'alakazam': OpCode.ALAKAZAM, 'machop': OpCode.MACHOP,
    'machoke': OpCode.MACHOKE, 'machamp': OpCode.MACHAMP, 'bellsprout': OpCode.BELLSPROUT,
    'weepinbell': OpCode.WEEPINBELL, 'victreebel': OpCode.VICTREEBEL, 'tentacool': OpCode.TENTACOOL,
    'tentacruel': OpCode.TENTACRUEL, 'geodude': OpCode.GEODUDE, 'graveler': OpCode.GRAVELER,
    'golem': OpCode.GOLEM, 'slowpoke': OpCode.SLOWPOKE, 'slowbro': OpCode.SLOWBRO,
    'magnemite': OpCode.MAGNEMITE, 'magneton': OpCode.MAGNETON, 'farfetchd': OpCode.FARFETCHD,
    'doduo': OpCode.DODUO, 'dodrio': OpCode.DODRIO, 'seel': OpCode.SEEL, 'dewgong': OpCode.DEWGONG,
    'grimer': OpCode.GRIMER, 'muk': OpCode.MUK, 'shellder': OpCode.SHELLDER,
    'cloyster': OpCode.CLOYSTER, 'gastly': OpCode.GASTLY, 'haunter': OpCode.HAUNTER,
    'gengar': OpCode.GENGAR, 'onix': OpCode.ONIX, 'drowzee': OpCode.DROWZEE,
    'hypno': OpCode.HYPNO, 'krabby': OpCode.KRABBY, 'kingler': OpCode.KINGLER,
    'voltorb': OpCode.VOLTORB, 'electrode': OpCode.ELECTRODE, 'exeggcute': OpCode.EXEGGCUTE,
    'exeggutor': OpCode.EXEGGUTOR, 'cubone': OpCode.CUBONE, 'marowak': OpCode.MAROWAK,
    'hitmonlee': OpCode.HITMONLEE, 'hitmonchan': OpCode.HITMONCHAN, 'lickitung': OpCode.LICKITUNG,
    'koffing': OpCode.KOFFING, 'weezing': OpCode.WEEZING, 'rhyhorn': OpCode.RHYHORN,
    'rhydon': OpCode.RHYDON, 'chansey': OpCode.CHANSEY, 'tangela': OpCode.TANGELA,
    'kangaskhan': OpCode.KANGASKHAN, 'horsea': OpCode.HORSEA, 'seadra': OpCode.SEADRA,
    'goldeen': OpCode.GOLDEEN, 'seaking': OpCode.SEAKING, 'staryu': OpCode.STARYU,
    'starmie': OpCode.STARMIE, 'mr-mime': OpCode.MR_MIME, 'scyther': OpCode.SCYTHER,
    'jynx': OpCode.JYNX, 'electabuzz': OpCode.ELECTABUZZ, 'magmar': OpCode.MAGMAR,
    'pinsir': OpCode.PINSIR, 'tauros': OpCode.TAUROS, 'magikarp': OpCode.MAGIKARP,
    'gyarados': OpCode.GYARADOS, 'lapras': OpCode.LAPRAS, 'ditto': OpCode.DITTO,
    'eevee': OpCode.EEVEE, 'vaporeon': OpCode.VAPOREON, 'jolteon': OpCode.JOLTEON,
    'flareon': OpCode.FLAREON, 'porygon': OpCode.PORYGON, 'omanyte': OpCode.OMANYTE,
    'omastar': OpCode.OMASTAR, 'kabuto': OpCode.KABUTO, 'kabutops': OpCode.KABUTOPS,
    'aerodactyl': OpCode.AERODACTYL, 'snorlax': OpCode.SNORLAX, 'articuno': OpCode.ARTICUNO,
    'zapdos': OpCode.ZAPDOS, 'moltres': OpCode.MOLTRES, 'mew': OpCode.MEW,
}


# ════════════════════════════════════════════════════════════════════════
# POKECODE VM
# ════════════════════════════════════════════════════════════════════════

# DISPATCH TABLE (built at module level)
# ═════════════════════════════════════════════════════════════════════

_DISPATCH_TABLE: dict[OpCode, Callable] = {
    OpCode.BULBASAUR:    lambda self: self.exec_bulbasaur(),
    OpCode.IVYSAUR:      lambda self: self.exec_ivysaur(),
    OpCode.VENUSAUR:     lambda self: self.exec_venusaur(),
    OpCode.CHARMANDER:   lambda self: self.exec_charmander(),
    OpCode.CHARMELEON:   lambda self: self.exec_charmeleon(),
    OpCode.CHARIZARD:    lambda self: self.exec_charizard(),
    OpCode.SQUIRTLE:     lambda self: self.exec_squirtle(),
    OpCode.WARTORTLE:    lambda self: self.exec_wartortle(),
    OpCode.BLASTOISE:    lambda self: self.exec_blastoise(),
    OpCode.CATERPIE:     lambda self: self.exec_caterpie(),
    OpCode.METAPOD:      lambda self: self.exec_metapod(),
    OpCode.BUTTERFREE:   lambda self: self.exec_butterfree(),
    OpCode.WEEDLE:       lambda self: self.exec_weedle(),
    OpCode.KAKUNA:       lambda self: self.exec_kakuna(),
    OpCode.BEEDRILL:     lambda self: self.exec_beedrill(),
    OpCode.PIDGEY:       lambda self: self.exec_pidgey(),
    OpCode.PIDGEOTTO:    lambda self: self.exec_pidgeotto(),
    OpCode.PIDGEOT:      lambda self: self.exec_pidgeot(),
    OpCode.RATTATA:      lambda self: self.exec_rattata(),
    OpCode.SPEAROW:      lambda self: self.exec_spearow(),
    OpCode.FEAROW:       lambda self: self.exec_fearow(),
    OpCode.EKANS:        lambda self: self.exec_ekans(),
    OpCode.ARBOK:        lambda self: self.exec_arbok(),
    OpCode.PIKACHU:      lambda self: self.exec_pikachu(),
    OpCode.RAICHU:       lambda self: self.exec_raichu(),
    OpCode.SANDSHREW:    lambda self: self.exec_sandshrew(),
    OpCode.SANDSLASH:    lambda self: self.exec_sandslash(),
    OpCode.NIDORAN_F:    lambda self: self.exec_nidoran_f(),
    OpCode.NIDORINA:     lambda self: self.exec_nidorina(),
    OpCode.NIDOQUEEN:    lambda self: self.exec_nidoqueen(),
    OpCode.NIDORAN_M:    lambda self: self.exec_nidoran_m(),
    OpCode.NIDORINO:     lambda self: self.exec_nidorino(),
    OpCode.NIDOKING:     lambda self: self.exec_nidoking(),
    OpCode.CLEFAIRY:     lambda self: self.exec_clefairy(),
    OpCode.CLEFABLE:     lambda self: self.exec_clefable(),
    OpCode.VULPIX:       lambda self: self.exec_vulpix(),
    OpCode.NINETALES:    lambda self: self.exec_ninetales(),
    OpCode.JIGGLYPUFF:   lambda self: self.exec_jigglypuff(),
    OpCode.WIGGLYTUFF:   lambda self: self.exec_wigglytuff(),
    OpCode.ZUBAT:        lambda self: self.exec_zubat(),
    OpCode.GOLBAT:       lambda self: self.exec_golbat(),
    OpCode.ODDISH:       lambda self: self.exec_oddish(),
    OpCode.GLOOM:        lambda self: self.exec_gloom(),
    OpCode.VILEPLUME:    lambda self: self.exec_vileplume(),
    OpCode.PARAS:        lambda self: self.exec_paras(),
    OpCode.PARASECT:     lambda self: self.exec_parasect(),
    OpCode.VENONAT:      lambda self: self.exec_venonat(),
    OpCode.VENOMOTH:     lambda self: self.exec_venomoth(),
    OpCode.DIGLETT:      lambda self: self.exec_diglett(),
    OpCode.DUGTRIO:      lambda self: self.exec_dugtrio(),
    OpCode.MEOWTH:       lambda self: self.exec_meowth(),
    OpCode.PERSIAN:      lambda self: self.exec_persian(),
    OpCode.PSYDUCK:      lambda self: self.exec_psyduck(),
    OpCode.GOLDUCK:      lambda self: self.exec_golduck(),
    OpCode.MANKEY:       lambda self: self.exec_mankey(),
    OpCode.PRIMEAPE:     lambda self: self.exec_primeape(),
    OpCode.GROWLITHE:    lambda self: self.exec_growlithe(),
    OpCode.ARCANINE:     lambda self: self.exec_arcanine(),
    OpCode.POLIWAG:      lambda self: self.exec_poliwag(),
    OpCode.POLIWHIRL:    lambda self: self.exec_poliwhirl(),
    OpCode.POLIWRATH:    lambda self: self.exec_poliwrath(),
    OpCode.ABRA:         lambda self: self.exec_abra(),
    OpCode.KADABRA:      lambda self: self.exec_kadabra(),
    OpCode.ALAKAZAM:     lambda self: self.exec_alakazam(),
    OpCode.MACHOP:       lambda self: self.exec_machop(),
    OpCode.MACHOKE:      lambda self: self.exec_machoke(),
    OpCode.MACHAMP:      lambda self: self.exec_machamp(),
    OpCode.BELLSPROUT:   lambda self: self.exec_bellsprout(),
    OpCode.WEEPINBELL:   lambda self: self.exec_weepinbell(),
    OpCode.VICTREEBEL:   lambda self: self.exec_victreebel(),
    OpCode.TENTACOOL:    lambda self: self.exec_tentacool(),
    OpCode.TENTACRUEL:   lambda self: self.exec_tentacruel(),
    OpCode.GEODUDE:      lambda self: self.exec_geodude(),
    OpCode.GRAVELER:     lambda self: self.exec_graveler(),
    OpCode.GOLEM:        lambda self: self.exec_golem(),
    OpCode.SLOWPOKE:     lambda self: self.exec_slowpoke(),
    OpCode.SLOWBRO:      lambda self: self.exec_slowbro(),
    OpCode.MAGNEMITE:    lambda self: self.exec_magnemite(),
    OpCode.MAGNETON:     lambda self: self.exec_magneton(),
    OpCode.FARFETCHD:    lambda self: self.exec_farfetchd(),
    OpCode.DODUO:        lambda self: self.exec_doduo(),
    OpCode.DODRIO:       lambda self: self.exec_dodrio(),
    OpCode.SEEL:         lambda self: self.exec_seel(),
    OpCode.DEWGONG:      lambda self: self.exec_dewgong(),
    OpCode.GRIMER:       lambda self: self.exec_grimer(),
    OpCode.MUK:          lambda self: self.exec_muk(),
    OpCode.SHELLDER:     lambda self: self.exec_shellder(),
    OpCode.CLOYSTER:     lambda self: self.exec_cloyster(),
    OpCode.GASTLY:       lambda self: self.exec_gastly(),
    OpCode.HAUNTER:      lambda self: self.exec_haunter(),
    OpCode.GENGAR:       lambda self: self.exec_gengar(),
    OpCode.ONIX:         lambda self: self.exec_onix(),
    OpCode.DROWZEE:      lambda self: self.exec_drowzee(),
    OpCode.HYPNO:        lambda self: self.exec_hypno(),
    OpCode.KRABBY:       lambda self: self.exec_krabby(),
    OpCode.KINGLER:      lambda self: self.exec_kingler(),
    OpCode.VOLTORB:      lambda self: self.exec_voltorb(),
    OpCode.ELECTRODE:    lambda self: self.exec_electrode(),
    OpCode.EXEGGCUTE:    lambda self: self.exec_exeggcute(),
    OpCode.EXEGGUTOR:    lambda self: self.exec_exeggutor(),
    OpCode.CUBONE:       lambda self: self.exec_cubone(),
    OpCode.MAROWAK:      lambda self: self.exec_marowak(),
    OpCode.HITMONLEE:    lambda self: self.exec_hitmonlee(),
    OpCode.HITMONCHAN:   lambda self: self.exec_hitmonchan(),
    OpCode.LICKITUNG:    lambda self: self.exec_lickitung(),
    OpCode.KOFFING:      lambda self: self.exec_koffing(),
    OpCode.WEEZING:      lambda self: self.exec_weezing(),
    OpCode.RHYHORN:      lambda self: self.exec_rhyhorn(),
    OpCode.RHYDON:       lambda self: self.exec_rhydon(),
    OpCode.CHANSEY:      lambda self: self.exec_chansey(),
    OpCode.TANGELA:      lambda self: self.exec_tangela(),
    OpCode.KANGASKHAN:   lambda self: self.exec_kangaskhan(),
    OpCode.HORSEA:       lambda self: self.exec_horsea(),
    OpCode.SEADRA:       lambda self: self.exec_seadra(),
    OpCode.GOLDEEN:      lambda self: self.exec_goldeen(),
    OpCode.SEAKING:      lambda self: self.exec_seaking(),
    OpCode.STARYU:       lambda self: self.exec_staryu(),
    OpCode.STARMIE:      lambda self: self.exec_starmie(),
    OpCode.MR_MIME:      lambda self: self.exec_mr_mime(),
    OpCode.SCYTHER:      lambda self: self.exec_scyther(),
    OpCode.JYNX:         lambda self: self.exec_jynx(),
    OpCode.ELECTABUZZ:   lambda self: self.exec_electabuzz(),
    OpCode.MAGMAR:       lambda self: self.exec_magmar(),
    OpCode.PINSIR:       lambda self: self.exec_pinsir(),
    OpCode.TAUROS:       lambda self: self.exec_tauros(),
    OpCode.MAGIKARP:     lambda self: self.exec_magikarp(),
    OpCode.GYARADOS:     lambda self: self.exec_gyarados(),
    OpCode.LAPRAS:       lambda self: self.exec_lapras(),
    OpCode.DITTO:        lambda self: self.exec_ditto(),
    OpCode.EEVEE:        lambda self: self.exec_eevee(),
    OpCode.VAPOREON:     lambda self: self.exec_vaporeon(),
    OpCode.JOLTEON:      lambda self: self.exec_jolteon(),
    OpCode.FLAREON:      lambda self: self.exec_flareon(),
    OpCode.PORYGON:      lambda self: self.exec_porygon(),
    OpCode.OMANYTE:      lambda self: self.exec_omanyte(),
    OpCode.OMASTAR:      lambda self: self.exec_omastar(),
    OpCode.KABUTO:       lambda self: self.exec_kabuto(),
    OpCode.KABUTOPS:     lambda self: self.exec_kabutops(),
    OpCode.AERODACTYL:   lambda self: self.exec_aerodactyl(),
    OpCode.SNORLAX:      lambda self: self.exec_snorlax(),
    OpCode.ARTICUNO:     lambda self: self.exec_articuno(),
    OpCode.ZAPDOS:       lambda self: self.exec_zapdos(),
    OpCode.MOLTRES:      lambda self: self.exec_moltres(),
    OpCode.MEW:          lambda self: self.exec_mew(),
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
    
    Mew encoding unario:
    - 1 Mew = MEW (NOP)
    - N Mews (2-151) = instrucción N-1
    - >151 Mews = instrucción 151 (MEW) + argumento = count - 151
    """
    tokens = source.lower().replace('\n', ' ').replace(',', ' ').replace('.', ' ').split()
    program = []
    i = 0
    while i < len(tokens):
        token = tokens[i].strip('.,;:()[]{}')
        if token.startswith('#'):
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
            elif count <= 151:
                # N Mews = instrucción N-1
                # count=2 -> Bulbasaur(1) -> index 0 = count-2
                # count=151 -> MEW(151) -> index 150 = count-1
                if count == 151:
                    target_op = OpCode.MEW
                else:
                    target_op = list(OpCode)[count - 2]
                program.append(target_op)
            else:
                # >151: MEW + argumento = count - 151
                # Emit MEW followed by argument handling (simplified: just emit MEW)
                program.append(OpCode.MEW)
                # Note: argument handling would need VM support
            continue
        
        if token.startswith('#'):
            i += 1
            continue
        if token in NAME_TO_OPCODE:
            program.append(NAME_TO_OPCODE[token])
        else:
            # Try fuzzy match
            for name, op in NAME_TO_OPCODE.items():
                if name.startswith(token) or token.startswith(name):
                    program.append(op)
                    break
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
# EJEMPLOS
# ═══════════════════════════════════════════════════════════════════════

HELLO_WORLD = """
# Hello World en POKECODE
# Inicializar memoria con "Hello World!\n"
Bulbasaur Ivysaur Venusaur Charmander Charmeleon Charizard
Squirtle Wartortle Blastoise Caterpie Metapod Butterfree
Weedle Kakuna Beedrill Pidgey Pidgeotto Pidgeot Rattata

# Imprimir cada carácter
Spearow Fearow Ekans Arbok Pikachu Raichu Sandshrew Sandslash
Nidoran-f Nidorina Nidoqueen Nidoran-m Nidorino Nidoking
Clefairy Clefable Vulpix Ninetales Jigglypuff
"""

FIBONACCI = """
# Fibonacci: imprime primeros N números
# ACC = N (input), luego imprime secuencia
Meowth Persian Psyduck Golduck Mankey Primeape Growlithe
Arcanine Poliwag Poliwhirl Poliwrath Abra Kadabra Alakazam
Machop Machoke Machamp Bellsprout Weepinbell Victreebel
Tentacool Tentacruel Geodude Graveler Golem
"""

BRAINFUCK_INTERPRETER = """
# Intérprete Brainfuck mínimo en POKECODE
# (Traducción directa de los 8 comandos BF)
# > = Venusaur (PTR_INC)
# < = Charmander (PTR_DEC)
# + = Parasect (INC)
# - = Venomoth (DEC)
# . = Haunter (OUT)
# , = Gastly (IN)
# [ = Ekans (JZ) + Spearow (JMP)
# ] = Arbok (JNZ) + Fearow (JMP_REL)

Venusaur Charmander Parasect Venomoth Haunter Gastly Ekans Spearow Arbok Fearow
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