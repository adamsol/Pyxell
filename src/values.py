
from . import types as t


class Value:

    def __init__(self, type=None):
        self.type = type

    def isTemplate(value):
        return isinstance(value, FunctionTemplate)


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
    return Literal(int(x), '{}LL', type=t.Int)

def Rat(x):
    return Literal(int(x), 'Rat({}LL)', type=t.Rat)

def Float(x):
    return Literal(float(x), type=t.Float)

def Bool(x):
    return Literal(bool(x), lambda value: str(value).lower(), type=t.Bool)

false = Bool(False)
true = Bool(True)

def Char(x):
    return Literal(str(x), "'{}'", type=t.Char)

def String(x):
    return Literal(str(x), 'make_string("{}")', type=t.String)


class Variable(Value):

    def __init__(self, type, name):
        super().__init__(type)
        self.name = name

    def __str__(self):
        return self.name


class Container(Value):

    def __init__(self, type, elements, formatter):
        super().__init__(type)
        self.elements = elements
        self.formatter = formatter

    def __str__(self):
        return self.formatter.format(', '.join(map(str, self.elements)))


class Array(Container):

    def __init__(self, elements, subtype=None):
        type = t.Array(subtype or (elements[0].type if elements else t.Unknown))
        super().__init__(type, elements, f'make_array<{type.subtype}>' + '({{{}}})')


class Set(Container):

    def __init__(self, elements, subtype=None):
        type = t.Set(subtype or (elements[0].type if elements else t.Unknown))
        super().__init__(type, elements, f'make_set<{type.subtype}>' + '({{{}}})')


class Dict(Container):

    def __init__(self, keys, values, key_type=None, value_type=None):
        type = t.Dict(key_type or (keys[0].type if keys else t.Unknown),
                      value_type or (values[0].type if values else t.Unknown))
        elements = [f'{{{key}, {value}}}' for key, value in zip(keys, values)]
        super().__init__(type, elements, f'make_dict<{type.key_type}, {type.value_type}>' + '({{{}}})')
        self.keys = keys
        self.values = values


class Nullable(Value):

    def __init__(self, value, subtype=None):
        super().__init__(t.Nullable(subtype or (value.type if value else t.Unknown)))
        self.value = value

    def __str__(self):
        arg = str(self.value or '')
        return f'{self.type}({arg})'


null = Nullable(None)


class Tuple(Container):

    def __init__(self, elements):
        type = t.Tuple([value.type for value in elements])
        super().__init__(type, elements, 'std::make_tuple({})')


class Object(Value):

    def __init__(self, cls):
        super().__init__(cls)

    def __str__(self):
        return f'std::make_shared<{self.type.initializer.name}>()'


class FunctionTemplate(Value):

    def __init__(self, id, typevars, type, body, env, lambda_=False):
        super().__init__(type)
        self.id = id
        self.final = True  # identifier cannot be redefined
        self.typevars = typevars
        self.body = body
        self.env = env
        self.lambda_ = lambda_
        self.compiled = {}


class Attribute(Value):

    def __init__(self, value, attr, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.attr = attr

    def __str__(self):
        op = '.' if self.value.type.isGenerator() or self.value.type.isNullable() else '->'
        return f'{self.value}{op}{self.attr}'


class Index(Value):

    def __init__(self, collection, index, **kwargs):
        super().__init__(**kwargs)
        self.collection = collection
        self.index = index

    def __str__(self):
        return f'{Dereference(self.collection)}[{self.index}]'


class Call(Value):

    def __init__(self, func, *args, **kwargs):
        super().__init__(**kwargs)
        self.func = func
        self.args = args

    def __str__(self):
        args = ', '.join(map(str, self.args))
        return f'{self.func}({args})'


def Cast(value, type):
    if value.type == type:
        return value
    return Call(f'static_cast<{type}>', value, type=type)

def Get(tuple, index):
    return Call(f'std::get<{index}>', tuple, type=tuple.type.elements[index])

def Dereference(value, type=None):
    return UnaryOperation('*', value, type=type)

def Extract(value):
    return Dereference(value, type=value.type.subtype)

def IsNotNull(value):
    return Call(Attribute(value, 'has_value'), type=t.Bool)

def IsNull(value):
    return UnaryOperation('!', IsNotNull(value), type=t.Bool)


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


class Condition(Value):

    def __init__(self, value1, value2, value3, **kwargs):
        super().__init__(**kwargs)
        self.value1 = value1
        self.value2 = value2
        self.value3 = value3

    def __str__(self):
        return f'({self.value1} ? {self.value2} : {self.value3})'


class Lambda(Value):

    def __init__(self, type, arg_vars, body):
        super().__init__(type)
        self.arg_vars = arg_vars

        if isinstance(body, Value):
            body = f'{{ return {body}; }}'
        self.body = body

    def __str__(self):
        args = ', '.join([f'{arg.type} {var}' for arg, var in zip(self.type.args, self.arg_vars)])
        return f'[=]({args}) mutable {self.body}'
