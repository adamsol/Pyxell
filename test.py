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
parser.add_argument('pattern', nargs='?', default='/',
                    help="file path pattern (relative to test folder)")
parser.add_argument('-e', '--expect-errors', action='store_true',
                    help="expect compiler errors when running intentionally invalid tests")
args = parser.parse_args()

# Run tests that satisfy a given pattern.
for i, path in enumerate(glob.glob(f'test/*{args.pattern}*.px'), 1):
    print(f"{B}> TEST {i}:{E} {os.path.basename(path)}")
    with open('tmp.out', 'w') as outfile:
        try:
            subprocess.check_output(f'pyxell.exe {path}', stderr=subprocess.STDOUT)
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
