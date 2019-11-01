#!/usr/bin/env python

import argparse
import os
import subprocess
from pathlib import Path

from antlr4 import *

from .antlr.PyxellLexer import PyxellLexer
from .antlr.PyxellParser import PyxellParser
from .compiler import PyxellCompiler
from .errors import PyxellErrorListener, PyxellError
from .indentation import transform_indented_code


# Parse arguments.
parser = argparse.ArgumentParser(prog='pyxell', description="Run Pyxell compiler.")
parser.add_argument('filepath', help="source file path")
parser.add_argument('clangargs', nargs=argparse.REMAINDER, help="other arguments that will be passed to clang")
args = parser.parse_args()

filepath = Path(args.filepath)
filename, ext = os.path.splitext(filepath)
abspath = Path(__file__).parents[1]

try:
    # Read the code and transform indents.
    pyxell_code = Path(abspath/'lib/std.px').read_text() + filepath.read_text()
    pyxell_code = transform_indented_code(pyxell_code)

    # Parse the program.
    input_stream = InputStream(pyxell_code)
    lexer = PyxellLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PyxellParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(PyxellErrorListener())
    tree = parser.program()

    # Generate LLVM code.
    compiler = PyxellCompiler()
    compiler.visit(tree)
    llvm_code = str(compiler.module)

except FileNotFoundError:
    print("File not found.")
    exit(1)

except PyxellError as error:
    print(str(error))
    exit(1)

# Create an executable.
with open(f'{filename}.ll', 'w') as file:
    file.write(llvm_code)
subprocess.check_output(['clang', f'{filename}.ll', abspath/'lib/io.ll', abspath/'lib/base.ll', '-o', f'{filename}.exe', '-O2'] + args.clangargs)
