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
    for name in units:
        path = abspath/f'lib/{name}.px'
        units[name] = build_ast(path)
        json.dump(units[name], open(str(path).replace('.px', '.json'), 'w'), indent='\t')


def compile(filepath, cpp_compiler, verbose=False, *other_args):
    filepath = Path(filepath)
    filename, ext = os.path.splitext(filepath)
    cpp_filename = f'{filename}.cpp'
    exe_filename = f'{filename}.exe'

    if verbose:
        print(f'transpiling {filepath} to {cpp_filename}')

    compiler = PyxellCompiler()

    # for name, ast in units.items():
    #     compiler.run(ast, name)

    ast = build_ast(filepath)
    code = compiler.run_main(ast)

    with open(cpp_filename, 'w') as file:
        file.write(code)

    if cpp_compiler.lower() not in {'', 'no', 'none'}:
        command = [cpp_compiler, cpp_filename, '-I', str(abspath), '-o', exe_filename, '-std=c++17', '-O2', *other_args, '-lstdc++']
        if platform.system() != 'Windows':
            command.append('-lm')

        if verbose:
            print(f'running {" ".join(command)}')

        try:
            if verbose:
                subprocess.call(command, stderr=subprocess.STDOUT)
            else:
                subprocess.check_output(command, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            print(f"command not found: {cpp_compiler}")


    return exe_filename


def main():
    parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
    parser.add_argument('filepath', nargs=argparse.OPTIONAL, help="source file path")
    parser.add_argument('-c', '--cpp-compiler', default='gcc', help="C++ compiler command (default: gcc)")
    parser.add_argument('-l', '--libs', action='store_true', help="build libraries and exit")
    parser.add_argument('-r', '--run', action='store_true', help="run the program after compilation")
    parser.add_argument('-v', '--verbose', action='store_true', help="output diagnostic information")
    args, other_args = parser.parse_known_args()

    if not (args.filepath or args.libs):
        parser.error('either filepath or -l option is required')

    if args.libs:
        build_libs()
        sys.exit(0)

    try:
        exe_filename = compile(args.filepath, args.cpp_compiler, args.verbose, *other_args)
    except FileNotFoundError:
        print(f"file not found: {args.filepath}")
        sys.exit(1)
    except PyxellError as e:
        print(str(e))
        sys.exit(1)

    if args.run:
        if args.verbose:
            print(f'executing {exe_filename}')

        subprocess.call(exe_filename)
