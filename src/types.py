
import llvmlite.ir as ll


tVoid = ll.VoidType()
tInt = ll.IntType(64)
tBool = ll.IntType(1)
tChar = ll.IntType(8)

def tFunc(args, ret=tVoid):
    return ll.FunctionType(ret, args)


def showType(type):
    if type == tVoid:
        return 'Void'
    if type == tInt:
        return 'Int'
    if type == tBool:
        return 'Bool'
    if type == tChar:
        return 'Char'
    return str(type)

ll.Type.show = showType


vFalse = ll.Constant(tBool, 0)
vTrue = ll.Constant(tBool, 1)
