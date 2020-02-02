#!/usr/bin/env python

import argparse
import colorama
import concurrent.futures
import glob
import os
import subprocess
import sys
import traceback
import threading
from pathlib import Path
from timeit import default_timer as timer

from src.main import compile
from src.errors import PyxellError

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
parser.add_argument('-c', '--cpp-compiler', default='g++', help="C++ compiler command (default: g++)")
parser.add_argument('-t', '--thread-count', dest='thread_count', type=int, default=16,
                    help="number of threads to use")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help="display all tests and don't remove generated files")
args = parser.parse_args()

# Run tests that satisfy the pattern.
tests = []
for path in glob.glob('test/**/{}*.px'.format('[!_]' if '_' not in args.pattern else ''), recursive=True):
    path = path.replace(os.path.sep, '/')
    if args.pattern in path:
        tests.append(path)

n = len(tests)

if n == 0:
    print("No tests to run.")
    sys.exit(0)

print(f"Running {n} tests using {args.thread_count} thread{'s' if args.thread_count > 1 else ''}.")

ok = 0
t0 = timer()
output_dict = {}
output_index = 1
lock = threading.Lock()

def test(i, path):
    global ok
    global output_index

    passed = False
    output = []
    output.append(f"{B}> TEST {i}/{n}:{E} {path}")

    with open(path.replace(".px", ".tmp"), 'w') as tmpfile:
        try:
            expected_error = Path(path.replace(".px", ".err")).read_text()
        except FileNotFoundError:
            expected_error = None

        error = False

        try:
            compile(path, args.cpp_compiler)
        except PyxellError as e:
            error_message = str(e)
            if expected_error:
                if error_message.strip().endswith(expected_error):
                    output.append(f"{G}{error_message}{E}")
                    passed = True
                else:
                    output.append(f"{R}{error_message}\n---\n> {expected_error}{E}")
            else:
                output.append(f"{R}{error_message}{E}")
            error = True
        except subprocess.CalledProcessError as e:
            output.append(f"{R}{e.output.decode()}{E}")
            error = True
        except Exception:
            output.append(f"{R}{traceback.format_exc()}{E}")
            error = True

        if not error:
            if expected_error:
                output.append(f"{R}Program compiled successfully, but error expected.\n---\n> {expected_error}{E}")
            else:
                t1 = timer()
                try:
                    with open(f'{path.replace(".px", ".in")}', 'r') as infile:
                        subprocess.call(f'{path.replace(".px", ".exe")}', stdin=infile, stdout=tmpfile)
                except FileNotFoundError:
                    subprocess.call(f'{path.replace(".px", ".exe")}', stdout=tmpfile)
                t2 = timer()

                try:
                    subprocess.check_output(['diff', '--strip-trailing-cr', path.replace(".px", ".tmp"), path.replace(".px", ".out")], stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    if e.returncode == 2:
                        output.append(f"{Y}{e.output.decode()}{E}")
                    else:
                        output.append(f"{R}WA: {e.output.decode()}{E}")
                else:
                    output.append(f"{G}OK{E} ({t2-t1:.3f}s)")
                    passed = True

        # Print the output of tests in the right order.
        output_dict[i] = '\n'.join(output) if not passed or args.verbose else ''
        with lock:
            while output_index in output_dict:
                if output_dict[output_index]:
                    print(output_dict[output_index])
                output_index += 1

    if passed:
        ok += 1
        if not args.verbose:
            os.remove(path.replace(".px", ".tmp"))
            if not error:
                os.remove(path.replace(".px", ".cpp"))
                os.remove(path.replace(".px", ".exe"))

with concurrent.futures.ThreadPoolExecutor(args.thread_count) as executor:
    for i, path in enumerate(tests, 1):
        executor.submit(test, i, path)

print(f"{B}---{E}")
msg = f"Run {n} tests in {timer()-t0:.3f}s"
if ok == n:
    print(msg + f", {G}all passed{E}.")
else:
    print(msg + f", {R}{n-ok} failed{E}.")
