
from antlr4.error.ErrorListener import ErrorListener


class PyxellErrorListener(ErrorListener):

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise PyxellError(PyxellError.InvalidSyntax(), line, column+1)


class PyxellError(Exception):

    CannotUnpack = lambda t, n: f"Cannot unpack value of type `{t.show()}` into {n} values"
    IllegalAssignment = lambda t1, t2: f"Illegal assignment from `{t1.show()}` to `{t2.show()}`"
    InvalidIndentation = lambda: f"Indentation error"
    InvalidSyntax = lambda: f"Syntax error"
    NoAttribute = lambda t, id: f"Type `{t.show()}` has no attribute `{id}`"
    NoBinaryOperator = lambda op, t1, t2: f"No binary operator `{op}` defined for `{t1.show()}` and `{t2.show()}`"
    NoUnaryOperator = lambda op, t: f"No unary operator `{op}` defined for `{t.show()}`"
    NotComparable = lambda t1, t2: f"Cannot compare `{t1.show()}` with `{t2.show()}`"
    NotIndexable = lambda t: f"Type `{t.show()}` is not indexable"
    NotLvalue = lambda: f"Expression cannot be assigned to"
    NotPrintable = lambda t: f"Variable of type `{t.show()}` cannot be printed"
    UndeclaredIdentifier = lambda id: f"Undeclared identifier `{id}`"
    UnknownType = lambda: f"Cannot settle type of the expression"

    def __init__(self, msg, line, column=None):
        text = f"Line {line}"
        if column:
            text += f", column {column}"
        text += f": {msg}."
        super().__init__(text)
