
import argparse
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from timeit import default_timer as timer

from .errors import PyxellError
from .indentation import transform_indented_code
from .parser import PyxellParser
from .transpiler import PyxellTranspiler

abspath = Path(os.path.abspath(__file__)).parents[1]

version = Path(abspath/'version.txt').read_text()


def build_ast(path):
    # Note: Python automatically normalizes '\r' and '\r\n' to '\n' when reading a file.
    lines = transform_indented_code(path.read_text(), path)
    return PyxellParser(lines, path).parse_program()


units = {}
for name in ['std', 'math', 'random']:
    units[name] = build_ast(abspath/f'lib/{name}.px')


def resolve_local_includes(path):
    code = path.read_text().replace('#pragma once', '')

    def replacer(match):
        return resolve_local_includes(path.parents[0]/match.group(1))

    return re.sub(r'#include "(.+?)"', replacer, code)


def cpp_flags(opt_level):
    return ['-std=c++17', f'-O{opt_level}']


def precompile_base_header(cpp_compiler, opt_level):
    command = [cpp_compiler, *cpp_flags(opt_level), '-c', str(abspath/'lib/base.hpp')]
    subprocess.run(command, stdout=subprocess.PIPE, check=True)


def run_cpp_compiler(cpp_compiler, cpp_filename, exe_filename, opt_level, verbose=False, disable_warnings=False):
    command = [cpp_compiler, *cpp_flags(opt_level), cpp_filename, '-include', str(abspath/'lib/base.hpp'), '-o', exe_filename, '-lstdc++']
    if disable_warnings:
        command.append('-w')
    if platform.system() != 'Windows':
        command.append('-lm')

    if verbose:
        print(f"running {' '.join(command)}")

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if verbose and output:
            print(output.decode())
    except FileNotFoundError:
        print(f"command not found: {cpp_compiler}")
        sys.exit(1)


def compile(filepath, cpp_compiler, opt_level, verbose=False, mode='executable'):
    filepath = Path(filepath)
    filename, ext = os.path.splitext(filepath)
    cpp_filename = f'{filename}.cpp'
    exe_filename = f'{filename}.exe'

    if verbose:
        print(f"transpiling {filepath} to {cpp_filename}")

    t1 = timer()
    transpiler = PyxellTranspiler()

    for name, ast in units.items():
        transpiler.run(ast, name, f'lib/{name}.px')

    ast = build_ast(filepath)
    code = transpiler.run_main(ast, filepath)

    with open(cpp_filename, 'w') as file:
        file.write(f"/*\n"
                   f"Generated by Pyxell {version}.\n"
                   f"https://github.com/adamsol/Pyxell\n"
                   f"*/\n\n")

        if mode == 'standalone-cpp':
            file.write(resolve_local_includes(abspath/'lib/base.hpp'))
            file.write("\n\n/* Program */\n\n")

        file.write(code)

    t2 = timer()
    global transpilation_time
    transpilation_time = t2 - t1

    if mode != 'executable':
        return

    t1 = timer()
    run_cpp_compiler(cpp_compiler, cpp_filename, exe_filename, opt_level, verbose)
    t2 = timer()
    global compilation_time
    compilation_time = t2 - t1

    return exe_filename


def main():
    parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
    parser.add_argument('filepath', nargs=argparse.OPTIONAL, help="source file path")
    parser.add_argument('-c', '--cpp-compiler', default='gcc', help="C++ compiler command (default: gcc)")
    parser.add_argument('-l', '--time-limit', type=int, help="program execution time limit")
    parser.add_argument('-n', '--dont-run', action='store_true', help="don't run the program after compilation")
    parser.add_argument('-O', '--opt-level', type=int, choices=range(4), default=0, help="compiler optimization level (default: 0)")
    parser.add_argument('-p', '--precompile-header', action='store_true', help="precompile the base.hpp header and exit")
    parser.add_argument('-s', '--standalone-cpp', action='store_true', help="save transpiled C++ code for standalone compilation and exit")
    parser.add_argument('-t', '--time', action='store_true', help="measure time of program compilation and execution")
    parser.add_argument('-v', '--verbose', action='store_true', help="output diagnostic information")
    parser.add_argument('-V', '--version', action='store_true', help="print version number and exit")
    args = parser.parse_args()

    if args.version:
        print(f"Pyxell {version}")
        sys.exit(0)

    if args.precompile_header:
        precompile_base_header(args.cpp_compiler, args.opt_level)
        sys.exit(0)

    if not args.filepath:
        parser.error("filepath is required")

    try:
        mode = 'standalone-cpp' if args.standalone_cpp else 'executable'
        exe_filename = compile(args.filepath, args.cpp_compiler, args.opt_level, args.verbose, mode)
    except FileNotFoundError:
        print(f"file not found: {args.filepath}")
        sys.exit(1)
    except PyxellError as e:
        print(str(e))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        sys.exit(1)

    if exe_filename and not args.dont_run:
        if '/' not in exe_filename and '\\' not in exe_filename:
            exe_filename = './' + exe_filename

        if args.verbose:
            print(f"executing {exe_filename}")

        t1 = timer()

        try:
            subprocess.run(exe_filename, timeout=args.time_limit)
        except subprocess.TimeoutExpired:
            print('execution time limit exceeded')
            sys.exit(2)

        t2 = timer()
        execution_time = t2 - t1

    if args.time:
        print("---")
        print(f"transpilation: {transpilation_time:.3f}s")
        if exe_filename:
            print(f"compilation: {compilation_time:.3f}s")
            if not args.dont_run:
                print(f"execution: {execution_time:.3f}s")
