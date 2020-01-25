#!/usr/bin/env python

import argparse
import os
import platform
import subprocess
from pathlib import Path

from .compiler import PyxellCompiler
from .errors import PyxellError
from .indentation import transform_indented_code
from .library import BaseLibraryGenerator
from .parsing import parse_program

abspath = Path(__file__).parents[1]


with open(abspath/'lib/base.ll', 'w') as file:
    file.write(BaseLibraryGenerator().llvm_ir())

subprocess.check_output(['clang', str(abspath/'lib/io.c'), '-S', '-emit-llvm', '-o', str(abspath/'lib/io.ll')], stderr=subprocess.STDOUT)


def build_ast(path):
    code = transform_indented_code(path.read_text())
    return parse_program(code)


units = {}
for name in ['std', 'math', 'time', 'random']:
    path = abspath/f'lib/{name}.px'
    units[name] = build_ast(path)


def compile(filepath, clangargs):
    filepath = Path(filepath)
    filename, ext = os.path.splitext(filepath)

    compiler = PyxellCompiler()

    for name, ast in units.items():
        compiler.run(ast, name)

    compiler.run_main(build_ast(filepath))

    with open(f'{filename}.ll', 'w') as file:
        file.write(compiler.llvm_ir())

    clang_command = ['clang', f'{filename}.ll', str(abspath/'lib/io.ll'), str(abspath/'lib/base.ll'), '-o', f'{filename}.exe', '-O2', *clangargs]
    if platform.system() != 'Windows':
        clang_command.append('-lm')

    subprocess.check_output(clang_command, stderr=subprocess.STDOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
    parser.add_argument('filepath', help="source file path")
    parser.add_argument('clangargs', nargs=argparse.REMAINDER, help="other arguments that will be passed to clang")
    args = parser.parse_args()

    try:
        compile(args.filepath, args.clangargs)
    except FileNotFoundError:
        print(f"file not found: {args.filepath}")
        exit(1)
    except PyxellError as e:
        print(str(e))
        exit(1)
