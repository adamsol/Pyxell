
from antlr4 import *

from .antlr.PyxellLexer import PyxellLexer
from .antlr.PyxellParser import PyxellParser
from .errors import PyxellErrorListener


def _get_parser(code):
    input_stream = InputStream(code)
    lexer = PyxellLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PyxellParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(PyxellErrorListener())
    return parser


def parse_program(code):
    return _get_parser(code).program()


def parse_expr(code):
    return _get_parser(code).interpolation_expr()
