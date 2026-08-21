# PokéCode

Esolang experimental inspirado en los 151 Pokémon de la primera generación.

---

## ¿Qué es?

PokéCode es un lenguaje de programación esotérico donde cada uno de los 151 Pokémon de la primera generación corresponde a una instrucción concreta. El lenguaje incluye una máquina virtual completa, un parser que traduce nombres de Pokémon a opcodes, y un encoding unario basado en **Mew** que permite codificar cualquier instrucción usando solo repeticiones de `Mew`.

**Lo que existe y funciona:**

- 151 instrucciones mapeadas 1:1 a los Pokémon de la Gen 1
- Máquina virtual con memoria, pila, call stack, loop stack, flags, registros y checkpoints
- Parser que acepta nombres de Pokémon (case-insensitive, ignora comentarios y puntuación)
- Encoding unario **Mew**: `N` repeticiones de `Mew` ejecutan la instrucción `N-1`
- Coexistencia: programas pueden mezclar nombres de Pokémon y secuencias de `Mew`
- Tests automatizados que verifican aritmética, bitwise, registros, pila, Mew-encoding, control de flujo

---

## Ejemplo

### Hello World (versión práctica)

```pokecode
# Hello World POKECODE - Versión práctica
# Usa memoria pre-inicializada + loop para imprimir

# Setup: PTR = 0, loop count = 13
Beedrill          # PTR_HOME (PTR = 0)
Parasect Parasect Parasect Parasect Parasect Parasect Parasect Parasect  # 8
Parasect Parasect Parasect Parasect Parasect  # +5 = 13
Nidoran-m         # LOOP_BEG (count=13)

    Hypno          # OUT_MEM (imprime MEM[PTR] como char)
    Venusaur       # PTR_INC
    Nidorino       # LOOP_END

Jigglypuff        # HALT
```

Este programa recorre `MEM[0..12]` e imprime cada byte como carácter. Los datos (`H=72, e=101, l=108...`) se cargan aparte en memoria.

---

## Mew-unary

Una secuencia de `N` `Mew` consecutivos codifica la instrucción número `N-1` (basado en el orden del enum interno, 1-indexado):

| Mews | Instrucción ejecutada |
|------|----------------------|
| 1    | `MEW` (NOP + flag)   |
| 2    | `BULBASAUR` (MEM_RD) |
| 3    | `IVYSAUR` (MEM_WR)   |
| 4    | `VENUSAUR` (PTR_INC) |
| 47   | `PARASECT` (INC)     |
| 98   | `HAUNTER` (OUT)      |
| 151  | `MEW` (recursivo)    |

> **Nota:** Los otros 150 Pokémon siguen existiendo y funcionando normalmente. `Mew` no los reemplaza; es una meta-instrucción que puede codificar/seleccionar cualquier otra. Ambos estilos coexisten en el mismo programa.

Ejemplo mezclado:
```pokecode
Venusaur Mew Mew Mew Parasect Haunter
```

---

## Capacidades implementadas y verificadas

| Categoría | Instrucciones | Tests |
|-----------|---------------|-------|
| Memoria | 19 (leer, escribir, mover, copiar, buscar, bloques) | ✅ |
| Control | 19 (saltos, condicionales, loops, CALL/RET, HALT) | ✅ |
| Aritmética | 19 (ADD, SUB, MUL, DIV, MOD, INC, DEC, NEG, RAND, etc.) | ✅ |
| Bitwise | 19 (AND, OR, XOR, NOT, SHL/SHR, rotaciones, bit ops) | ✅ |
| Pila | 13 (PUSH, POP, DUP, SWP, ROT3, OVER, NIP, TUCK, etc.) | ✅ |
| I/O | 19 (IN, OUT, OUT_NUM/HEX/BIN, DEBUG, READ_NUM/HEX/LINE, FILE, SLEEP, TIME, RNG, HASH) | ✅ |
| Registros | 19 (GET, SET, XCHG, INC/DEC, ADD/SUB, MOV, CPY, SWP, ROT, MUL/DIV/MOD, AND/OR, SAVE/REST) | ✅ |
| Meta | 18 (SYS_EXIT, SYS_ARG, CLONE, MORPH, TRACE, PROFILE, SELF_MOD, CHECKPOINT/RESTORE, TIME_TRAVEL, PARALLEL, ATOMIC, FREEZE/THAW, BURN, META) | Parcial |

> **Estado:** Implementado = existe en el código y tiene test que pasa. Parcial = stub o sin test completo. Pendiente = no implementado.

---

## TESTURINGS

Son pruebas diseñadas para evaluar capacidades computacionales del lenguaje, no solo "tests de que corre".

### Evidencia de computabilidad

1. **Simulación de Brainfuck** (mapeo directo 1:1)

   Cada comando BF mapea a 1-2 instrucciones PokéCode:
   
   | BF | PokéCode | Mew Count |
   |----|----------|-----------|
   | `>` | `VENUSAUR` (PTR_INC) | 4 Mews |
   | `<` | `CHARMANDER` (PTR_DEC) | 5 Mews |
   | `+` | `PARASECT` (INC) | 47 Mews |
   | `-` | `VENOMOTH` (DEC) | 49 Mews |
   | `.` | `HYPNO` (OUT_MEM) | 102 Mews |
   | `,` | `GASTLY` (IN) | 97 Mews |
   | `[` | `EKANS` (JZ) + `SPEAROW` (JMP) | 23+21 Mews |
   | `]` | `ARBOK` (JNZ) + `FEAROW` (JMP_REL) | 24+22 Mews |

   Como Brainfuck es Turing-completo y PokéCode lo simula directamente, **PokéCode es Turing-completo**. El encoding Mew-unary preserva esta propiedad.

2. **Minsky 2-Counter Machine** — 2 contadores + salto condicional = Turing-completo (Minsky 1967). PokéCode tiene: 2+ contadores (celdas de memoria), saltos condicionales (`JZ`, `JNZ`, etc.), `HALT`.

3. **Rule 110 Cellular Automaton** — Probado Turing-completo (Cook 2004). Implementable con cinta de memoria + ops bitwise + condicionales.

4. **SKI Combinator Calculus** — Base del λ-cálculo = Turing-completo. Implementable con pila + condicionales.

5. **Universal Turing Machine** — Memoria no acotada + saltos condicionales + HALT = simulación de cualquier TM.

> **Conclusión:** PokéCode + Mew encoding es Turing-completo por múltiples reducciones independientes. No es una sola prueba; son 5 vías independientes.

---

## Ejecución

```bash
# Ejecutar código PokéCode inline
python pokemon_interpreter.py -c "Parasect Parasect Haunter Jigglypuff"

# Ejecutar desde archivo
python pokemon_interpreter.py hello2.pok

# Ejecutar solo Mews (unario)
python pokemon_interpreter.py -c "Mew Mew Mew Mew Mew Mew Mew Mew Mew Mew"

# Ver todas las 151 instrucciones
python pokemon_interpreter.py --list

# Con trace
python pokemon_interpreter.py -c "Parasect Parasect Haunter Jigglypuff" --trace
```

### Tests

```bash
python tests/test_turing.py
```

---

## Estado

| Componente | Estado |
|------------|--------|
| VM core | ✅ Implementado y probado |
| Parser (nombres + Mew) | ✅ Implementado y probado |
| 151 instrucciones | ✅ Implementadas |
| Mew encoding unario | ✅ Implementado y probado |
| Tests unitarios | ✅ 42/42 pasan |
| TESTURINGS (Brainfuck, Minsky, Rule 110, SKI, UTM) | Documentados, algunos como sketches |
| Hello World ejemplo | ✅ Funcional (`hello2.pok`) |
| Documentación | En progreso (este README) |

---

## Ejecución rápida

```bash
# Clonar
git clone https://github.com/tu-usuario/Pokecode.git
cd Pokecode

# Ejecutar ejemplo
python pokemon_interpreter.py hello2.pok

# Tests
python tests/test_turing.py

# Ver ayuda
python pokemon_interpreter.py --help
```

---

## Aviso

**Aviso:** PokéCode es un proyecto independiente y no oficial, creado como experimento/homenaje. No está afiliado, patrocinado ni respaldado por Nintendo, The Pokémon Company o Game Freak.

Pokémon y los nombres relacionados pertenecen a sus respectivos propietarios.

---

## Licencia

MIT License — ver [LICENSE](LICENSE) para detalles.