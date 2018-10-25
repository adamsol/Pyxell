#!/usr/bin/env python

import os
import glob
import subprocess
import colorama
import argparse

# Setup terminal colors.
R = colorama.Style.BRIGHT + colorama.Fore.RED
G = colorama.Style.BRIGHT + colorama.Fore.GREEN
B = colorama.Style.BRIGHT + colorama.Fore.BLUE
Y = colorama.Style.BRIGHT + colorama.Fore.YELLOW
M = colorama.Style.BRIGHT + colorama.Fore.MAGENTA
C = colorama.Style.BRIGHT + colorama.Fore.CYAN
E = colorama.Style.RESET_ALL
colorama.init()

# Parse arguments.
parser = argparse.ArgumentParser(description="Test Pyxell compiler.")
parser.add_argument('pattern', nargs='?', default='',
                    help="file path pattern (relative to test folder)")
parser.add_argument('-e', '--expect-errors', action='store_true',
                    help="expect compiler errors when running intentionally invalid tests")
parser.add_argument('-t', '--target-windows-gnu', action='store_true',
                    help="run compiler with -target x86_64-pc-windows-gnu")
args = parser.parse_args()

# Run tests that satisfy a given pattern.
i = 0
for path in glob.glob(f'test/**/[!_]*.px', recursive=True):
    if args.pattern.replace('/', os.path.sep) not in path:
        continue
    i += 1
    print(f"{B}> TEST {i}:{E} {path}")

    with open('tmp.out', 'w') as outfile:
        try:
            params = '-target x86_64-pc-windows-gnu' if args.target_windows_gnu else ''
            subprocess.check_output(f'pyxell.exe {path} {params}', stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if args.expect_errors:
                print(f"{G}{e.output.decode()}{E}")
            else:
                print(f"{R}Compiler returned error code {e.returncode}.\n{e.output.decode()}{E}")
            continue
        else:
            if args.expect_errors:
                print(f"{R}Compiler returned code 0, but error expected!{E}")
                continue

        try:
            with open(f'{path.replace(".px", ".in")}', 'r') as infile:
                subprocess.call(f'{path.replace(".px", ".exe")}', stdin=infile, stdout=outfile)
        except FileNotFoundError:
            subprocess.call(f'{path.replace(".px", ".exe")}', stdout=outfile)

        try:
            subprocess.check_output(f'diff --strip-trailing-cr tmp.out {path.replace(".px", ".out")}', stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:
                print(f"{Y}{e.output.decode()}{E}")
            else:
                print(f"{R}WA: {e.output.decode()}{E}")
        else:
            print(f"{G}OK{E}")
