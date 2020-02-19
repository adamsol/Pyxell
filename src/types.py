
from collections import defaultdict, namedtuple

from .utils import *


class Type:
    pass


class PrimitiveType(Type):

    def __init__(self, pyxell_name, c_name=None):
        self.pyxell_name = pyxell_name
        self.c_name = c_name or pyxell_name

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


Void = PrimitiveType('Void')
Int = PrimitiveType('Int')
Float = PrimitiveType('Float')
Bool = PrimitiveType('Bool')
Char = PrimitiveType('Char')

String = PrimitiveType('String')
String.subtype = Char


class Array(Type):

    def __init__(self, subtype):
        super().__init__()
        self.subtype = subtype

    def __eq__(self, other):
        return isinstance(other, Array) and self.subtype == other.subtype

    def __hash__(self):
        return hash(Array)

    def __str__(self):
        return f'Array<{self.subtype}>'

    def show(self):
        return f'[{self.subtype.show()}]'


class Tuple(Type):

    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def __eq__(self, other):
        return isinstance(other, Tuple) and self.elements == other.elements

    def __hash__(self):
        return hash(Tuple)

    def __str__(self):
        elems = ', '.join(map(str, self.elements))
        return f'Tuple<{elems}>'

    def show(self):
        return '*'.join([t.show() for t in self.elements])


class Func(Type):

    Arg = namedtuple('Arg', ['type', 'name', 'default'])
    Arg.__new__.__defaults__ = (None,) * 3

    def __init__(self, args, ret=Void):
        super().__init__()
        self.args = [arg if isinstance(arg, Func.Arg) else Func.Arg(arg) for arg in args]
        self.ret = ret

    def __eq__(self, other):
        return isinstance(other, Func) and [arg.type for arg in self.args] == [arg.type for arg in other.args] and self.ret == other.ret

    def __hash__(self):
        return hash(Func)

    def __str__(self):
        args = ', '.join([str(arg.type) for arg in self.args])
        return f'std::function<{self.ret}({args})>'

    def show(self):
        return '->'.join([arg.type.show() for arg in self.args]) + '->' + self.ret.show()


class Var(Type):

    def __init__(self, name):
        super().__init__()
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name

    def __hash__(self):
        return hash(Var)

    def show(self):
        return self.name


Unknown = PrimitiveType('<Unknown>', 'void*')


@extend_class(Type)
def isArray(type):
    return isinstance(type, Array)


def Nullable(subtype):
    return NullableType(subtype)

@extend_class(Type)
def isNullable(type):
    return getattr(type, 'kind', None) == 'nullable'


@extend_class(Type)
def isTuple(type):
    return isinstance(type, Tuple)


@extend_class(Type)
def isFunc(type):
    return isinstance(type, Func)


def Class(context, name, base, members):
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


@extend_class(Type)
def isVar(type):
    return isinstance(type, Var)


@extend_class(Type)
def isCollection(type):
    return type == String or type.isArray()

@extend_class(Type)
def isUnknown(type):
    if type == Unknown:
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

    if type1 in {Int, Float} and type2 in {Int, Float}:
        return Float

    if type1.isArray() and type2.isArray():
        subtype = unify_types(type1.subtype, type2.subtype)
        return Array(subtype) if subtype else None

    if type1.isNullable() or type2.isNullable():
        subtype = unify_types(type1.subtype if type1.isNullable() else type1, type2.subtype if type2.isNullable() else type2)
        return Nullable(subtype) if subtype else None

    if type1.isTuple() and type2.isTuple():
        elems = [unify_types(t1, t2) for t1, t2 in zip(type1.elements, type2.elements)]
        return Tuple(elems) if all(elems) and len(type1.elements) == len(type2.elements) else None

    if type1.isClass() and type2.isClass():
        return common_superclass(type1, type2)

    if type1 == Unknown:
        return type2
    if type2 == Unknown:
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
            Tuple([arg.type for arg in type1.args] + [type1.ret]),
            Tuple([arg.type for arg in type2.args] + [type2.ret]))

    if type1.isClass() and type2.isClass():
        return {} if common_superclass(type1, type2) == type2 else None

    if type2.isVar():
        return {type2.name: type1}

    if type1 == Unknown or type2 == Unknown:
        return {}
    if type1 == Int and type2 == Float:
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
