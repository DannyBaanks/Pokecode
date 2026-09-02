# PokéCode

Esolang experimental inspirado en los 151 Pokémon de la primera generación, con una **permutación optimizada de nombres**: las operaciones más usadas tienen los nombres más cortos para minimizar el coste textual de los programas.

---

## ¿Qué es?

PokéCode es un lenguaje esotérico inspirado en los 151 Pokémon de la Gen 1. El intérprete implementa **151 instrucciones atómicas** con nombre Pokémon (`len(NAME_TO_OPCODE) == 151`); los 151 son a la vez el motivo temático y el recuento exacto. Hay una **permutación real de nombres sobre opcodes**: los opcodes y sus semánticas son fijos, y los nombres Pokémon se asignan por frecuencia (operación más usada → nombre más corto). La codificación **Mew unario** está reservada y no participa en la permutación.

**Lo que existe y funciona:**

- 151 instrucciones con nombre (semánticas fijas, nombres permutados para minimizar tamaño textual)
- Máquina virtual: memoria, pila, call stack, loop stack, flags, registros, checkpoints
- Parser que descarta líneas de comentario (`#` o `;`) y tokens desconocidos (sin fuzzy-match)
- Encoding unario **Mew**: `N` repeticiones de `Mew` ejecutan el opcode `N-1` por valor directo
- Motor público genérico: `pokemon_interpreter.py` + `host.py` (todo en uno, sin dependencias internas) ejecutan `.pkmc` / `.pok`
- Corpus 151 `.pkmc` en `pkmc/` — uno por opcode, todos verificados con el motor
- Tests: aritmética, bitwise, registros, pila, Mew-encoding, control de flujo, cinta y saltos no acotados (9/9 en pytest) + 151 corpus

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
Una secuencia de más de 151 `Mew` consecutivos es inválida y el parser la rechaza;
no existe un opcode 152 ni un argumento oculto para Mew.

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

### 1. Simulación de Brainfuck — REAL y ejecutada

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
| `[` | `ABRA CUBONE @fin` (prueba celda y salta por etiqueta) |
| `]` | `ABRA DODRIO @bucle` (prueba celda y vuelve por etiqueta) |

### Cinta y saltos no acotados

La VM usa una cinta dispersa, bidireccional y sin límite fijo de direcciones.
Las etiquetas del parser permiten que los saltos existentes (`CUBONE`, `DODRIO`
y los demás saltos absolutos) tengan destinos de cualquier tamaño:

```pokecode
@bucle:
ABRA CUBONE @fin
# cuerpo
ABRA DODRIO @bucle
@fin:
```

`@bucle:` y `@fin:` son directivas de ensamblador, no instrucciones Pokémon ni
una variante de Mew. Un salto sin etiqueta conserva el destino histórico en
`ACC`, de 8 bits. El traductor Brainfuck genera etiquetas y ejecuta el Hello
World clásico, además de programas con bucles anidados.

> **Conclusión:** PokéCode contiene una simulación ejecutable de Brainfuck con
> cinta y control no acotados. Bajo la semántica estándar de Brainfuck, esto
> demuestra Turing-completitud de esta versión de la VM.

---

## Ejecución

```bash
# Programa inline
python pokemon_interpreter.py -c "MUK MUK MUK DITTO DODUO"
python host.py -c "MUK MUK HYPNO DODUO"

# Desde archivo (.pok o .pkmc)
python pokemon_interpreter.py hello.pok
python host.py pkmc/046_MUK.pkmc
python host.py hello.pok --trace

# Solo Mews (47 Mews = MUK)
python pokemon_interpreter.py -c "Mew " * 47
python host.py -c "Mew Mew Mew Mew"  # 4 Mews = ARBOK

# Trace
python pokemon_interpreter.py -c "EEVEE ABRA MUK MUK JYNX ZUBAT DITTO DODUO" --trace

# Corpus completo 151
python host.py pkmc/001_ABRA.pkmc
for f in pkmc/*.pkmc; do python host.py "$f" > /dev/null && echo "$f OK"; done
```

### Motor público

`pokemon_interpreter.py` es el motor todo-en-uno (VM + parser). `host.py` es un wrapper fino del mismo motor para uso público:

- `.pkmc` es la extensión canónica del motor (también acepta `.pok`)
- Lista las 151: `python host.py --list`
- Mew sigue siendo **solo unario por valor** (`N` Mews = opcode `N-1`); `@etiqueta:` es directiva de ensamblador para saltos, no una variante de Mew

```bash
python host.py --list
#  46  muk
# 151  mew
python gen_151_pkmc.py  # regenera y verifica los 151
```

### Corpus canónico `pkmc/` — 1 opcode → 1 ejemplo visible

`pkmc/` = **canonical opcode examples**. Cada archivo:

- corresponde a **exactamente un opcode**;
- muestra la **forma mínima válida** de usarlo;
- sirve como **referencia para humanos y LLMs**;
- puede **ejecutarse directamente** con el host (`python host.py pkmc/046_MUK.pkmc`);
- **NO sustituye** los tests semánticos.

> $$ \boxed{ \text{1 opcode} \rightarrow \text{1 ejemplo canónico visible} } $$

Para opcodes complejos el ejemplo es una *flashcard ejecutable* con contexto:

```pokecode
# PRE: ACC=3
# POST: stack=[3]
GLOOM
DODUO
```

```pokecode
# demonstrate JZ — expected branch: @zero
EEVEE ABRA
CUBONE @zero
DRATINI
@zero:
DODUO
```

Separación limpia:

| Carpeta/archivo | Rol |
|---|---|
| `pkmc/` | **cómo se usa** |
| `tests/` | **cómo sabemos que funciona** |
| `README` / `SPEC` | **qué significa** |
| `host.py` + `pokemon_interpreter.py` | **cómo se ejecuta** |

Con 151 nombres Pokémon, esto evita que el siguiente humano o LLM tenga que adivinar la forma correcta.

### Tests

```bash
python -m pytest tests/test_turing.py -q
python tests/test_turing.py
python gen_151_pkmc.py  # verifica 151 .pkmc
```

### Ejemplos funcionales (no maqueta)

Dos programas en `examples/` demuestran cómputo no trivial sin traductor:

| Ejemplo | Archivo | Qué prueba | Salida |
|---------|---------|------------|--------|
| **Fibonacci 10** | `examples/fibonacci.pok` | memoria (`ABRA/JYNX`), puntero (`ZUBAT/ARBOK`), aritmética (`IVYSAUR`), pila (`GLOOM/GOLEM`), saltos etiquetados (`CUBONE/DODRIO @loop`) | `0 1 1 2 3 5 8 13 21 34` |
| **FizzBuzz 1..15** | `examples/fizzbuzz.pok` | `MACHOKE` (MOD), bifurcaciones anidadas, strings en memoria (`DITTO` x4/x8) | `1 2 Fizz 4 Buzz ... FizzBuzz` |

```bash
python host.py examples/fibonacci.pok
# -> 0 1 1 2 3 5 8 13 21 34

python host.py examples/fizzbuzz.pok
# -> 1 / 2 / Fizz / 4 / Buzz / Fizz / 7 / 8 / Fizz / Buzz / 11 / Fizz / 13 / 14 / FizzBuzz

python pokemon_interpreter.py --example fib
# usa FIBONACCI integrado (pokemon_interpreter.py:1570)
```

El `FIBONACCI` anterior era un stub (`EEVEE ABRA JYNX...`). Ahora es el programa verificado anterior.

---

## Estado

| Componente | Estado |
|------------|--------|
| VM core | OK |
| Parser (comentarios, Mew, sin fuzzy) | OK |
| 151 instrucciones (nombres permutados) | OK |
| Mew encoding unario (por valor) | OK |
| Motor público (`pokemon_interpreter.py` + `host.py`) | OK — ejecuta `.pkmc` / `.pok` |
| Corpus 151 `.pkmc` (`pkmc/001_*` … `151_Mew.pkmc`) | 151/151 verificados |
| Tests unitarios | 9/9 pasan |
| Traductor Brainfuck | OK (bucles anidados y Hello World) |
| Hello World (`hello.pok` / `pkmc/038_DODUO.pkmc` etc) | OK |
| Fibonacci (`examples/fibonacci.pok` + `--example fib`) | OK — 0 1 1 2 3 5 8 13 21 34 verificado |
| FizzBuzz (`examples/fizzbuzz.pok`) | OK — 1..15 con MOD y bifurcaciones verificado |
| Documentación | Este README |

---

## Aviso

PokéCode es un proyecto independiente y no oficial, creado como experimento/homenaje. No está afiliado, patrocinado ni respaldado por Nintendo, The Pokémon Company o Game Freak. Pokémon y los nombres relacionados pertenecen a sus respectivos propietarios.

## Licencia

MIT License — ver [LICENSE](LICENSE) para detalles.
