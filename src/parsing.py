
from antlr4 import *

from .antlr.PyxellLexer import PyxellLexer
from .antlr.PyxellParser import PyxellParser

from .ast import PyxellASTVisitor
from .errors import PyxellErrorListener


def _get_parser(code):
    input_stream = InputStream(code)
    lexer = PyxellLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PyxellParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(PyxellErrorListener())
    return parser


def _build_ast(tree):
    visitor = PyxellASTVisitor()
    return visitor.visit(tree)


def parse_program(code):
    return _build_ast(_get_parser(code).program())


def parse_expr(code):
    return _build_ast(_get_parser(code).interpolation_expr())
