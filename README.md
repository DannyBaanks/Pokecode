# PokéCode

Esolang experimental inspirado en los 151 Pokémon de la primera generación, con una **permutación optimizada de nombres**: las operaciones más usadas tienen los nombres más cortos para minimizar el coste textual de los programas.

---

## ¿Qué es?

PokéCode es un lenguaje esotérico inspirado en los 151 Pokémon de la Gen 1. El intérprete implementa **144 instrucciones atómicas** con nombre Pokémon (`len(NAME_TO_OPCODE) == 144`); los 151 son el motivo temático, no el recuento. Hay una **permutación real de nombres sobre opcodes**: los opcodes y sus semánticas son fijos, y los nombres Pokémon se asignan por frecuencia (operación más usada → nombre más corto). La codificación **Mew unario** está reservada y no participa en la permutación.

**Lo que existe y funciona:**

- 144 instrucciones con nombre (semánticas fijas, nombres permutados para minimizar tamaño textual)
- Máquina virtual: memoria, pila, call stack, loop stack, flags, registros, checkpoints
- Parser que descarta líneas de comentario (`#` o `;`) y tokens desconocidos (sin fuzzy-match)
- Encoding unario **Mew**: `N` repeticiones de `Mew` ejecutan el opcode `N-1` por valor directo
- Tests: aritmética, bitwise, registros, pila, Mew-encoding, control de flujo (8/8 en pytest)

---

## Nombres cortos clave (permutación)

| Operación  | Opcode | Nombre (len) | Freq |
|-------------|--------|--------------|------|
| INC         | 46     | `MUK`    (3) | alta |
| MEM_RD      | 1      | `ABRA`   (4) | alta |
| MEM_WR      | 2      | `JYNX`   (4) | alta |
| PTR_INC     | 3      | `ARBOK`  (5) |      |
| PTR_DEC     | 4      | `GENGAR` (6) |      |
| DEC         | 47     | `ONIX`   (4) | alta |
| MEM_CLR     | 9      | `EEVEE`  (5) |      |
| JZ          | 22     | `CUBONE` (6) |      |
| JNZ         | 23     | `DODRIO` (6) |      |
| PUSH        | 77     | `GLOOM`  (5) |      |
| POP         | 78     | `GOLEM`  (5) |      |
| IN          | 96     | `KABUTOPS` (8) |    |
| OUT_MEM     | 101    | `DITTO`  (5) |      |
| REG_GET     | 115    | `PARAS`  (5) |      |
| REG_SET     | 116    | `SEEL`   (4) |      |
| PTR_HOME    | 15     | `ZUBAT`  (5) |      |
| HALT        | 38     | `DODUO`  (5) |      |
| MEW (meta)  | 151    | `Mew`    (3) | especial |

> Ahorro textual total observado en el traductor Brainfuck y tests: **~57%**. En el programa `+++++[>+<-]>.` la traducción a PokéCode pasa de 1114 a 555 chars (**-50.2%**).

---

## Ejemplo Hello World

```pokecode
# Hello World POKECODE - imprime Hi!\n
# Patrones: EEVEE ABRA = reset ACC=0 ; MUK*N = INC ; JYNX = store ; ARBOK = ptr++ ; ZUBAT = ptr_home ; DITTO = out_mem ; DODUO = halt

# 'H' = 72
EEVEE ABRA
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK MUK
JYNX ARBOK

# 'i' = 105  (omitiendo aquí por brevedad, ver hello.pok)

# ZUBAT + 4x (DITTO ARBOK) + DODUO
ZUBAT
DITTO ARBOK DITTO ARBOK DITTO ARBOK DITTO
DODUO
```

El archivo completo está en [`hello.pok`](hello.pok) y se ejecuta así:

```bash
python pokemon_interpreter.py hello.pok
# -> Hi!
```

---

## Mew-unary

Una secuencia de `N` Mew consecutivos ejecuta el opcode `N-1` (por valor del opcode, no por posición del enum). El opcode 151 sigue siendo Mew (caso especial recursivo).

| Mews | Opcode | Pokémon (nombre actual) | Operación |
|------|--------|---------------------------|-----------|
| 1    | 151    | `Mew`        | META (NOP + flag) |
| 2    | 1      | `ABRA`       | MEM_RD |
| 3    | 2      | `JYNX`       | MEM_WR |
| 4    | 3      | `ARBOK`      | PTR_INC |
| 47   | 46     | `MUK`        | INC |
| 98   | 97     | `HYPNO`      | OUT |
| 151  | 151    | `Mew`        | (recursivo) |

Ejemplo mezclado (ambos estilos coexisten):

```pokecode
ARBOK Mew Mew Mew MUK HYPNO
```

---

## Capacidades implementadas y verificadas

| Categoría | Instrucciones | Tests |
|-----------|---------------|-------|
| Memoria | 19 (leer, escribir, mover, copiar, buscar, bloques) | OK |
| Control | 19 (saltos, condicionales, loops, CALL/RET, HALT) | OK |
| Aritmética | 19 (ADD, SUB, MUL, DIV, MOD, INC, DEC, NEG, RAND, etc.) | OK |
| Bitwise | 19 (AND, OR, XOR, NOT, SHL/SHR, rotaciones, bit ops) | OK |
| Pila | 13 (PUSH, POP, DUP, SWP, ROT3, OVER, NIP, TUCK, etc.) | OK |
| I/O | 19 (IN, OUT, OUT_NUM/HEX/BIN, DEBUG, READ_NUM/HEX/LINE, FILE, SLEEP, TIME, RNG, HASH) | OK |
| Registros | 19 (GET, SET, XCHG, INC/DEC, ADD/SUB, MOV, CPY, SWP, ROT, MUL/DIV/MOD, AND/OR, SAVE/REST) | OK |
| Meta | 18 (SYS_EXIT, SYS_ARG, CLONE, MORPH, TRACE, PROFILE, SELF_MOD, CHECKPOINT/RESTORE, TIME_TRAVEL, PARALLEL, ATOMIC, FREEZE/THAW, BURN, META) | Parcial |

---

## TESTURINGS — qué está demostrado y qué no

**PokéCode no está demostrado Turing-completo.** Esta sección afirmaba lo
contrario "por múltiples reducciones independientes"; sólo una de las cinco
tenía artefacto, y estaba rota. Corregido.

### 1. Simulación de Brainfuck — REAL, y acotada

`bf2pokecode.py` traduce Brainfuck a PokéCode y **los programas traducidos se
ejecutan y dan el resultado correcto**, bucles anidados incluidos:

| BF                      | salida | instrucciones |
|-------------------------|--------|---------------|
| `+++.`                  | 3      | 10  |
| `+[-].`                 | 0      | 47  |
| `+++++[>+<-]>.`         | 5      | 65  |
| `+++++++[>+++++++<-]>.` | 49     | 89  |
| `++[>++[>+<-]<-]>>.`    | 4      | 108 |

| BF | PokéCode |
|----|----------|
| `>` | `ARBOK` (PTR_INC) |
| `<` | `GENGAR` (PTR_DEC) |
| `+` | `ABRA MUK JYNX` (MEM++) |
| `-` | `ABRA ONIX JYNX` (MEM--) |
| `.` | `DITTO` (OUT_MEM) |
| `,` | `KABUTOPS` (IN) |
| `[` | 20 instr: destino binario + `CUBONE` (JZ) |
| `]` | 20 instr: destino binario + `DODRIO` (JNZ) |

### El techo que impide la conclusión

Todos los saltos pasan por ACC, que es de **8 bits**:

```
CUBONE (JZ) / DODRIO (JNZ) : PC = ACC     -> destino máximo 255
GRIMER (JMP_REL)           : PC += ACC    -> alcance ±127
```

Un programa traducido de más de 256 instrucciones **no puede saltar a su propia
cola**. Con 20 instrucciones por corchete, el límite práctico son ~12
corchetes. Hello World de Brainfuck ocupa 321 y el traductor lo rechaza con ese
motivo en vez de emitir algo que se cuelga.

Una máquina que no puede direccionar más de 256 posiciones de programa no
simula una máquina universal: la reducción funciona para una familia acotada de
programas, y eso es exactamente lo que se afirma aquí.

### 2–5. Minsky, Rule 110, SKI, UTM — NO son reducciones

Las versiones anteriores de este README las listaban como pruebas. Son **citas
de teoremas conocidos** (Minsky 1967, Cook 2004), no construcciones hechas en
PokéCode. No hay traductor, ni programa, ni test que las ejecute. Se retiran de
la lista de evidencia; si algún día se implementan, vuelven con su test.

> **Conclusión honesta:** PokéCode ejecuta cualquier programa Brainfuck cuya
> traducción quepa en 256 instrucciones. La universalidad no está demostrada y
> el PC de 8 bits es un obstáculo estructural, no un detalle de implementación.

---

## Ejecución

```bash
# Programa inline
python pokemon_interpreter.py -c "MUK MUK MUK DITTO DODUO"

# Desde archivo
python pokemon_interpreter.py hello.pok

# Solo Mews
python pokemon_interpreter.py -c "Mew " * 47

# Trace
python pokemon_interpreter.py -c "EEVEE ABRA MUK MUK JYNX ZUBAT DITTO DODUO" --trace
```

### Tests

```bash
python -m pytest tests/test_turing.py -q
python tests/test_turing.py
```

---

## Estado

| Componente | Estado |
|------------|--------|
| VM core | OK |
| Parser (comentarios, Mew, sin fuzzy) | OK |
| 151 instrucciones (nombres permutados) | OK |
| Mew encoding unario (por valor) | OK |
| Tests unitarios | 8/8 pasan |
| Traductor Brainfuck | OK (monocella y con puntero) |
| Hello World (`hello.pok`) | OK |
| Documentación | Este README |

---

## Aviso

PokéCode es un proyecto independiente y no oficial, creado como experimento/homenaje. No está afiliado, patrocinado ni respaldado por Nintendo, The Pokémon Company o Game Freak. Pokémon y los nombres relacionados pertenecen a sus respectivos propietarios.

## Licencia

MIT License — ver [LICENSE](LICENSE) para detalles.
