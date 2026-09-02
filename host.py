#!/usr/bin/env python3
"""
PokéCode Host — motor público genérico, todo en uno.

Ejecuta programas .pkmc / .pok con el mismo VM que usa el intérprete.
No expone infraestructura interna, solo la VM y el parser de PokéCode.

Uso:
  py host.py programa.pkmc
  py host.py -c "MUK MUK HYPNO DODUO"
  py host.py --list
  py host.py programa.pkmc --input "hola"
  py host.py programa.pkmc --trace
"""

from __future__ import annotations

import sys

# Reusa la VM pública del proyecto
from pokemon_interpreter import (
    NAME_TO_OPCODE,
    OpCode,
    run_pokecode,
    HELLO_WORLD,
    FIBONACCI,
)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="PokéCode Host — ejecuta .pkmc / .pok (151 instrucciones)")
    p.add_argument("file", nargs="?", help="Archivo .pkmc o .pok")
    p.add_argument("-c", "--code", help="Código inline")
    p.add_argument("-i", "--input", default="", help="Entrada para KABUTOPS/IN")
    p.add_argument("-t", "--trace", action="store_true", help="Traza por stdout")
    p.add_argument("--trace-file", help="Archivo de traza")
    p.add_argument("--max-cycles", type=int, default=10_000_000)
    p.add_argument("--example", choices=["hello", "fib"], help="Ejemplo integrado")
    p.add_argument("--list", action="store_true", help="Lista las 151 instrucciones")

    args = p.parse_args()

    if args.list:
        print("PokéCode — 151 instrucciones Gen 1")
        print("=" * 60)
        # NAME_TO_OPCODE ya es 151 entradas exactas
        for name, op in sorted(NAME_TO_OPCODE.items(), key=lambda x: int(x[1])):
            print(f"{int(op):3d}  {name}")
        print(f"\nTotal: {len(NAME_TO_OPCODE)}")
        return

    if args.example == "hello":
        source = HELLO_WORLD
    elif args.example == "fib":
        source = FIBONACCI
    elif args.code is not None:
        source = args.code
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    else:
        p.print_help()
        return

    try:
        out = run_pokecode(
            source,
            input_data=args.input,
            trace=args.trace,
            trace_file=args.trace_file,
            max_cycles=args.max_cycles,
        )
        if out:
            # Salida tal cual, sin decoración
            sys.stdout.write(out)
            if not out.endswith("\n"):
                sys.stdout.write("\n")
    except SystemExit as e:
        sys.exit(e.code if isinstance(e.code, int) else 0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
