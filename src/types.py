
import llvmlite.ir as ll

from .utils import extend_class


class CustomStructType(ll.LiteralStructType):

    def __init__(self, elements, kind):
        super().__init__(elements)
        self.kind = kind

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self.kind == other.kind


tVoid = ll.VoidType()
tInt = ll.IntType(64)
tFloat = ll.DoubleType()
tBool = ll.IntType(1)
tChar = ll.IntType(8)


def tPtr(type=tChar):
    return type.as_pointer()


tString = CustomStructType([tPtr(), tInt], 'string')
tString.subtype = tChar

@extend_class(ll.Type)
def isString(type):
    return getattr(type, 'kind', None) == 'string'


def tArray(subtype):
    type = CustomStructType([tPtr(subtype), tInt], 'array')
    type.subtype = subtype
    return type

@extend_class(ll.Type)
def isArray(type):
    return getattr(type, 'kind', None) == 'array'


def tTuple(elements):
    if len(elements) == 1:
        return elements[0]
    return CustomStructType(elements, 'tuple')

@extend_class(ll.Type)
def isTuple(type):
    return getattr(type, 'kind', None) == 'tuple'


def tFunc(args, ret=tVoid):
    type = tPtr(ll.FunctionType(ret, args))
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
    if type.isTuple():
        return '*'.join(t.show() for t in type.elements)
    if type.isFunc():
        return '->'.join(t.show() for t in type.args) + '->' + type.ret.show()
    return str(type)


@extend_class(ll.Type)
def default(type):
    return ll.Constant(type, 0 if type in (tInt, tFloat, tBool, tChar) else 'null')


def vInt(n):
    return ll.Constant(tInt, str(n))

def vFloat(f):
    return ll.Constant(tFloat, str(f))

def vBool(b):
    return ll.Constant(tBool, int(b))

vFalse = vBool(False)
vTrue = vBool(True)

def vChar(c):
    return ll.Constant(tChar, ord(c))

def vNull(type=tChar):
    return ll.Constant(tPtr(type), 'null')

def vIndex(i):
    return ll.Constant(ll.IntType(32), i)
