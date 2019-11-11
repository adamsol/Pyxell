
from collections import namedtuple

import llvmlite.ir as ll

from .utils import *


__all__ = [
    'tVoid', 'tInt', 'tFloat', 'tBool', 'tChar', 'tPtr', 'tString', 'tArray', 'tNullable', 'tTuple', 'tFunc', 'tUnknown',
    'Arg',
    'can_cast', 'unify_types',
    'vInt', 'vFloat', 'vBool', 'vFalse', 'vTrue', 'vChar', 'vNull', 'vIndex',
]


class UnknownType(ll.Type):

    def _to_string(self):
        return 'i8*'

    def __eq__(self, other):
        return isinstance(other, UnknownType)

    def __hash__(self):
        return hash(UnknownType)


class CustomStructType(ll.LiteralStructType):

    def __init__(self, elements, kind):
        super().__init__(elements)
        self.kind = kind

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self.kind == other.kind

    def __hash__(self):
        return hash(CustomStructType)


tVoid = ll.VoidType()
tInt = ll.IntType(64)
tFloat = ll.DoubleType()
tBool = ll.IntType(1)
tChar = ll.IntType(8)


def tPtr(type=tChar):
    ptr_type = type.as_pointer()
    ptr_type.kind = getattr(type, 'kind', None)
    return ptr_type


tString = tPtr(CustomStructType([tPtr(), tInt], 'string'))
tString.subtype = tChar

@extend_class(ll.Type)
def isString(type):
    return getattr(type, 'kind', None) == 'string'


def tArray(subtype):
    type = tPtr(CustomStructType([tPtr(subtype), tInt], 'array'))
    type.subtype = subtype
    return type

@extend_class(ll.Type)
def isArray(type):
    return getattr(type, 'kind', None) == 'array'


def tNullable(subtype):
    type = tPtr(subtype)
    type.subtype = subtype
    type.kind = 'nullable'
    return type

@extend_class(ll.Type)
def isNullable(type):
    return getattr(type, 'kind', None) == 'nullable'


def tTuple(elements):
    type = tPtr(CustomStructType(elements, 'tuple'))
    type.elements = elements
    return type

@extend_class(ll.Type)
def isTuple(type):
    return getattr(type, 'kind', None) == 'tuple'


Arg = namedtuple('Arg', ['type', 'name', 'default'], defaults=[None]*3)

def tFunc(args, ret=tVoid):
    args = [arg if isinstance(arg, Arg) else Arg(arg) for arg in args]
    type = tPtr(ll.FunctionType(ret, [arg.type for arg in args]))
    type.args = args
    type.ret = ret
    type.kind = 'function'
    return type

@extend_class(ll.Type)
def isFunc(type):
    return getattr(type, 'kind', None) == 'function'


@extend_class(ll.Type)
def isCollection(type):
    return type == tString or type.isArray()


tUnknown = UnknownType()

@extend_class(ll.Type)
def isUnknown(type):
    if type == tUnknown:
        return True
    if type.isArray():
        return type.subtype.isUnknown()
    if type.isTuple():
        return any(elem.isUnknown() for elem in type.elements)
    if type.isFunc():
        return any(arg.type.isUnknown() for arg in type.args) or type.ret.isUnknown()
    return False


def can_cast(type1, type2):
    if type1 == type2:
        return True
    if type1.isArray() and type2.isArray():
        return can_cast(type1.subtype, type2.subtype)
    if type1.isNullable() and type2.isNullable():
        return can_cast(type1.subtype, type2.subtype)
    if type2.isNullable():
        return can_cast(type1, type2.subtype)
    if type1.isTuple() and type2.isTuple():
        return len(type1.elements) == len(type2.elements) and \
               all(can_cast(t1, t2) for t1, t2 in zip(type1.elements, type2.elements))
    if type1 == tUnknown or type2 == tUnknown:
        return True
    return False


def unify_types(type1, type2):
    if type1 == type2:
        return type1
    if type1 == tFloat and type2 == tInt or type1 == tInt and type2 == tFloat:
        return tFloat
    if type1.isArray() and type2.isArray():
        subtype = unify_types(type1.subtype, type2.subtype)
        return tArray(subtype) if subtype else None
    if type1.isNullable() or type2.isNullable():
        subtype = unify_types(type1.subtype if type1.isNullable() else type1, type2.subtype if type2.isNullable() else type2)
        return tNullable(subtype) if subtype else None
    if type1.isTuple() and type2.isTuple():
        elems = [unify_types(t1, t2) for t1, t2 in zip(type1.elements, type2.elements)]
        return tTuple(elems) if all(elems) and len(type1.elements) == len(type2.elements) else None
    if type1 == tUnknown:
        return type2
    if type2 == tUnknown:
        return type1
    return None


@extend_class(ll.Type)
def show(type):
    if type == tVoid:
        return 'Void'
    if type == tInt:
        return 'Int'
    if type == tFloat:
        return 'Float'
    if type == tBool:
        return 'Bool'
    if type == tChar:
        return 'Char'
    if type.isString():
        return 'String'
    if type.isArray():
        return f'[{type.subtype.show()}]'
    if type.isNullable():
        return f'{type.subtype.show()}?'
    if type.isTuple():
        return '*'.join(t.show() for t in type.elements)
    if type.isFunc():
        return '->'.join(arg.type.show() for arg in type.args) + '->' + type.ret.show()
    if type == tUnknown:
        return '<Unknown>'
    return str(type)


@extend_class(ll.Type)
def default(type):
    return ll.Constant(type, 0 if type in (tInt, tFloat, tBool, tChar) else 'null')


def vInt(n):
    return ll.Constant(tInt, n)

def vFloat(f):
    return ll.Constant(tFloat, f)

def vBool(b):
    return ll.Constant(tBool, b)

vFalse = vBool(False)
vTrue = vBool(True)

def vChar(c):
    return ll.Constant(tChar, ord(c))

def vNull(type):
    return ll.Constant(type, 'null')

def vIndex(i):
    return ll.Constant(ll.IntType(32), i)
