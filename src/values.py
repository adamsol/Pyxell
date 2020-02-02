
from .types import *

__all__ = [
    'Value',
    'vInt', 'vFloat', 'vBool', 'vFalse', 'vTrue', 'vChar',
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


def vInt(n):
    return Value(tInt, n, '{}LL')

def vFloat(f):
    return Value(tFloat, f)

def vBool(b):
    return Value(tBool, b, lambda value: str(value).lower())

vFalse = vBool(False)
vTrue = vBool(True)

def vChar(c):
    return Value(tChar, ord(c), "'{}'")


class Variable(Value):

    def __init__(self, type, name):
        self.type = type
        self.name = name

    def __str__(self):
        return self.name
