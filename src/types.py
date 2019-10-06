
import llvmlite.ir as ll


tVoid = ll.VoidType()
tInt = ll.IntType(64)
tBool = ll.IntType(1)
tChar = ll.IntType(8)

def tTuple(elements):
    type = ll.LiteralStructType(elements)
    type.kind = 'tuple'
    return type

def tFunc(args, ret=tVoid):
    return ll.FunctionType(ret, args)

def tPtr(type=tChar):
    return type.as_pointer()


def isTuple(type):
    return getattr(type, 'kind', None) == 'tuple'

ll.Type.isTuple = isTuple


def showType(type):
    if type == tVoid:
        return 'Void'
    if type == tInt:
        return 'Int'
    if type == tBool:
        return 'Bool'
    if type == tChar:
        return 'Char'
    if type.isTuple():
        return '*'.join(t.show() for t in type.elements)
    return str(type)

ll.Type.show = showType


def vInt(n):
    return ll.Constant(tInt, n)

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
