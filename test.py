#!/usr/bin/env python

import argparse
import colorama
import concurrent.futures
import glob
import os
import re
import subprocess
import sys
import traceback
import threading
from pathlib import Path
from timeit import default_timer as timer

from src.codegen import INDENT
from src.main import compile, run_cpp_compiler
from src.errors import NotSupportedError, PyxellError

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
parser.add_argument('pattern', nargs='?', default='', help="file path pattern (relative to test folder)")
parser.add_argument('-c', '--cpp-compiler', default='clang', help="C++ compiler command (default: clang)")
parser.add_argument('-s', '--separate', action='store_true', help="compile each test individually (instead of putting all the code into one C++ file)")
parser.add_argument('-O', '--opt-level', default='0', help="compiler optimization level (default: 0)")
parser.add_argument('-t', '--thread-count', dest='thread_count', type=int, default=16, help="number of threads to use")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help="display all tests and don't remove generated files")
args = parser.parse_args()

# Run tests that satisfy the pattern.
tests = {}
i = 1
for path in sorted(glob.glob('test/**/{}*.px'.format('[!_]' if '_' not in args.pattern else ''), recursive=True)):
    path = path.replace(os.path.sep, '/')
    if args.pattern in path:
        tests[path] = i
        i += 1

n = len(tests)

if n == 0:
    print("No tests to run.")
    sys.exit(0)

print(f"Running {n} tests using {args.thread_count} thread{'s' if args.thread_count > 1 else ''}.")

ok = 0
skipped = 0
t0 = timer()
output_dict = {}
output_index = 1
lock = threading.Lock()

aggregate_cpp_code = []
aggregate_cpp_filename = 'all-tests.cpp'
aggregate_exe_filename = aggregate_cpp_filename.replace('.cpp', '.exe')
tests_to_compile = set()

def test(path, running_aggregate_tests=False):
    global ok
    global skipped
    global output_index

    index = tests[path]
    passed = False
    output = [f"{B}> TEST {index}/{n}:{E} {path}"]

    try:
        try:
            expected_error = Path(path.replace('.px', '.err')).read_text()
        except FileNotFoundError:
            expected_error = None

        error = True
        exe_filename = True

        try:
            if running_aggregate_tests:
                exe_filename = f'./{aggregate_exe_filename}'
            else:
                exe_filename = compile(path, args.cpp_compiler, args.opt_level, mode=('executable' if args.separate else 'cpp'))
            error = False
        except NotSupportedError as e:
            skipped += 1
            output.append(f"{Y}{e}{E}")
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
        except subprocess.CalledProcessError as e:
            output.append(f"{R}{e.output.decode()}{E}")
        except Exception:
            output.append(f"{R}{traceback.format_exc()}{E}")

        if not error:
            if expected_error:
                output.append(f"{R}Program compiled successfully, but error expected.\n---\n> {expected_error}{E}")

            elif not args.separate and not running_aggregate_tests:
                aggregate_cpp_code.extend([
                    f'namespace test{index} {{',
                    re.sub('^', INDENT, Path(path.replace('.px', '.cpp')).read_text(), flags=re.MULTILINE),
                    '}\n',
                ])
                tests_to_compile.add(path)
                # The function will be run again with running_aggregate_tests=True.
                return

            elif exe_filename is None:
                output.append(f"{G}OK{E}")
                passed = True

            else:
                with open(path.replace('.px', '.tmp'), 'w') as tmpfile:
                    t1 = timer()
                    command = [exe_filename]
                    if running_aggregate_tests:
                        command.append(path)
                    try:
                        with open(path.replace('.px', '.in'), 'r') as infile:
                            subprocess.call(command, stdin=infile, stdout=tmpfile)
                    except FileNotFoundError:
                        subprocess.call(command, stdout=tmpfile)
                    t2 = timer()

                try:
                    subprocess.check_output(['diff', '--strip-trailing-cr', '--text', path.replace('.px', '.tmp'), path.replace('.px', '.out')], stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    if e.returncode == 2:
                        output.append(f"{Y}{e.output.decode()}{E}")
                    else:
                        output.append(f"{R}WA: {e.output.decode()}{E}")
                else:
                    output.append(f"{G}OK{E} ({t2-t1:.3f}s)")
                    passed = True

    except Exception:
        output.append(f"{R}{traceback.format_exc()}{E}")

    # Print the output of tests in the right order.
    output_dict[index] = '\n'.join(output) if not passed or args.verbose else ''
    with lock:
        while output_index in output_dict:
            if output_dict[output_index]:
                print(output_dict[output_index])
            output_index += 1

    if passed:
        ok += 1
        if not args.verbose:
            os.remove(path.replace('.px', '.tmp'))
            if not error:
                os.remove(path.replace('.px', '.cpp'))
                os.remove(path.replace('.px', '.exe'))

with concurrent.futures.ThreadPoolExecutor(args.thread_count) as executor:
    for path in tests:
        executor.submit(test, path)

if not args.separate:
    if args.verbose:
        print(f"Compiling {aggregate_cpp_filename}.")

    aggregate_cpp_code.extend([
        'int main(int argc, char **argv) {',
        INDENT + 'std::string path = argv[1];',
        *[INDENT + f'if (path == "{path}") test{tests[path]}::main();' for path in tests_to_compile],
        '}',
    ])

    with open(aggregate_cpp_filename, 'w') as file:
        file.write('\n'.join(aggregate_cpp_code))

    try:
        run_cpp_compiler(args.cpp_compiler, aggregate_cpp_filename, aggregate_exe_filename, args.opt_level, disable_warnings=True)
    except subprocess.CalledProcessError as e:
        print(f"{R}{e.output.decode()}{E}")
    else:
        with concurrent.futures.ThreadPoolExecutor(args.thread_count) as executor:
            for path in tests_to_compile:
                executor.submit(test, path, running_aggregate_tests=True)

        if not args.verbose:
            os.remove(aggregate_cpp_filename)
            os.remove(aggregate_exe_filename)

print(f"{B}---{E}")
msg = f"Run {n} tests in {timer()-t0:.3f}s"
failed = n - ok - skipped

if skipped:
    msg += f", {Y}{skipped} skipped{E}"

if failed:
    msg += f", {R}{failed} failed{E}"
else:
    msg += f", {G}all passed{E}"

print(msg + f".")
