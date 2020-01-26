#!/usr/bin/env python

import argparse
import os
import json
import platform
import subprocess
import sys
from pathlib import Path

from .compiler import PyxellCompiler
from .errors import PyxellError
from .indentation import transform_indented_code
from .library import BaseLibraryGenerator
from .parsing import parse_program

abspath = Path(__file__).parents[1]

units = {}
for name in ['std', 'math', 'time', 'random']:
    try:
        unit = json.load(open(abspath/f'lib/{name}.json'))
    except FileNotFoundError:
        unit = None
    units[name] = unit


def build_ast(path):
    code = transform_indented_code(path.read_text())
    return parse_program(code)


def build_libs():
    with open(abspath/'lib/base.ll', 'w') as file:
        file.write(BaseLibraryGenerator().llvm_ir())

    subprocess.check_output(['clang', str(abspath/'lib/io.c'), '-S', '-emit-llvm', '-o', str(abspath/'lib/io.ll')], stderr=subprocess.STDOUT)

    for name in units:
        path = abspath/f'lib/{name}.px'
        units[name] = build_ast(path)
        json.dump(units[name], open(str(path).replace('.px', '.json'), 'w'))


def compile(filepath, clangargs):
    filepath = Path(filepath)
    filename, ext = os.path.splitext(filepath)
    exename = f'{filename}.exe'

    compiler = PyxellCompiler()

    for name, ast in units.items():
        compiler.run(ast, name)

    compiler.run_main(build_ast(filepath))

    with open(f'{filename}.ll', 'w') as file:
        file.write(compiler.llvm_ir())

    clang_command = ['clang', f'{filename}.ll', str(abspath/'lib/io.ll'), str(abspath/'lib/base.ll'), '-o', exename, '-O2', *clangargs]
    if platform.system() != 'Windows':
        clang_command.append('-lm')

    subprocess.check_output(clang_command, stderr=subprocess.STDOUT)

    return exename


def main():
    parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
    parser.add_argument('filepath', nargs=argparse.OPTIONAL, help="source file path")
    parser.add_argument('clangargs', nargs=argparse.REMAINDER, help="other arguments that will be passed to clang")
    parser.add_argument('-l', '--libs', action='store_true', help="build libraries and exit")
    parser.add_argument('-r', '--run', action='store_true', help="run the program after compilation")
    args = parser.parse_args()

    if not (args.filepath or args.libs):
        parser.error('either filepath or -l option is required')

    if args.libs:
        build_libs()
        sys.exit(0)

    if not os.path.exists(abspath/'lib/base.ll'):
        build_libs()

    try:
        exename = compile(args.filepath, args.clangargs)
    except FileNotFoundError:
        print(f"file not found: {args.filepath}")
        sys.exit(1)
    except PyxellError as e:
        print(str(e))
        sys.exit(1)

    if args.run:
        subprocess.call(exename)
