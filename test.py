#!/usr/bin/env python

import argparse
import colorama
import glob
import os
import subprocess
from timeit import default_timer as timer

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
parser.add_argument('-t', '--target-windows-gnu', action='store_true',
                    help="run compiler with -target x86_64-pc-windows-gnu")
args = parser.parse_args()

# Run tests that satisfy the pattern.
tests = []
for path in glob.glob('test/**/{}*.px'.format('[!_]' if '_' not in args.pattern else ''), recursive=True):
    if args.pattern.replace('/', os.path.sep) in path:
        tests.append(path)
n = len(tests)

t0 = timer()
ok = i = 0
for i, path in enumerate(tests, 1):
    print(f"{B}> TEST {i}/{n}:{E} {path}")

    with open('tmp.out', 'w') as outfile:
        try:
            params = '-target x86_64-pc-windows-gnu' if args.target_windows_gnu else ''
            subprocess.check_output(f'pyxell.exe {path} {params}', stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if os.path.isfile(path.replace(".px", ".err")):
                error_message = e.output.decode()
                with open(f'{path.replace(".px", ".err")}', 'r') as errfile:
                    error_expected = errfile.read()
                    if e.output.decode().endswith(error_expected):
                        print(f"{G}{error_message}{E}")
                        ok += 1
                    else:
                        print(f"{R}{error_message}\n---\n> {error_expected}{E}")
            else:
                print(f"{R}Compiler returned error code {e.returncode}.\n{e.output.decode()}{E}")
            continue
        else:
            if os.path.isfile(path.replace(".px", ".err")):
                print(f"{R}Compiler returned code 0, but error expected!{E}")
                continue

        t1 = timer()
        try:
            with open(f'{path.replace(".px", ".in")}', 'r') as infile:
                subprocess.call(f'{path.replace(".px", ".exe")}', stdin=infile, stdout=outfile)
        except FileNotFoundError:
            subprocess.call(f'{path.replace(".px", ".exe")}', stdout=outfile)
        t2 = timer()

        try:
            subprocess.check_output(f'diff --strip-trailing-cr tmp.out {path.replace(".px", ".out")}', stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:
                print(f"{Y}{e.output.decode()}{E}")
            else:
                print(f"{R}WA: {e.output.decode()}{E}")
        else:
            print(f"{G}OK{E} ({t2-t1:.3f}s)")
            ok += 1

if i > 0:
    print(f"{B}---{E}")
    msg = f"Run {i} tests in {timer()-t0:.3f}s"
    if ok == i:
        print(msg + f", {G}all passed{E}.")
    else:
        print(msg + f", {R}{i-ok} failed{E}.")
else:
    print("No tests to run.")
