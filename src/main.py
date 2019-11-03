#!/usr/bin/env python

import argparse
import os
import subprocess
from pathlib import Path

from .compiler import PyxellCompiler
from .indentation import transform_indented_code
from .parsing import parse_program

abspath = Path(__file__).parents[1]


def run_compiler(filepath, clangargs):
    filename, ext = os.path.splitext(filepath)

    units = {
        **{name: abspath/f'lib/{name}.px' for name in [
            'std', 'math', 'time', 'random',
        ]},
        'main': Path(filepath),
    }

    compiler = PyxellCompiler()

    for name, path in units.items():
        code = transform_indented_code(path.read_text())
        tree = parse_program(code)
        compiler.visitProgram(tree, unit=name)

    with open(f'{filename}.ll', 'w') as file:
        file.write(compiler.llvm())

    try:
        subprocess.check_output(['clang', f'{filename}.ll', abspath/'lib/io.ll', abspath/'lib/base.ll', '-o', f'{filename}.exe', '-O2', *clangargs], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise ValueError(e.output.decode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
    parser.add_argument('filepath', help="source file path")
    parser.add_argument('clangargs', nargs=argparse.REMAINDER, help="other arguments that will be passed to clang")
    args = parser.parse_args()

    try:
        run_compiler(args.filepath, args.clangargs)
    except Exception as e:
        print(str(e))
        exit(1)
