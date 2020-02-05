
from . import types as t


class Value:

    def __init__(self, type=None):
        self.type = type


class Literal(Value):

    def __init__(self, value, formatter=None, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.formatter = formatter

    def __str__(self):
        if isinstance(self.formatter, str):
            return self.formatter.format(self.value)
        if callable(self.formatter):
            return self.formatter(self.value)
        return str(self.value)


def Int(x):
    return Literal(x, '{}LL', type=t.Int)

def Float(x):
    return Literal(x, type=t.Float)

def Bool(x):
    return Literal(x, lambda value: str(value).lower(), type=t.Bool)

false = Bool(False)
true = Bool(True)

def Char(x):
    return Literal(x, "'{}'", type=t.Char)

def String(x):
    return Literal(x, '"{}"s', type=t.String)


class Tuple(Value):

    def __init__(self, elements):
        type = t.Tuple([value.type for value in elements])
        super().__init__(type=type)
        self.elements = elements

    def __str__(self):
        elems = ', '.join(map(str, self.elements))
        return f'std::make_tuple({elems})'


class Variable(Value):

    def __init__(self, type, name):
        super().__init__(type)
        self.name = name

    def __str__(self):
        return self.name


class Attribute(Value):

    def __init__(self, value, attr, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.attr = attr

    def __str__(self):
        return f'{self.value}.{self.attr}'


class Index(Value):

    def __init__(self, collection, index, **kwargs):
        super().__init__(**kwargs)
        self.collection = collection
        self.index = index

    def __str__(self):
        return f'{self.collection}[{self.index}]'


class Call(Value):

    def __init__(self, func, *args, **kwargs):
        super().__init__(**kwargs)
        self.func = func
        self.args = args

    def __str__(self):
        args = ', '.join(map(str, self.args))
        return f'{self.func}({args})'


def Cast(value, type):
    return Call(f'static_cast<{type}>', value, type=type)


def Get(tuple, index):
    return Call(f'std::get<{index}>', tuple, type=tuple.type.elements[index])


class UnaryOperation(Value):

    def __init__(self, op, value, **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.value = value

    def __str__(self):
        return f'({self.op}{self.value})'


class BinaryOperation(Value):

    def __init__(self, value1, op, value2, **kwargs):
        super().__init__(**kwargs)
        self.value1 = value1
        self.op = op
        self.value2 = value2

    def __str__(self):
        return f'({self.value1} {self.op} {self.value2})'


class TernaryOperation(Value):

    def __init__(self, value1, op1, value2, op2, value3, **kwargs):
        super().__init__(**kwargs)
        self.value1 = value1
        self.op1 = op1
        self.value2 = value2
        self.op2 = op2
        self.value3 = value3

    def __str__(self):
        return f'({self.value1} {self.op1} {self.value2} {self.op2} {self.value3})'
