
from antlr4 import *

from .parser.PyxellLexer import PyxellLexer
from .parser.PyxellParser import PyxellParser

from .ast import PyxellASTVisitor
from .errors import PyxellErrorListener


def _get_parser(code, filepath):
    input_stream = InputStream(code)
    lexer = PyxellLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PyxellParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(PyxellErrorListener(filepath))
    return parser


def _build_ast(tree):
    visitor = PyxellASTVisitor()
    return visitor.visit(tree)


def parse_program(code, filepath):
    return _build_ast(_get_parser(code, filepath).program())


def parse_expr(code, filepath):
    return _build_ast(_get_parser(code, filepath).interpolation_expr())
