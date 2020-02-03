
from collections import defaultdict, namedtuple

from .utils import *


__all__ = [
    'Type',
    'tVoid', 'tInt', 'tFloat', 'tBool', 'tChar',
    'unify_types', 'type_variables_assignment', 'get_type_variables', 'can_cast',
]


class Type:
    pass


class PrimitiveType(Type):

    def __init__(self, pyxell_name, c_name):
        self.pyxell_name = pyxell_name
        self.c_name = c_name

    def __eq__(self, other):
        if not isinstance(other, PrimitiveType):
            return False
        return self.pyxell_name == other.pyxell_name

    def __hash__(self):
        return hash(self.pyxell_name)

    def __str__(self):
        return self.c_name

    def show(self):
        return self.pyxell_name


class VariableType(Type):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.kind = 'variable'

    def __eq__(self, other):
        return isinstance(other, VariableType) and self.name == other.name

    def __hash__(self):
        return hash(VariableType)


class UnknownType(Type):

    def _to_string(self):
        return 'i8*'

    def __eq__(self, other):
        return isinstance(other, UnknownType)

    def __hash__(self):
        return hash(UnknownType)


tVoid = PrimitiveType('Void', 'void')
tInt = PrimitiveType('Int', 'long long')
tFloat = PrimitiveType('Float', 'double')
tBool = PrimitiveType('Bool', 'bool')
tChar = PrimitiveType('Char', 'char')


def tPtr(type=tChar):
    ptr_type = type.as_pointer()
    ptr_type.kind = getattr(type, 'kind', None)
    return ptr_type


# tString = tPtr(CustomStructType([tPtr(), tInt], 'string'))
# tString.subtype = tChar

@extend_class(Type)
def isString(type):
    return getattr(type, 'kind', None) == 'string'


def tArray(subtype):
    type = tPtr(CustomStructType([tPtr(subtype), tInt], 'array'))
    type.subtype = subtype
    return type

@extend_class(Type)
def isArray(type):
    return getattr(type, 'kind', None) == 'array'


def tNullable(subtype):
    return NullableType(subtype)

@extend_class(Type)
def isNullable(type):
    return getattr(type, 'kind', None) == 'nullable'


def tTuple(elements):
    type = tPtr(CustomStructType(elements, 'tuple'))
    type.elements = elements
    return type

@extend_class(Type)
def isTuple(type):
    return getattr(type, 'kind', None) == 'tuple'


Arg = namedtuple('Arg', ['type', 'name', 'default'])
Arg.__new__.__defaults__ = (None,) * 3

def tFunc(args, ret=tVoid):
    args = [arg if isinstance(arg, Arg) else Arg(arg) for arg in args]
    type = tPtr(ll.FunctionType(ret, [arg.type for arg in args]))
    type.args = args
    type.ret = ret
    type.kind = 'function'
    return type

@extend_class(Type)
def isFunc(type):
    return getattr(type, 'kind', None) == 'function'


def tClass(context, name, base, members):
    type = tPtr(context.get_identified_type(name))
    type.kind = 'class'
    type.name = name
    type.base = base
    type.members = members
    type.methods = None
    type.constructor = None
    return type

@extend_class(Type)
def isClass(type):
    return getattr(type, 'kind', None) == 'class'


def tVar(name):
    return VariableType(name)

@extend_class(Type)
def isVar(type):
    return getattr(type, 'kind', None) == 'variable'


@extend_class(Type)
def isCollection(type):
    return type == tString or type.isArray()


tUnknown = UnknownType()

@extend_class(Type)
def isUnknown(type):
    if type == tUnknown:
        return True
    if type.isArray():
        return type.subtype.isUnknown()
    if type.isNullable():
        return type.subtype.isUnknown()
    if type.isTuple():
        return any(elem.isUnknown() for elem in type.elements)
    if type.isFunc():
        return any(arg.type.isUnknown() for arg in type.args) or type.ret.isUnknown()
    return False


def unify_types(type1, *types):
    if not types:
        return type1

    type2, *types = types
    if types:
        return unify_types(unify_types(type1, type2), *types)

    if type1 is None or type2 is None:
        return None

    if type1 == type2:
        return type1

    if type1 in {tInt, tFloat} and type2 in {tInt, tFloat}:
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

    if type1.isClass() and type2.isClass():
        return common_superclass(type1, type2)

    if type1 == tUnknown:
        return type2
    if type2 == tUnknown:
        return type1

    return None


def common_superclass(type1, type2):
    t1 = type1
    t2 = type2

    while True:
        if t1 == t2:
            return t1

        if t1.base and t2.base:
            t1 = t1.base
            t2 = t2.base
        elif t1.base:
            t1 = t1.base
            t2 = type2
        elif t2.base:
            t1 = type1
            t2 = t2.base
        else:
            return None


def type_variables_assignment(type1, type2):

    if type1.isArray() and type2.isArray():
        return type_variables_assignment(type1.subtype, type2.subtype)

    if type1.isNullable() and type2.isNullable():
        return type_variables_assignment(type1.subtype, type2.subtype)

    if type2.isNullable():
        return type_variables_assignment(type1, type2.subtype)

    if type1.isTuple() and type2.isTuple():
        if len(type1.elements) != len(type2.elements):
            return None
        result = defaultdict(list)
        for e1, e2 in zip(type1.elements, type2.elements):
            d = type_variables_assignment(e1, e2)
            if d is None:
                return None
            for name, type in d.items():
                result[name].append(type)
        for name, types in result.items():
            type = unify_types(*types)
            if type is None:
                return None
            result[name] = type
        return result

    if type1.isFunc() and type2.isFunc():
        return type_variables_assignment(
            tTuple([arg.type for arg in type1.args] + [type1.ret]),
            tTuple([arg.type for arg in type2.args] + [type2.ret]))

    if type1.isClass() and type2.isClass():
        return {} if common_superclass(type1, type2) == type2 else None

    if type2.isVar():
        return {type2.name: type1}

    if type1 == tUnknown or type2 == tUnknown:
        return {}
    if type1 == tInt and type2 == tFloat:
        return {}
    if type1 == type2:
        return {}

    return None


def get_type_variables(type):
    # For this to work properly, the condition `type1 == type2` in `type_variables_assignment` must be at the bottom.
    return type_variables_assignment(type, type).keys()


def can_cast(type1, type2):
    if type1.isArray() and type2.isArray():
        return type1.subtype == type2.subtype or type1.subtype.isUnknown()
    if not type1.isNullable() and type2.isNullable():
        return can_cast(type1, type2.subtype)
    return type_variables_assignment(type1, type2) == {}
