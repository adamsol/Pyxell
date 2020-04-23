
from collections import defaultdict, namedtuple


class Type:

    def __eq__(self, other):
        return type(self) == type(other) and self.eq(other)

    def __hash__(self):
        return hash(Type)

    def eq(self, other):
        return False

    def isNumber(self):
        return self in {Int, Rat, Float}

    def isArray(self):
        return isinstance(self, Array)

    def isSet(self):
        return isinstance(self, Set)

    def isDict(self):
        return isinstance(self, Dict)

    def isGenerator(self):
        return isinstance(self, Generator)

    def isNullable(self):
        return isinstance(self, Nullable)

    def isTuple(self):
        return isinstance(self, Tuple)

    def isFunc(self):
        return isinstance(self, Func)

    def isClass(self):
        return isinstance(self, Class)

    def isVar(self):
        return isinstance(self, Var)

    def isUnknown(self):
        if self == Unknown:
            return True
        if self.isContainer():
            return self.subtype.isUnknown()
        if self.isNullable():
            return self.subtype.isUnknown()
        if self.isTuple():
            return any(elem.isUnknown() for elem in self.elements)
        if self.isFunc():
            return any(arg.type.isUnknown() for arg in self.args) or self.ret.isUnknown()
        return False

    def isSequence(self):
        return self == String or self.isArray()

    def isContainer(self):
        return self.isArray() or self.isSet() or self.isDict()

    def isCollection(self):
        return self.isSequence() or self.isContainer()

    def isIterable(self):
        return self.isCollection() or self.isGenerator()

    def isHashable(self):
        if self.isNumber() or self in {Bool, Char, String, Unknown}:
            return True
        if self.isContainer():
            return False
        if self.isNullable():
            return self.subtype.isHashable()
        if self.isTuple():
            return all(elem.isHashable() for elem in self.elements)
        if self.isClass():
            return True
        return False

    def isPrintable(self):
        if self.isNumber() or self in {Bool, Char, String, Unknown}:
            return True
        if self.isContainer():
            return self.subtype.isPrintable()
        if self.isNullable():
            return self.subtype.isPrintable()
        if self.isTuple():
            return all(elem.isPrintable() for elem in self.elements)
        if self.isClass():
            return 'toString' in self.methods
        return False

    def isOrderable(self):
        return self.isNumber() or self in {Char, Bool, String} or self.isArray() or self.isTuple()

    def isComparable(self):
        return self.isOrderable() or self.isSet() or self.isDict() or self.isClass()

    def hasValue(self):
        return self != Void and not self.isGenerator()


class PrimitiveType(Type):

    def __init__(self, pyxell_name, c_name=None):
        self.pyxell_name = pyxell_name
        self.c_name = c_name or pyxell_name

    def __str__(self):
        return self.c_name

    def show(self):
        return self.pyxell_name

    def eq(self, other):
        return self.pyxell_name == other.pyxell_name


Void = PrimitiveType('Void')
Int = PrimitiveType('Int')
Rat = PrimitiveType('Rat')
Float = PrimitiveType('Float')
Bool = PrimitiveType('Bool')
Char = PrimitiveType('Char')

String = PrimitiveType('String')
String.subtype = Char


class Wrapper(Type):

    def __init__(self, subtype):
        super().__init__()
        self.subtype = subtype

    def eq(self, other):
        return self.subtype == other.subtype


class Array(Wrapper):

    def __str__(self):
        return f'Array<{self.subtype}>'

    def show(self):
        return f'[{self.subtype.show()}]'


class Set(Wrapper):

    def __str__(self):
        return f'Set<{self.subtype}>'

    def show(self):
        return f'{{{self.subtype.show()}}}'


class Dict(Wrapper):

    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type
        super().__init__(Tuple([self.key_type, self.value_type]))

    def __str__(self):
        return f'Dict<{self.key_type}, {self.value_type}>'

    def show(self):
        return f'{{{self.key_type.show()}:{self.value_type.show()}}}'


class Generator(Wrapper):

    def __str__(self):
        return f'cppcoro::generator<{self.subtype}>'

    def show(self):
        return f'Generator<{self.subtype.show()}>'


class Nullable(Wrapper):

    def __str__(self):
        return f'Nullable<{self.subtype}>'

    def show(self):
        return f'{self.subtype.show()}?'


class Tuple(Type):

    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def __str__(self):
        elems = ', '.join(map(str, self.elements))
        return f'Tuple<{elems}>'

    def show(self):
        return '*'.join([t.show() for t in self.elements])

    def eq(self, other):
        return self.elements == other.elements


class Func(Type):

    Arg = namedtuple('Arg', ['type', 'name', 'default'])
    Arg.__new__.__defaults__ = (None,) * 3

    def __init__(self, args, ret=Void):
        super().__init__()
        self.args = [arg if isinstance(arg, Func.Arg) else Func.Arg(arg) for arg in args]
        self.ret = ret

    def args_str(self):
        return ', '.join([str(arg.type) for arg in self.args])

    def __str__(self):
        return f'std::function<{self.ret}({self.args_str()})>'

    def show(self):
        return '->'.join([arg.type.show() for arg in self.args]) + '->' + self.ret.show()

    def eq(self, other):
        return [arg.type for arg in self.args] == [arg.type for arg in other.args] and self.ret == other.ret


class Class(Type):

    def __init__(self, name, base, members, methods):
        super().__init__()
        self.name = name
        self.base = base
        self.members = members
        self.methods = methods
        self.initializer = None
        self.type = Type()

    def __str__(self):
        return f'Object<{self.initializer.name}>'

    def show(self):
        return self.name

    def eq(self, other):
        return self.name == other.name


class Var(Type):

    def __init__(self, name):
        super().__init__()
        self.name = name

    def show(self):
        return self.name

    def eq(self, other):
        return self.name == other.name


Unknown = PrimitiveType('<unknown>', 'Unknown')


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

    if type1 in {Int, Rat} and type2 in {Int, Rat}:
        return Rat

    if type1 in {Int, Rat, Float} and type2 in {Int, Rat, Float}:
        return Float

    if type1.isArray() and type2.isArray():
        subtype = unify_types(type1.subtype, type2.subtype)
        return Array(subtype) if subtype else None

    if type1.isSet() and type2.isSet():
        subtype = unify_types(type1.subtype, type2.subtype)
        return Set(subtype) if subtype else None

    if type1.isDict() and type2.isDict():
        key_type = unify_types(type1.key_type, type2.key_type)
        value_type = unify_types(type1.value_type, type2.value_type)
        return Dict(key_type, value_type) if key_type and value_type else None

    if type1.isGenerator() and type2.isGenerator():
        subtype = unify_types(type1.subtype, type2.subtype)
        return Generator(subtype) if subtype else None

    if type1.isNullable() or type2.isNullable():
        subtype = unify_types(type1.subtype if type1.isNullable() else type1, type2.subtype if type2.isNullable() else type2)
        return Nullable(subtype) if subtype else None

    if type1.isTuple() and type2.isTuple():
        elems = [unify_types(t1, t2) for t1, t2 in zip(type1.elements, type2.elements)]
        return Tuple(elems) if all(elems) and len(type1.elements) == len(type2.elements) else None

    if type1.isClass() and type2.isClass():
        return common_superclass(type1, type2)

    if type1.isVar():
        return type2
    if type2.isVar():
        return type1

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


def type_variables_assignment(type1, type2, conversion_allowed=True, covariance=True):

    if type1.isArray() and type2.isArray():
        return type_variables_assignment(type1.subtype, type2.subtype, conversion_allowed=covariance)
    if type1.isSet() and type2.isSet():
        return type_variables_assignment(type1.subtype, type2.subtype, conversion_allowed=covariance)
    if type1.isDict() and type2.isDict():
        return type_variables_assignment(type1.subtype, type2.subtype, conversion_allowed=covariance)
    if type1.isGenerator() and type2.isGenerator():
        return type_variables_assignment(type1.subtype, type2.subtype, conversion_allowed=covariance)

    if type1.isNullable() and type2.isNullable():
        return type_variables_assignment(type1.subtype, type2.subtype, conversion_allowed, covariance)
    if not type1.isNullable() and type2.isNullable() and conversion_allowed:
        return type_variables_assignment(type1, type2.subtype, conversion_allowed, covariance)

    if type1.isTuple() and type2.isTuple():
        if len(type1.elements) != len(type2.elements):
            return None
        type_lists = defaultdict(list)
        for e1, e2 in zip(type1.elements, type2.elements):
            d = type_variables_assignment(e1, e2, conversion_allowed, covariance)
            if d is None:
                return None
            for name, type in d.items():
                type_lists[name].append(type)
        result = {}
        for name, types in type_lists.items():
            type = unify_types(*types)
            if type is None:
                return None
            result[name] = type
            for t in types:
                if t.isVar():
                    result[t.name] = type
        return result

    if type1.isFunc() and type2.isFunc():
        return type_variables_assignment(
            Tuple([arg.type for arg in type1.args] + [type1.ret]),
            Tuple([arg.type for arg in type2.args] + [type2.ret]),
            conversion_allowed)

    if type1.isClass() and type2.isClass() and conversion_allowed:
        return {} if common_superclass(type1, type2) == type2 else None

    if type2.isVar():
        return {type2.name: type1}

    if type1 == Unknown:
        return {}
    if type1 == Int and type2 == Rat and conversion_allowed:
        return {}
    if type1 in {Int, Rat} and type2 == Float and conversion_allowed:
        return {}
    if type1 == type2:
        return {}

    return None


def get_type_variables(type):
    # For this to work properly, the condition `type1 == type2` in `type_variables_assignment` must be at the bottom.
    return type_variables_assignment(type, type).keys()


def can_cast(type1, type2, covariance=True):
    return type_variables_assignment(type1, type2, covariance=covariance) == {}
