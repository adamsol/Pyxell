
from antlr4.error.ErrorListener import ErrorListener


class PyxellErrorListener(ErrorListener):

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise PyxellError(PyxellError.InvalidSyntax(), line, column+1)


class PyxellError(Exception):

    InvalidIndentation = lambda: f"Indentation error"
    InvalidSyntax = lambda: f"Syntax error"

    CannotUnpack = lambda t, n: f"Cannot unpack value of type `{t.show()}` into {n} values"
    IllegalAssignment = lambda t1, t2: f"Illegal assignment from `{t1.show()}` to `{t2.show()}`"
    InvalidDeclaration = lambda t: f"Cannot declare variable of type `{t.show()}`"
    InvalidLoopStep = lambda: f"Incompatible number of loop variables and step expressions"
    MissingDefault = lambda id: f"Missing default value for argument `{id}`"
    MissingReturn = lambda id: f"Not all code paths return a value in function `{id}`"
    NoAttribute = lambda t, id: f"Type `{t.show()}` has no attribute `{id}`"
    NoBinaryOperator = lambda op, t1, t2: f"No binary operator `{op}` defined for `{t1.show()}` and `{t2.show()}`"
    NoUnaryOperator = lambda op, t: f"No unary operator `{op}` defined for `{t.show()}`"
    NotComparable = lambda t1, t2: f"Cannot compare `{t1.show()}` with `{t2.show()}`"
    NotIndexable = lambda t: f"Type `{t.show()}` is not indexable"
    NotIterable = lambda t: f"Type `{t.show()}` is not iterable"
    NotLvalue = lambda: f"Expression cannot be assigned to"
    NotFunction = lambda t: f"Type `{t.show()}` is not a function"
    NotPrintable = lambda t: f"Variable of type `{t.show()}` cannot be printed"
    RedeclaredIdentifier = lambda id: f"Identifier `{id}` is already declared"
    TooFewArguments = lambda t: f"Too few arguments for function `{t.show()}`"
    TooManyArguments = lambda t: f"Too many arguments for function `{t.show()}`"
    UndeclaredIdentifier = lambda id: f"Undeclared identifier `{id}`"
    UninitializedIdentifier = lambda id: f"Identifier `{id}` might not have been initialized"
    UnexpectedStatement = lambda s: f"Unexpected `{s}` statement"
    UnknownType = lambda: f"Cannot settle type of the expression"

    def __init__(self, msg, line, column=None):
        text = f"Line {line}"
        if column:
            text += f", column {column}"
        text += f": {msg}."
        super().__init__(text)
