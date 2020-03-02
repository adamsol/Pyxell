
from antlr4.error.ErrorListener import ErrorListener


class PyxellErrorListener(ErrorListener):

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise PyxellError(PyxellError.InvalidSyntax(), line, column+1)


class PyxellError(Exception):

    InvalidSyntax = lambda: f"Syntax error"

    AbstractClass = lambda t: f"Cannot instantiate an abstract class `{t.show()}`"
    CannotUnpack = lambda t, n: f"Cannot unpack value of type `{t.show()}` into {n} values"
    ClosureRequired = lambda id: f"Cannot access a non-global and non-local variable `{id}`"
    ExpectedNamedArgument = lambda: f"Positional argument cannot follow named arguments"
    IllegalAssignment = lambda t1, t2: f"Illegal assignment from `{t1.show()}` to `{t2.show()}`"
    IllegalLambda = lambda: "Lambda expression cannot be used in this context"
    IllegalOverride = lambda t1, t2: f"Cannot override member of type `{t1.show()}` with type `{t2.show()}`"
    IllegalRange = lambda: "Range expression cannot be used in this context"
    IllegalRedefinition = lambda id: f"Illegal redefinition of identifier `{id}`"
    IllegalSuper = lambda: "Cannot use `super` here"
    InvalidArgumentTypes = lambda t: f"Cannot unify argument types for type variable `{t.show()}`"
    InvalidDeclaration = lambda t: f"Cannot declare variable of type `{t.show()}`"
    InvalidFunctionCall = lambda id, types, msg: f"Error in function `{id}` called here{(' (with types ' + ', '.join(f'{name}={type.show()}' for name, type in types.items()) + ')') if types else ''}.\n{msg}"
    InvalidLoopStep = lambda: f"Incompatible number of loop variables and step expressions"
    InvalidMember = lambda id: f"Invalid type signature of member `{id}`"
    InvalidModule = lambda id: f"Could not find module `{id}`"
    MissingDefault = lambda id: f"Missing default value for argument `{id}`"
    MissingReturn = lambda: f"Not all code paths return a value"
    NoAttribute = lambda t, id: f"Type `{t.show()}` has no attribute `{id}`"
    NoBinaryOperator = lambda op, t1, t2: f"No binary operator `{op}` defined for `{t1.show()}` and `{t2.show()}`"
    NoUnaryOperator = lambda op, t: f"No unary operator `{op}` defined for `{t.show()}`"
    NotComparable = lambda t1, t2: f"Cannot compare `{t1.show()}` with `{t2.show()}`"
    NotIndexable = lambda t: f"Type `{t.show()}` is not indexable"
    NotIterable = lambda t: f"Type `{t.show()}` is not iterable"
    NotLvalue = lambda: f"Expression cannot be assigned to"
    NotFunction = lambda t: f"Type `{t.show()}` is not a function"
    NotNullable = lambda t: f"Type `{t.show()}` is not nullable"
    NotPrintable = lambda t: f"Variable of type `{t.show()}` cannot be printed"
    NotClass = lambda t: f"Type `{t.show()}` is not a class"
    NotType = lambda id: f"Identifier `{id}` does not represent a type"
    NotVariable = lambda id: f"Identifier `{id}` does not represent a variable"
    RedeclaredIdentifier = lambda id: f"Identifier `{id}` is already declared"
    RepeatedArgument = lambda id: f"Repeated argument `{id}`"
    RepeatedMember = lambda id: f"Repeated member `{id}` in class definition"
    TooFewArguments = lambda t: f"Too few arguments for function `{t.show()}`"
    TooManyArguments = lambda t: f"Too many arguments for function `{t.show()}`"
    UndeclaredIdentifier = lambda id: f"Undeclared identifier `{id}`"
    UninitializedIdentifier = lambda id: f"Identifier `{id}` might not have been initialized"
    UnexpectedArgument = lambda id: f"Unexpected argument `{id}`"
    UnexpectedStatement = lambda s: f"Unexpected `{s}` statement"
    UnknownType = lambda: f"Cannot settle type of the expression"

    def __init__(self, msg, line, column=None):
        self.line = line
        self.column = column
        text = f"Line {line}"
        if column:
            text += f", column {column}"
        text += f": {msg}."
        super().__init__(text)
