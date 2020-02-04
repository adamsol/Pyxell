
from .types import *

__all__ = [
    'Value',
    'vInt', 'vFloat', 'vBool', 'vFalse', 'vTrue', 'vChar', 'vString',
    'Variable',
]


class Value:

    def __init__(self, type, value, formatter=None):
        self.type = type
        self.value = value
        self.formatter = formatter

    def __str__(self):
        if isinstance(self.formatter, str):
            return self.formatter.format(self.value)
        if callable(self.formatter):
            return self.formatter(self.value)
        return str(self.value)


def vInt(x):
    return Value(tInt, x, '{}LL')

def vFloat(x):
    return Value(tFloat, x)

def vBool(x):
    return Value(tBool, x, lambda value: str(value).lower())

vFalse = vBool(False)
vTrue = vBool(True)

def vChar(x):
    return Value(tChar, x, "'{}'")

def vString(x):
    return Value(tString, x, '"{}"s')


class Variable(Value):

    def __init__(self, type, name):
        self.type = type
        self.name = name

    def __str__(self):
        return self.name
