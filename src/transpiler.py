
import ast
import copy
import re
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from functools import partial

from . import codegen as c
from . import types as t
from . import values as v
from .errors import NotSupportedError, PyxellError as err
from .parser import PyxellParser
from .types import can_cast, has_type_variables, type_variables_assignment, unify_types
from .utils import lmap


class Unit:

    def __init__(self, name, filepath):
        self.name = name
        self.filepath = filepath
        self.env = {'#loops': {}}

    def __repr__(self):
        return f"Unit('{self.name}', '{self.filepath}')"


class PyxellTranspiler:

    def __init__(self, cpp_compiler):
        self.cpp_compiler = cpp_compiler

        self.required_features = set()
        self.units = {}
        self.current_unit = None
        self.sequence_number = 0
        self.const_cache = {}
        self.current_block = c.Block()

        self.module_declarations = c.Collection()
        self.module_definitions = c.Collection()
        self.main = c.Function('int', 'main', [], self.current_block)

        self.module = c.Collection(
            self.module_declarations,
            self.module_definitions,
            self.main,
        )

    def run(self, ast, unit, filepath):
        self.units[unit] = Unit(unit, filepath)
        with self.unit(unit):
            if unit != 'std':
                self.env = self.units['std'].env.copy()
            self.transpile(ast)

    def run_main(self, ast, filepath):
        self.run(ast, 'main', filepath)
        self.output(c.Statement('return 0'))
        if 'generators' in self.required_features and 'clang' not in self.cpp_compiler:
            raise NotSupportedError(f"Generators require C++ coroutines support; use Clang.")
        return str(self.module)

    def transpile(self, node, void_allowed=False):
        if not isinstance(node, dict):
            return node
        node = self.convert_lambda(node)
        result = getattr(self, 'transpile'+node['node'])(node)
        if isinstance(result, v.Value) and result.type == t.Void and not void_allowed:
            self.throw(node, err.UnexpectedVoid())
        if '_eval' in node:
            node['_eval'] = node['_eval']()
        return result

    def throw(self, node, msg):
        raise err(self.current_unit.filepath, node['position'], msg)

    def require(self, feature):
        if feature not in {'generators'}:
            raise ValueError(feature)
        self.required_features.add(feature)


    ### Helpers ###

    @property
    def env(self):
        return self.current_unit.env

    @env.setter
    def env(self, env):
        self.current_unit.env = env

    @contextmanager
    def local(self):
        env = self.env.copy()
        yield
        self.env = env

    @contextmanager
    def unit(self, name):
        _unit = self.current_unit
        self.current_unit = self.units[name]
        try:
            yield
        finally:
            self.current_unit = _unit

    @contextmanager
    def block(self, block):
        _block = self.current_block
        self.current_block = block
        yield
        self.current_block = _block

    @contextmanager
    def no_output(self):
        with self.block(c.Block()):
            yield

    def output(self, stmt, toplevel=False):
        if isinstance(stmt, (v.Value, c.Var, c.Const, c.Label)):
            stmt = c.Statement(stmt)

        if toplevel:
            if isinstance(stmt, (c.Function, c.Struct)):
                self.module_definitions.append(stmt)
            else:
                self.module_declarations.append(stmt)
        else:
            self.current_block.append(stmt)

    def resolve_type(self, type):
        if type.isVar():
            return self.env.get(type.name, type)
        if type.isArray():
            return t.Array(self.resolve_type(type.subtype))
        if type.isSet():
            return t.Set(self.resolve_type(type.subtype))
        if type.isDict():
            return t.Dict(self.resolve_type(type.key_type), self.resolve_type(type.value_type))
        if type.isGenerator():
            return t.Generator(self.resolve_type(type.subtype))
        if type.isNullable():
            return t.Nullable(self.resolve_type(type.subtype))
        if type.isTuple():
            return t.Tuple([self.resolve_type(type) for type in type.elements])
        if type.isFunc():
            return t.Func([arg._replace(type=self.resolve_type(arg.type)) for arg in type.args], self.resolve_type(type.ret))
        return type

    def fake_name(self, prefix='$id'):
        self.sequence_number += 1
        return f'{prefix}{self.sequence_number}'


    ### Code generation ###

    def get(self, node, id):
        if id not in self.env:
            self.throw(node, err.UndeclaredIdentifier(id))

        result = self.env[id]

        if isinstance(result, t.Class):
            if None in result.methods.values():
                self.throw(node, err.AbstractClass(result))
            return result

        if not isinstance(result, v.Value):
            self.throw(node, err.NotVariable(id))

        if result.isTemplate() and not result.typevars:
            result = self.function(result)

        return result

    def default(self, type):
        if type == t.Int:
            return v.Int(0)
        if type == t.Rat:
            return self.rat(0)
        if type == t.Float:
            return v.Float(0)
        if type == t.Bool:
            return v.false
        if type == t.Char:
            return v.Char('\0')
        if type == t.String:
            return self.string('')
        if type.isArray():
            return v.Array([], type.subtype)
        if type.isSet():
            return v.Set([], type.subtype)
        if type.isDict():
            return v.Dict([], [], type.key_type, type.value_type)
        if type.isNullable():
            return v.Nullable(None, type.subtype)
        if type.isTuple():
            return v.Tuple([self.default(t) for t in type.elements])
        if type.isFunc():
            return v.Lambda(type, [''] * len(type.args), self.default(type.ret) if type.ret != t.Void else c.Block())
        if type.isClass():
            return v.Literal('nullptr', type=type)

    def index(self, node, collection, index, lvalue=False):
        exprs = node['exprs']

        if collection.type.isSequence() or collection.type.isDict():
            if lvalue and collection.type == t.String:
                self.throw(node, err.NotLvalue())

            collection = self.tmp(collection)

            if collection.type.isSequence():
                index = self.tmp(self.cast(exprs[1], index, t.Int))
                index = v.TernaryOp(
                    v.BinaryOp(index, '<', v.Int(0)),
                    v.BinaryOp(self.attr(node, collection, 'length'), '+', index),
                    index)
                return v.Index(collection, index, type=collection.type.subtype)

            if collection.type.isDict():
                index = self.cast(exprs[1], index, collection.type.key_type)
                type = collection.type.value_type

                iterator = self.tmp(v.Call(v.Attribute(collection, 'find'), index, type=t.Iterator(collection.type)))
                end = v.Call(v.Attribute(collection, 'end'))

                block = c.Block()
                self.output(c.If(f'{iterator} == {end}', block))
                with self.block(block):
                    default = self.default(type)
                    self.output(c.Statement(iterator, '=', v.Call(v.Attribute(collection, 'insert_or_assign'), iterator, index, default)))

                return v.Attribute(iterator, 'second', type=type)

        self.throw(node['op'], err.NotIndexable(collection.type))

    def cond(self, node, pred, callback_true, callback_false):
        pred = self.cast(node['op'], pred, t.Bool)

        block_true = c.Block()
        block_false = c.Block()

        with self.block(block_true):
            value_true = callback_true()
        with self.block(block_false):
            value_false = callback_false()

        type = unify_types(value_true.type, value_false.type)
        if type is None:
            self.throw(node['op'], err.IncompatibleTypes(value_true.type, value_false.type))

        result = self.var(type)
        self.output(c.Var(result))

        with self.block(block_true):
            self.store(result, value_true)
        with self.block(block_false):
            self.store(result, value_false)

        self.output(c.If(pred, block_true, block_false))

        return result

    def safe(self, node, value, callback_notnull, callback_null):
        if not value.type.isNullable():
            self.throw(node['op'], err.NotNullable(value.type))

        return self.cond(node, v.IsNotNull(value), callback_notnull, callback_null)

    def attribute(self, node, expr, attr, for_print=False):
        if expr['node'] == 'AtomId':
            module_name = expr['name']
            if module_name in self.units:
                try:
                    with self.unit(module_name):
                        return self.get(node, attr)
                except err:
                    self.throw(node['op'], err.NoIdentifier(module_name, attr))

        obj = self.tmp(self.transpile(expr))
        return self.attr(node, obj, attr, for_print)

    def attr(self, node, obj, attr, for_print=False):
        type = obj.type
        value = None

        if attr == 'toString' and type.isPrintable():
            if type in {t.Char, t.String}:
                # Value shouldn't be wrapped in quotes.
                value = v.Cast(obj, t.String)
                if not for_print:
                    value = v.Lambda(t.Func([], t.String), [], value)
            elif type.isClass():
                value = self.member(node, obj, 'toString')
            else:
                value = v.Variable(t.Func([type], t.String), 'toString')

        elif attr == 'toInt' and type in {t.Rat, t.Float, t.String}:
            value = v.Variable(t.Func([type], t.Int), 'toInt')
        elif attr == 'toRat' and type == t.String:
            value = v.Variable(t.Func([type], t.Rat), 'toRat')
        elif attr == 'toFloat' and type == t.String:
            value = v.Variable(t.Func([type], t.Float), 'toFloat')

        elif attr == 'fraction' and type == t.Rat:
            value = v.Tuple([v.Cast(v.Attribute(obj, 'numerator'), t.Rat), v.Cast(v.Attribute(obj, 'denominator'), t.Rat)])

        elif attr == 'char' and type == t.Int:
            value = v.Cast(obj, t.Char)
        elif attr == 'code' and type == t.Char:
            value = v.Cast(obj, t.Int)

        elif type.isCollection():
            if attr == 'length':
                value = v.Cast(v.Call(v.Attribute(obj, 'size')), t.Int)
            elif attr == 'empty':
                value = v.Call(v.Attribute(obj, 'empty'), type=t.Bool)

            elif type == t.String:
                value = {
                    'all': self.env['String_all'],
                    'any': self.env['String_any'],
                    'filter': self.env['String_filter'],
                    'map': self.env['String_map'],
                    'fold': self.env['String_fold'],
                    'reduce': self.env['String_reduce'],
                    'get': v.Variable(t.Func([type, t.Int], t.Nullable(t.Char)), attr),
                    'split': v.Variable(t.Func([type, type], t.Array(type)), attr),
                    'find': v.Variable(t.Func([type, type, t.Func.Arg('start', t.Int, default=v.Int(0))], t.Nullable(t.Int)), attr),
                    'count': v.Variable(t.Func([type, type.subtype], t.Int), attr),
                    'startsWith': v.Variable(t.Func([type, type], t.Bool), attr),
                    'endsWith': v.Variable(t.Func([type, type], t.Bool), attr),
                }.get(attr)

            elif attr == 'join' and type.isArray() and type.subtype in {t.Char, t.String, t.Unknown}:
                value = v.Variable(t.Func([type, t.Func.Arg('sep', t.String, default=self.string(''))], t.String), attr)

            elif type.isArray():
                value = {
                    'all': self.env['Array_all'],
                    'any': self.env['Array_any'],
                    'filter': self.env['Array_filter'],
                    'map': self.env['Array_map'],
                    'fold': self.env['Array_fold'],
                    'reduce': self.env['Array_reduce'],
                    'push': v.Variable(t.Func([type, type.subtype]), attr),
                    'insert': v.Variable(t.Func([type, t.Int, type.subtype]), attr),
                    'extend': v.Variable(t.Func([type, type]), attr),
                    'get': v.Variable(t.Func([type, t.Int], t.Nullable(type.subtype)), attr),
                    'pop': v.Variable(t.Func([type], type.subtype), attr),
                    'erase': v.Variable(t.Func([type, t.Int, t.Func.Arg('count', t.Int, default=v.Int(1))]), attr),
                    'clear': v.Variable(t.Func([type]), attr),
                    'reverse': v.Variable(t.Func([type]), attr),
                    'sort': v.Variable(t.Func([type, t.Func.Arg('reverse', t.Bool, default=v.false), t.Func.Arg('key', t.Func([type.subtype], t.Var('K')), default={'node': 'AtomPlaceholder'})], type), attr),
                    'copy': v.Variable(t.Func([type], type), attr),
                    'find': v.Variable(t.Func([type, type.subtype, t.Func.Arg('start', t.Int, default=v.Int(0))], t.Nullable(t.Int)), attr),
                    'count': v.Variable(t.Func([type, type.subtype], t.Int), attr),
                }.get(attr)

            elif type.isSet():
                value = {
                    'all': self.env['Set_all'],
                    'any': self.env['Set_any'],
                    'filter': self.env['Set_filter'],
                    'map': self.env['Set_map'],
                    'fold': self.env['Set_fold'],
                    'reduce': self.env['Set_reduce'],
                    'add': v.Variable(t.Func([type, type.subtype]), attr),
                    'union': v.Variable(t.Func([type, type]), 'union_'),
                    'subtract': v.Variable(t.Func([type, type]), attr),
                    'intersect': v.Variable(t.Func([type, type]), attr),
                    'pop': v.Variable(t.Func([type], type.subtype), attr),
                    'remove': v.Variable(t.Func([type, type.subtype]), attr),
                    'clear': v.Variable(t.Func([type]), attr),
                    'copy': v.Variable(t.Func([type], type), attr),
                }.get(attr)

            elif type.isDict():
                value = {
                    'all': self.env['Dict_all'],
                    'any': self.env['Dict_any'],
                    'filter': self.env['Dict_filter'],
                    'map': self.env['Dict_map'],
                    'fold': self.env['Dict_fold'],
                    'reduce': self.env['Dict_reduce'],
                    'update': v.Variable(t.Func([type, type]), attr),
                    'get': v.Variable(t.Func([type, type.key_type], t.Nullable(type.value_type)), attr),
                    'remove': v.Variable(t.Func([type, type.key_type]), attr),
                    'clear': v.Variable(t.Func([type]), attr),
                    'copy': v.Variable(t.Func([type], type), attr),
                }.get(attr)

        elif type.isTuple() and len(attr) == 1:
            index = ord(attr) - ord('a')
            if 0 <= index < len(type.elements):
                value = v.Get(obj, index)

        elif type.isClass():
            value = self.member(node, obj, attr)

        if value is None:
            self.throw(node['op'], err.NoAttribute(type, attr))

        if value.type.isFunc() and not isinstance(value, v.Lambda) and (not type.isClass() or attr in type.methods):
            if for_print:
                value = v.Call(value, obj, type=t.String)
            else:
                value = value.bind(obj)

        return value

    def member(self, node, obj, attr, lvalue=False):
        if attr not in obj.type.members:
            self.throw(node['op'], err.NoAttribute(obj.type, attr))
        if lvalue and attr in obj.type.methods:
            self.throw(node, err.NotLvalue())

        value = v.Attribute(obj, obj.type.members[attr], type=obj.type.members[attr].type)
        if attr in obj.type.methods:
            value = v.Call(f'reinterpret_cast<{value.type.ret} (*)({value.type.args_str()})>', v.Call(value), type=value.type)
        return value

    def cast(self, node, value, type):
        # Special case to handle generic functions and lambdas.
        if value.isTemplate():
            if value.bound:
                type = t.Func([value.bound.type] + type.args, type.ret)
            d = type_variables_assignment(type, value.type)
            if d is None:
                self.throw(node, err.NoConversion(value.type, type))
            try:
                return self.function(value, d)
            except err as e:
                if value.lambda_:
                    raise
                self.throw(node, err.InvalidFunctionCall(value.name, d, e))

        # This is the only place where containers are not covariant during type checking.
        if not can_cast(value.type, type, covariance=False):
            self.throw(node, err.NoConversion(value.type, type))

        if not value.type.isNullable() and type.isNullable():
            return v.Nullable(v.Cast(value, type.subtype))
        return v.Cast(value, type)

    def unify(self, node, *values, error=None):
        if not values:
            return []

        types = [value.type for value in values]
        type = unify_types(*types)
        if type is None:
            if error:
                self.throw(node, error)
            else:
                types = list(OrderedDict.fromkeys(types))  # remove duplicates whilst preserving order
                self.throw(node, err.IncompatibleTypes(*types))

        return [self.cast(node, value, type) for value in values]

    def range(self, node, exprs):
        values = lmap(self.transpile, exprs)
        values = self.unify(node, *values)
        if values[0].type not in {t.Int, t.Rat, t.Float, t.Bool, t.Char}:
            self.throw(node, err.InvalidRange(values[0].type))

        return values

    def const(self, value):
        s = str(value)
        if s in self.const_cache:
            return self.const_cache[s]
        const = self.var(value.type)
        self.output(c.Const(const, s), toplevel=True)
        self.const_cache[s] = const
        return const

    def rat(self, value):
        return self.const(v.Rat(value))

    def string(self, value):
        return self.const(v.String(value))

    def var(self, type, prefix='v'):
        return v.Variable(type, self.fake_name(prefix))

    def tmp(self, value, force_copy=False):
        if not force_copy:
            if isinstance(value, v.Variable) or isinstance(value, v.Literal) and value.type in {t.Int, t.Float, t.Bool, t.Char}:
                return value
            if isinstance(value, v.Value) and value.isTemplate():
                return value
        tmp = self.var(value.type)
        self.output(c.Var(tmp, value))
        return tmp

    def declare(self, node, type, name, redeclare=False):
        if not type.hasValue() or type.isVar():
            self.throw(node, err.InvalidDeclaration(type))
        if name in self.env and not redeclare:
            self.throw(node, err.RedefinedIdentifier(name))

        var = self.var(type)
        self.env[name] = var
        self.output(c.Var(var), toplevel=(self.env.get('#return') is None))

        return self.env[name]

    def lvalue(self, expr, declare=None, override=False):
        if expr['node'] == 'AtomId':
            name = expr['name']

            if name not in self.env:
                if declare is None:
                    self.throw(expr, err.UndeclaredIdentifier(name))
                self.declare(expr, declare, name)
            elif override:
                self.declare(expr, declare, name, redeclare=True)
            elif not isinstance(self.env[name], v.Value) or getattr(self.env[name], 'final', False):
                self.throw(expr, err.RedefinedIdentifier(name))

            return self.env[name]

        if expr['node'] == 'ExprAttr' and not expr.get('safe'):
            obj = self.transpile(expr['expr'])
            attr = expr['id']['name']
            if obj.type.isTuple():
                return self.attr(expr, obj, attr)
            elif obj.type.isClass():
                return self.member(expr, obj, attr, lvalue=True)
            else:
                self.throw(expr, err.NotLvalue())

        if expr['node'] == 'ExprIndex' and not expr.get('safe'):
            return self.index(expr, *map(self.transpile, expr['exprs']), lvalue=True)

        if expr['node'] == 'AtomPlaceholder':
            return None

        self.throw(expr, err.NotLvalue())

    def store(self, left, right):
        self.output(c.Statement(left, '=', right))

    def assign(self, expr, value):
        type = value.type

        if type.isFunc():
            type = t.Func([arg.type for arg in type.args], type.ret)

        exprs = expr['exprs'] if expr['node'] == 'ExprTuple' else [expr]
        len1 = len(exprs)

        if type.isTuple():
            len2 = len(type.elements)
            if len1 > 1 and len1 != len2:
                self.throw(expr, err.CannotUnpack(type, len1))
        elif len1 > 1:
            self.throw(expr, err.CannotUnpack(type, len1))

        if len1 > 1:
            value = self.tmp(value)
            for i, expr in enumerate(exprs):
                self.assign(expr, v.Get(value, i))
        elif value.isTemplate() and expr['node'] == 'AtomId' and expr['name'] not in self.env:
            name = expr['name']
            value = copy.copy(value)
            value.name = name
            self.env[name] = value
        else:
            var = self.lvalue(expr, declare=type, override=expr.get('override', False))
            if var is None:
                return
            value = self.cast(expr, value, var.type)
            self.store(var, value)
            type.literal = False

    def unaryop(self, node, op, value):
        if op in {'+', '-'}:
            types = {t.Int, t.Rat, t.Float}
        elif op == 'not':
            types = {t.Bool}

        if value.type not in types:
            self.throw(node['op'], err.NoUnaryOperator(op, value.type))

        op = {
            'not': '!',
        }.get(op, op)

        return v.UnaryOp(op, value, type=value.type)

    def binaryop(self, node, op, left, right):
        types = [left.type, right.type]

        if op != '^' and left.type in {t.Int, t.Rat} and right.type in {t.Int, t.Rat} and t.Rat in {left.type, right.type}:
            left = self.cast(node['op'], left, t.Rat)
            right = self.cast(node['op'], right, t.Rat)

        if left.type.isNumber() and right.type.isNumber() and t.Float in {left.type, right.type}:
            left = self.cast(node['op'], left, t.Float)
            right = self.cast(node['op'], right, t.Float)

        if op == '^':
            if left.type in {t.Int, t.Rat} and right.type == t.Int:
                return v.Call('pow', v.Cast(left, t.Rat), right, type=t.Rat)

            if left.type.isNumber() and right.type == t.Rat:
                return v.Call('pow', v.Cast(left, t.Float), v.Cast(right, t.Float), type=t.Float)

            if left.type == right.type == t.Float:
                return v.Call('pow', left, right, type=t.Float)

        if op == '^^':
            if left.type == right.type == t.Int:
                return v.Call('pow', left, right, type=t.Int)

        if op == '/':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.BinaryOp(v.Cast(left, t.Rat), op, v.Cast(right, t.Rat), type=t.Rat)

            elif left.type == right.type == t.Float:
                return v.BinaryOp(left, op, right, type=t.Float)

        if op == '//':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.Call('floordiv', left, right, type=left.type)

        if op == '%':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.Call('mod', left, right, type=left.type)

        if op == '*':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            if left.type.isSequence() and right.type == t.Int:
                return v.Call('multiply', left, right, type=left.type)

            if left.type == t.Int and right.type.isSequence():
                return self.binaryop(node, op, right, left)

        if op == '&':
            if left.type.isSet() and right.type.isSet():
                left, right = self.unify(node['op'], left, right, error=err.NoBinaryOperator('&', left.type, right.type))
                return v.Call('intersection', left, right, type=left.type)

        if op == '+':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            if left.type != right.type and left.type in {t.Char, t.Int} and right.type in {t.Char, t.Int}:
                return v.Cast(v.BinaryOp(left, op, right), t.Char)

            if left.type != right.type and left.type in {t.Char, t.String} and right.type in {t.Char, t.String}:
                return v.Call('concat', v.Cast(left, t.String), v.Cast(right, t.String), type=t.String)

            if left.type.isCollection() and right.type.isCollection():
                left, right = self.unify(node['op'], left, right, error=err.NoBinaryOperator('+', left.type, right.type))
                return v.Call('concat', left, right, type=left.type)

        if op == '-':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            if left.type == right.type and left.type == t.Char:
                return v.BinaryOp(v.Cast(left, t.Int), op, v.Cast(right, t.Int), type=t.Int)

            if left.type == t.Char and right.type == t.Int:
                return v.Cast(v.BinaryOp(left, op, right), t.Char)

            if left.type.isSet() and right.type.isSet():
                left, right = self.unify(node['op'], left, right, error=err.NoBinaryOperator('-', left.type, right.type))
                return v.Call('difference', left, right, type=left.type)

        if op == '%%':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.BinaryOp(v.BinaryOp(left, '%', right), '==', v.Int(0) if left.type == t.Int else self.rat(0), type=t.Bool)

        self.throw(node['op'], err.NoBinaryOperator(op, *types))

    def convert_string(self, node, string):
        string = re.sub('{{', '\\\\u007B', string)
        string = re.sub('}}', '\\\\u007D'[::-1], string[::-1])[::-1]
        parts = re.split(r'{([^}]*)}', string)

        if len(parts) == 1:
            return {
                **node,
                'value': string,
            }

        pos = (node['position'][0], node['position'][1] + 1)
        exprs = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                exprs.append({
                    'node': 'AtomString',
                    'value': part,
                })
                pos = (pos[0], pos[1] + len(part))
            else:
                pos = (pos[0], pos[1] + 1)
                exprs.append({
                    'node': 'ExprCall',
                    'expr': {
                        'node': 'ExprAttr',
                        'op': {'position': pos},
                        'expr': PyxellParser([ast.literal_eval(f'"{part}"')], self.current_unit.filepath, pos).parse_interpolation_expr(),
                        'id': {
                            'node': 'AtomId',
                            'name': 'toString',
                        },
                    },
                    'args': [],
                })
                pos = (pos[0], pos[1] + len(part) + 1)

        return {
            'node': 'ExprCall',
            'expr': {
                'node': 'ExprAttr',
                'expr': {
                    'node': 'ExprCollection',
                    'kind': 'array',
                    'items': exprs,
                },
                'id': {
                    'node': 'AtomId',
                    'name': 'join',
                },
            },
            'args': [],
        }

    def convert_lambda(self, expr):
        ids = []

        def convert_expr(expr):
            if expr is None:
                return

            node = expr['node']

            if node in {'DictPair', 'ExprIndex', 'ExprBinaryOp', 'ExprIn', 'ExprCmp', 'ExprCond', 'ExprRange', 'ExprBy', 'ExprTuple'}:
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                }
            if node == 'ExprCollection':
                return {
                    **expr,
                    'items': lmap(convert_expr, expr['items']),
                }
            if node == 'ExprComprehension':
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                    'comprehensions': lmap(convert_expr, expr['comprehensions']),
                }
            if node == 'ComprehensionIteration':
                return {
                    **expr,
                    'iterables': lmap(convert_expr, expr['iterables']),
                }
            if node in {'ComprehensionPredicate', 'ExprAttr', 'CallArg', 'ExprUnaryOp', 'ExprIsNull', 'ExprSpread', 'DictSpread'}:
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                }
            if node == 'ExprSlice':
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                    'slice': lmap(convert_expr, expr['slice']),
                }
            if node == 'ExprCall':
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                    'args': lmap(convert_expr, expr['args']) if expr.get('partial') else expr['args'],
                }
            if node == 'AtomString':
                expr = self.convert_string(expr, expr['value'])
                if expr['node'] == 'AtomString':
                    return expr
                return convert_expr(expr)
            if node == 'AtomPlaceholder':
                id = {
                    **expr,
                    'node': 'AtomId',
                    'name': f'${chr(len(ids)+97)}',
                }
                ids.append(id)
                return id
            return expr

        expr = convert_expr(expr)
        if ids:
            return {
                **expr,
                'node': 'ExprLambda',
                'ids': ids,
                'expr': expr,
            }
        return expr

    def function(self, template, assigned_types={}):
        real_types = tuple(assigned_types.get(name) for name in template.typevars)

        if real_types in template.cache:
            return template.cache[real_types].bind(template.bound)

        body = template.body

        with self.unit(template.unit.name):  # to display the correct filepath when a generic function from another module cannot be compiled
            with self.local():
                self.env = template.env.copy()
                self.env.update(assigned_types)

                func_type = self.resolve_type(template.type)

                func = self.var(func_type, prefix='f')
                template.cache[real_types] = func

                arg_vars = [self.var(arg.type, prefix='a') for arg in func_type.args]
                block = c.Block()

                with self.block(block):
                    if body:
                        self.env['#return'] = func_type.ret
                        self.env['#loops'] = {}

                        for arg, var in zip(func_type.args, arg_vars):
                            self.env[arg.name] = var

                        # Try to resolve any unresolved type variables in the return type.
                        if has_type_variables(func_type.ret):
                            with self.local():
                                self.env['#return-types'] = []

                                with self.no_output():
                                    self.transpile(body)

                                if self.env['#return-types']:
                                    ret = unify_types(*self.env['#return-types'])
                                else:
                                    ret = t.Void

                                if ret is not None:
                                    d = type_variables_assignment(ret, self.env['#return'])
                                    if d is not None:
                                        self.env.update(d)
                                        func_type.ret = self.resolve_type(func_type.ret)

                            self.env['#return'] = func_type.ret

                        if not func_type.ret.hasValue() and not func_type.ret.isGenerator() and func_type.ret != t.Void:
                            self.throw(body, err.InvalidReturnType(func_type.ret))
                        if has_type_variables(func_type.ret):
                            self.throw(body, err.UnknownReturnType())

                        self.transpile(body)

                        if func_type.ret.hasValue() and not template.lambda_:
                            self.output(c.Statement('return', self.default(func_type.ret)))

                    else:  # `extern`
                        self.output(c.Statement('return', v.Call(v.Variable(template.type, template.name), *arg_vars)))

        if template.lambda_:
            # The closure is created every time the function is used (except for recursive calls),
            # so current values of variables are captured, possibly different than in the moment of definition.
            del template.cache[real_types]
            self.output(c.Var(func, v.Lambda(func_type, arg_vars, block, capture_vars=[func])))
        else:
            self.output(c.Statement(func_type.ret, f'{func}({func_type.args_str()})'), toplevel=True)
            self.output(c.Function(func_type.ret, func, arg_vars, block), toplevel=True)

        return func.bind(template.bound)

    @contextmanager
    def loop(self, stmt_callback, label):
        if label:
            label = label['name']

        with self.local():
            labels = {'break': self.fake_name('l'), 'continue': self.fake_name('l')}
            self.env['#loops'] = {**self.env['#loops'], label: labels, None: labels}

            body = c.Block()
            with self.block(body):
                self.output(c.If(v.false, c.Block(c.Label(labels['continue']), c.Statement('continue'))))
                yield

            self.output(stmt_callback(body))
            self.output(c.Label(labels['break']))


    ### Statements ###

    def transpileBlock(self, node):
        for stmt in node['stmts']:
            self.transpile(stmt)

    def transpileStmtUse(self, node):
        module_name = node['id']['name']
        if module_name not in self.units:
            self.throw(node['id'], err.UnknownModule(module_name))

        unit = self.units[module_name]
        kind, *ids = node['detail']

        if kind == 'hiding':
            hidden = set()
            for id in ids:
                name = id['name']
                if name not in unit.env:
                    self.throw(id, err.NoIdentifier(module_name, name))
                hidden.add(name)
            self.env.update({x: unit.env[x] for x in unit.env.keys() - hidden})
        else:
            self.env.update(unit.env)

    def transpileStmtSkip(self, node):
        pass

    def transpileStmtPrint(self, node):
        exprs = node['exprs']
        values = lmap(self.transpile, exprs)

        for i, (expr, value) in enumerate(zip(exprs, values)):
            if not value.type.isPrintable():
                self.throw(expr, err.NotPrintable(value.type))

            if i > 0:
                self.output(c.Statement(v.Call('write', self.string(' '))))
            self.output(c.Statement(v.Call('write', self.attr(expr, value, 'toString', for_print=True))))

        self.output(c.Statement(v.Call('write', self.string('\\n'))))  # std::endl is very slow

    def transpileStmtDecl(self, node):
        type = self.resolve_type(self.transpile(node['type']))
        var = self.declare(node, type, node['id']['name'])

        expr = node['expr']
        if expr:
            value = self.cast(expr, self.transpile(expr), type)
        else:
            value = self.default(type)

        self.store(var, value)

    def transpileStmtAssg(self, node):
        lvalues = node['exprs'][:-1]
        value = self.transpile(node['exprs'][-1], void_allowed=(len(lvalues) == 0))

        if value.type == t.Void:
            self.output(value)
        else:
            value = self.tmp(value)

        for lvalue in lvalues:
            self.assign(lvalue, value)

    def transpileStmtAssgExpr(self, node):
        exprs = node['exprs']
        op = node['op']['text']
        left = self.lvalue(exprs[0])
        if left is None:
            self.throw(node, err.NotLvalue())

        if op == '??':
            block = c.Block()
            self.output(c.If(v.IsNull(left), block))
            with self.block(block):
                right = self.transpile(exprs[1])
                if not left.type.isNullable() or not can_cast(right.type, left.type.subtype):
                    self.throw(node['op'], err.NoBinaryOperator(op, left.type, right.type))
                self.store(left, v.Nullable(self.cast(node, right, left.type.subtype)))
        else:
            right = self.transpile(exprs[1])
            value = self.binaryop(node, op, left, right)
            if value.type != left.type:
                self.throw(node, err.NoConversion(value.type, left.type))
            self.store(left, value)

    def transpileStmtAppend(self, node):
        # Special instruction for array/set/dict literals and comprehensions.
        collection = self.transpile(node['collection'])
        exprs = node['exprs']
        values = lmap(self.transpile, exprs)
        if any(value.type == t.Unknown for value in values):
            return

        if collection.type.isArray():
            value = self.cast(exprs[0], values[0], collection.type.subtype)
            self.output(v.Call(v.Attribute(collection, 'push_back'), value))
        elif collection.type.isSet():
            value = self.cast(exprs[0], values[0], collection.type.subtype)
            self.output(v.Call(v.Attribute(collection, 'insert'), value))
        elif collection.type.isDict():
            values = [self.cast(exprs[0], values[0], collection.type.key_type), self.cast(exprs[1], values[1], collection.type.value_type)]
            self.output(v.Call(v.Attribute(collection, 'insert_or_assign'), *values))

    def transpileStmtIf(self, node):
        exprs = node['exprs']
        blocks = node['blocks']

        def emitIf(index):
            if index == len(blocks):
                return

            expr = None
            if index < len(exprs):
                expr = exprs[index]
                cond = self.cast(expr, self.transpile(expr), t.Bool)

            then = c.Block()
            with self.block(then):
                with self.local():
                    self.transpile(blocks[index])

            if expr:
                els = c.Block()
                with self.block(els):
                    emitIf(index+1)
                self.output(c.If(cond, then, els))
            else:
                self.output(then)

        emitIf(0)

    def transpileStmtWhile(self, node):
        expr = node['expr']

        with self.loop(partial(c.While, v.true), node.get('label')):
            cond = self.cast(expr, self.transpile(expr), t.Bool)
            cond = v.UnaryOp('!', cond)
            self.output(c.If(cond, c.Statement('break')))

            self.transpile(node['block'])

    def transpileStmtUntil(self, node):
        expr = node['expr']

        second_iteration = self.tmp(v.false, force_copy=True)

        with self.loop(partial(c.While, v.true), node.get('label')):
            cond = self.cast(expr, self.transpile(expr), t.Bool)
            cond = v.BinaryOp(second_iteration, '&&', cond)
            self.output(c.If(cond, c.Statement('break')))
            self.store(second_iteration, v.true)

            self.transpile(node['block'])

    def transpileStmtFor(self, node):
        vars = node['vars']
        iterables = node['iterables']

        types = []
        conditions = []
        updates = []
        getters = []

        for iterable in iterables:
            if iterable['node'] == 'ExprBy':
                step_expr = iterable['exprs'][1]
                step = self.transpile(step_expr)
                iterable = iterable['exprs'][0]
            else:
                step_expr = None
                step = v.Int(1)

            step = self.tmp(step, force_copy=True)

            if iterable['node'] == 'ExprRange':
                values = self.range(iterable['op'], iterable['exprs'])
                type = values[0].type
                types.append(type)

                index = self.tmp(v.Cast(values[0], {t.Rat: t.Rat, t.Float: t.Float}.get(type, t.Int)), force_copy=True)
                self.cast(step_expr, step, index.type)

                if len(values) == 1:
                    cond = v.true  # infinite range
                else:
                    end = self.tmp(values[1], force_copy=True)
                    eq = '=' if iterable.get('inclusive') else ''
                    neg = self.tmp(v.BinaryOp(step, '<', v.Cast(v.Int(0), step.type), type=t.Bool))
                    cond = v.TernaryOp(neg, f'{index} >{eq} {end}', f'{index} <{eq} {end}')

                update = v.BinaryOp(index, '+=', step)
                getter = v.Cast(index, type)

            else:
                value = self.tmp(self.transpile(iterable))
                type = value.type
                if not type.isIterable():
                    self.throw(iterable, err.NotIterable(type))

                types.append(type.subtype)
                iterator = self.tmp(v.Call(v.Attribute(value, 'begin'), type=t.Iterator(value.type)))
                end = self.tmp(v.Call(v.Attribute(value, 'end'), type=t.Sentinel(value.type)))

                self.cast(step_expr, step, t.Int)

                if type.isSequence():
                    self.output(c.If(f'{step} < 0 && {iterator} != {end}', c.Statement(iterator, '=', v.Call('std::prev', end))))
                    index = self.tmp(v.Int(0), force_copy=True)
                    length = self.tmp(v.Call(v.Attribute(value, 'size'), type=t.Int))
                    cond = f'{index} < {length}'
                    abs_step = self.tmp(v.Call('std::abs', step, type=step.type))
                    update = f'{index} += {abs_step}, {iterator} += {step}'
                else:
                    self.store(step, f'std::abs({step})')
                    cond = f'{iterator} != {end}'
                    update = f'safe_advance({iterator}, {end}, {step})'

                getter = v.UnaryOp('*', iterator, type=type.subtype)

            conditions.append(cond)
            updates.append(update)
            getters.append(getter)

        condition = ' && '.join(str(cond) for cond in conditions)
        update = ', '.join(str(update) for update in updates)

        with self.loop(partial(c.For, '', condition, update), node.get('label')):
            if len(vars) == 1 and len(types) > 1:
                tuple = v.Tuple(getters)
                self.assign(vars[0], tuple)
            elif len(vars) > 1 and len(types) == 1:
                if not types[0].isTuple():
                    self.throw(vars[0], err.CannotUnpack(types[0], len(vars)))
                tuple = getters[0]
                for i, var in enumerate(vars):
                    self.assign(var, v.Get(tuple, i))
            elif len(vars) == len(types):
                for var, getter in zip(vars, getters):
                    self.assign(var, getter)
            else:
                self.throw(vars[0], err.CannotUnpack(t.Tuple(types), len(vars)))

            self.transpile(node['block'])

    def transpileStmtLoopControl(self, node):
        stmt = node['stmt']  # `break` / `continue`
        label = node.get('label')
        name = label and label['name']

        if not self.env['#loops']:
            self.throw(node, err.InvalidUsage(stmt))
        if name not in self.env['#loops']:
            self.throw(label, err.UnknownLabel(name))

        self.output(c.Statement('goto', self.env['#loops'][name][stmt]))

    def transpileStmtFunc(self, node, class_type=None):
        func_name = node['id']['name']
        if class_type is None and func_name in self.env:
            self.throw(node['id'], err.RedefinedIdentifier(func_name))

        with self.local():
            typevars = [id['name'] for id in node.get('typevars', [])]
            for name in typevars:
                self.env[name] = t.Var(name)

            args = [] if class_type is None else [t.Func.Arg('this', class_type)]
            for i, arg in enumerate(node['args']):
                name = arg['id'].get('name')  # allow placeholders as argument names
                type = self.transpile(arg.get('type'))
                default = arg.get('expr')
                variadic = arg.get('variadic')
                if type is None:
                    type_name = f'${chr(i+65)}'
                    type = t.Var(type_name)
                    if variadic:
                        type = t.Array(type)
                    typevars.append(type_name)
                    self.env[type_name] = type
                if not type.hasValue():
                    self.throw(arg, err.InvalidDeclaration(type))
                if variadic:
                    if any(arg.variadic for arg in args):
                        self.throw(arg, err.RepeatedVariadic())
                    if not type.isArray():
                        self.throw(arg, err.InvalidVariadicType(type))
                args.append(t.Func.Arg(name, type, default, variadic))

            if typevars and class_type:
                self.throw(node, err.GenericMethod())

            ret_type = self.transpile(node.get('ret'))
            if ret_type is None:
                n = len(node['args'])
                ret_type = t.Var(f'${chr(n+65)}')
                typevars.append(ret_type.name)
                self.env[ret_type.name] = ret_type
            if node.get('generator'):
                self.require('generators')
                ret_type = t.Generator(ret_type)
            func_type = t.Func(args, ret_type)

            env = self.env.copy()

            lambda_ = node.get('lambda') or self.env.get('#return') is not None
            func = v.FunctionTemplate(func_name, typevars, func_type, node['block'], env, self.current_unit, lambda_)

        if class_type is None:
            self.env[func_name] = env[func_name] = func
        else:
            return self.function(func)

    def transpileStmtReturn(self, node):
        try:
            type = self.env['#return']
        except KeyError:
            self.throw(node, err.InvalidUsage('return'))

        expr = node['expr']
        if expr:
            value = self.transpile(expr, void_allowed=True)

            if type.isGenerator():
                self.throw(node, err.NoConversion(value.type, type))

            if '#return-types' in self.env:
                self.env['#return-types'].append(value.type)
            else:
                value = self.cast(node, value, type)

        elif type.hasValue():
            if '#return-types' in self.env:
                type = t.Void
                self.env['#return-types'].append(type)
            else:
                self.throw(node, err.NoConversion(t.Void, type))

        if type.isGenerator():
            self.output(c.Statement('co_return'))
        elif type == t.Void:
            if expr:
                # Special case for lambdas returning Void.
                self.output(value)
            self.output(c.Statement('return'))
        else:
            self.output(c.Statement('return', value))

    def transpileStmtYield(self, node):
        type = self.env.get('#return')
        if not type or not type.isGenerator():
            self.throw(node, err.InvalidUsage('yield'))

        type = type.subtype
        value = self.transpile(node['expr'])

        if '#return-types' in self.env:
            self.env['#return-types'].append(t.Generator(value.type))
        else:
            value = self.cast(node, value, type)

        self.output(c.Statement('co_yield', value))

    def transpileStmtClass(self, node):
        class_name = node['id']['name']
        if class_name in self.env:
            self.throw(node['id'], err.RedefinedIdentifier(class_name))

        base = self.transpile(node['base'])
        if base and not base.isClass():
            self.throw(node['base'], err.NotClass(base))

        base_members = base.members if base else {}
        members = dict(base_members)
        base_methods = base.methods if base else {}
        methods = dict(base_methods)

        type = t.Class(class_name, base, members, methods)
        self.env[class_name] = type

        cls = self.var(t.Func([], type), prefix='c')
        type.initializer = cls

        fields = c.Block()
        self.output(c.Statement('struct', cls), toplevel=True)
        self.output(c.Struct(cls, fields, base=(base.initializer if base else None)), toplevel=True)

        for member in node['members']:
            if member['node'] == 'ClassField':
                name = member['id']['name']
                if name in members:
                    self.throw(member, err.RepeatedMember(name))
                if name == 'toString':
                    self.throw(member, err.InvalidMember(name))

                field = self.var(self.transpile(member['type']), prefix='m')

                default = member.get('expr')
                if default:
                    field.default = self.cast(default, self.transpile(default), field.type)
                else:
                    field.default = self.default(field.type)

                fields.append(c.Statement(c.Var(field)))
                members[name] = field

        if not any(member['id']['name'] == 'toString' for member in node['members']) and (not base or 'toString' in base.default_methods):
            node['members'].append({
                'node': 'ClassMethod',
                'id': {
                    'node': 'AtomId',
                    'name': 'toString',
                },
                'args': [],
                'ret': t.String,
                'block': {
                    'node': 'StmtReturn',
                    'expr': self.string(f'{class_name} object'),
                },
            })
            type.default_methods.add('toString')

        for member in node['members']:
            if member['node'] != 'ClassField':
                name = member['id']['name']
                if name in members and name not in base_members:
                    self.throw(member, err.RepeatedMember(name))

                members[name] = methods[name] = None

                if member['block']:
                    with self.local():
                        self.env['#this'] = True

                        if member['node'] in {'ClassConstructor', 'ClassDestructor'}:
                            self.env['#super'] = None
                        else:
                            self.env['#super'] = base_methods.get(name)

                        methods[name] = func = self.transpileStmtFunc(member, class_type=type)

                    if member['node'] == 'ClassMethod':
                        if name == 'toString':
                            if len(func.type.args) > 1 or func.type.ret != t.String:
                                self.throw(member, err.InvalidMember(name))
                            members[name] = v.Variable(func.type, 'toString')
                        elif base_members.get(name):
                            members[name] = v.Variable(func.type, base_members[name].name)
                        else:
                            members[name] = self.var(func.type, prefix='m')

                        block = c.Block()
                        fields.append(c.Function('virtual void*', members[name], [], block))
                        with self.block(block):
                            self.output(c.Statement('return', v.Call('reinterpret_cast<void*>', func)))

                    elif member['node'] == 'ClassDestructor':
                        block = c.Block()
                        fields.append(c.Function('virtual', f'~{cls}', [], block))
                        with self.block(block):
                            # To call the destructor function expecting shared_ptr as the argument,
                            # we create a shared_ptr that points to, but doesn't own, `this`.
                            # https://stackoverflow.com/a/29709885
                            self.output(v.Call(methods['<destructor>'], v.Call(type, v.Call(type), 'this')))

        if not any(member['node'] == 'ClassDestructor' for member in node['members']):
            # Empty virtual destructor as recommended by C++.
            # https://stackoverflow.com/a/10024812
            fields.append(c.Function('virtual', f'~{cls}', [], c.Block()))


    ### Expressions ###

    def transpileExprCollection(self, node):
        items = node['items']
        kind = node['kind']
        type_lists = [], []

        with self.no_output():
            for item in items:
                if item['node'] in {'ExprRange', 'ExprBy'}:
                    if item['node'] == 'ExprBy':
                        if item['exprs'][0]['node'] != 'ExprRange':
                            self.throw(item['op'], err.InvalidIterative())
                        item = item['exprs'][0]
                    values = self.range(item['op'], item['exprs'])
                    type_lists[0].extend(value.type for value in values)

                elif item['node'] == 'ExprSpread':
                    item = item['expr']
                    if item['node'] == 'ExprBy':
                        item = item['exprs'][0]
                    value = self.transpile(item)
                    if not value.type.isIterable():
                        self.throw(item, err.NotIterable(value.type))
                    type_lists[0].append(value.type.subtype)

                elif item['node'] == 'DictPair':
                    values = lmap(self.transpile, item['exprs'])
                    for i in range(2):
                        type_lists[i].append(values[i].type)

                elif item['node'] == 'DictSpread':
                    item = item['expr']
                    if item['node'] == 'ExprBy':
                        item = item['exprs'][0]
                    value = self.transpile(item)
                    if not value.type.isDict():
                        self.throw(item, err.NotDictionary(value.type))
                    type_lists[0].append(value.type.key_type)
                    type_lists[1].append(value.type.value_type)

                else:
                    value = self.transpile(item)
                    type_lists[0].append(value.type)

        types = [t.Unknown, t.Unknown]
        for i in range(2):
            types[i].literal = True
            if type_lists[i]:
                types[i] = unify_types(*type_lists[i])
                if types[i] is None:
                    self.throw(node, err.IncompatibleTypes(*type_lists[i]))
                types[i].literal = all(t.literal for t in type_lists[i])

        if kind == 'array':
            result = v.Array([], types[0])
        else:
            if not types[0].isHashable():
                self.throw(node, err.NotHashable(types[0]))
            if kind == 'set':
                result = v.Set([], types[0])
            elif kind == 'dict':
                result = v.Dict([], [], *types)

        result = self.tmp(result)
        result.type.literal = True

        for item in items:
            if item['node'] in {'ExprRange', 'ExprSpread', 'ExprBy'}:
                if item['node'] == 'ExprSpread':
                    item = item['expr']
                var = {
                    **item,
                    'node': 'AtomId',
                    'name': self.fake_name(),
                }
                self.transpile({
                    'node': 'StmtFor',
                    'vars': [var],
                    'iterables': [item],
                    'block': {
                        'node': 'StmtAppend',
                        'collection': result,
                        'exprs': [var],
                    },
                })
            elif item['node'] == 'DictPair':
                self.transpile({
                    'node': 'StmtAppend',
                    'collection': result,
                    'exprs': item['exprs'],
                })
            elif item['node'] == 'DictSpread':
                vars = [{
                    **item,
                    'node': 'AtomId',
                    'name': self.fake_name(),
                } for _ in range(2)]

                self.transpile({
                    'node': 'StmtFor',
                    'vars': vars,
                    'iterables': [item['expr']],
                    'block': {
                        'node': 'StmtAppend',
                        'collection': result,
                        'exprs': vars,
                    },
                })
            else:
                self.transpile({
                    'node': 'StmtAppend',
                    'collection': result,
                    'exprs': [item],
                })

        return result

    def transpileExprComprehension(self, node):
        exprs = node['exprs']
        kind = node['kind']

        value, collection = [{
            'node': 'AtomId',
            'name': self.fake_name(),
        } for _ in range(2)]

        stmt = inner_stmt = {
            'node': 'StmtAssg',
            'exprs': [
                value,
                {
                    'node': 'ExprTuple',
                    'exprs': exprs,
                },
            ],
        }

        for cpr in reversed(node['comprehensions']):
            if cpr['node'] == 'ComprehensionIteration':
                stmt = {
                    **cpr,
                    'node': 'StmtFor',
                    'vars': [{**var, 'override': True} for var in cpr['vars']],
                    'block': stmt,
                }
            elif cpr['node'] == 'ComprehensionPredicate':
                stmt = {
                    **cpr,
                    'node': 'StmtIf',
                    'exprs': [cpr['expr']],
                    'blocks': [stmt],
                }

        # A small hack to obtain type of the expression.
        with self.local():
            with self.no_output():
                inner_stmt['_eval'] = lambda: self.transpile(value).type.elements
                self.transpile(stmt)
                types = inner_stmt.pop('_eval')

        with self.local():
            if kind == 'array':
                self.assign(collection, v.Array([], types[0]))
            elif kind == 'set':
                if not types[0].isHashable():
                    self.throw(node, err.NotHashable(types[0]))
                self.assign(collection, v.Set([], types[0]))
            elif kind == 'dict':
                if not types[0].isHashable():
                    self.throw(node, err.NotHashable(types[0]))
                self.assign(collection, v.Dict([], [], *types))

            inner_stmt['node'] = 'StmtAppend'
            inner_stmt['collection'] = collection
            inner_stmt['exprs'] = exprs

            self.transpile(stmt)

            result = self.transpile(collection)

        result.type.literal = True
        return result

    def transpileExprAttr(self, node):
        expr = node['expr']
        attr = node['id']['name']

        if node.get('safe'):
            obj = self.tmp(self.transpile(expr))
            return self.safe(node, obj, lambda: v.Nullable(self.attr(node, v.Extract(obj), attr)), lambda: v.null)

        return self.attribute(node, expr, attr)

    def transpileExprIndex(self, node):
        exprs = node['exprs']

        if node.get('safe'):
            collection = self.tmp(self.transpile(exprs[0]))
            return self.safe(node, collection, lambda: v.Nullable(self.index(node, v.Extract(collection), self.transpile(exprs[1]))), lambda: v.null)

        return self.index(node, *map(self.transpile, exprs))

    def transpileExprSlice(self, node):
        slice = node['slice']

        collection = self.transpile(node['expr'])
        type = collection.type
        if not type.isSequence():
            self.throw(node['op'], err.NotSliceable(type))

        a = v.Nullable(self.cast(slice[0], self.transpile(slice[0]), t.Int)) if slice[0] else v.null
        b = v.Nullable(self.cast(slice[1], self.transpile(slice[1]), t.Int)) if slice[1] else v.null
        step = self.cast(slice[2], self.transpile(slice[2]), t.Int) if slice[2] else v.Int(1)

        return v.Call('slice', collection, a, b, step, type=type)

    def transpileExprCall(self, node):
        expr = node['expr']

        def _resolve_args(func):
            if not func.type.isFunc():
                self.throw(node['op'], err.NotCallable(func.type))

            obj = None
            if func.isTemplate() and func.bound:
                obj = func.bound

            func_args = func.type.args[1:] if obj else func.type.args[:]
            func_named_args = {func_arg.name for func_arg in func_args}

            pos_args = []
            named_args = {}

            for i, call_arg in enumerate(node['args']):
                id = call_arg.get('id')
                if id:
                    name = id['name']
                    if name in named_args:
                        self.throw(call_arg, err.RepeatedArgument(name))
                    if name not in func_named_args:
                        self.throw(call_arg, err.UnexpectedArgument(name))
                    named_args[name] = call_arg
                else:
                    if named_args:
                        self.throw(call_arg, err.ExpectedNamedArgument())
                    pos_args.append(call_arg)

            with self.local():
                type_variables = defaultdict(list)
                exprs = []
                args = []

                for i, func_arg in enumerate(func_args):
                    name = func_arg.name

                    if name in named_args:
                        if i < len(pos_args):
                            self.throw(named_args[name], err.RepeatedArgument(name))

                        expr = named_args.pop(name)['expr']

                    elif func_arg.variadic and (pos_args or not func_arg.default):
                        expr = {
                            **(pos_args[i]['expr'] if i < len(pos_args) else {}),
                            'node': 'ExprCollection',
                            'kind': 'array',
                            'items': [arg['expr'] for arg in pos_args[i:]],
                        }
                        pos_args = []

                    elif i < len(pos_args):
                        expr = pos_args[i]['expr']
                        pos_args[i] = None

                    elif func_arg.default:
                        if isinstance(func_arg.default, v.Value):
                            exprs.append({})
                            args.append(func_arg.default)
                            continue
                        else:
                            expr = func_arg.default

                    else:
                        if name is None:
                            self.throw(node['op'], err.TooFewArguments())
                        else:
                            self.throw(node['op'], err.MissingArgument(name))

                    value = self.transpile(expr)

                    if not value.isTemplate():
                        d = type_variables_assignment(value.type, func_arg.type)
                        if d is None:
                            self.throw(expr, err.NoConversion(value.type, func_arg.type))

                        for name, type in d.items():
                            type_variables[name].append(type)

                    exprs.append(expr)
                    args.append(value)

                if any(arg is not None for arg in pos_args):
                    self.throw(node['op'], err.TooManyArguments())

                if obj:
                    for name, type in type_variables_assignment(obj.type, func.type.args[0].type).items():
                        type_variables[name].append(type)

                if func.isTemplate():
                    for name in func.typevars:
                        self.env.pop(name, None)  # to avoid name conflicts

                assigned_types = {}

                for name, types in type_variables.items():
                    type = unify_types(*types)
                    if type is None:
                        self.throw(node['op'], err.InvalidArgumentTypes(t.Var(name)))

                    self.env[name] = assigned_types[name] = type

                for i in range(len(args)):
                    type = self.resolve_type(func_args[i].type)
                    args[i] = self.cast(exprs[i], args[i], type)
                    d = type_variables_assignment(args[i].type, func_args[i].type)
                    assigned_types.update(d)
                    self.env.update(d)

                if func.isTemplate():
                    try:
                        func = self.function(func, assigned_types)
                    except err as e:
                        self.throw(node['op'], err.InvalidFunctionCall(func.name, assigned_types, e))

                return func, args

        def _call(func):
            func, args = _resolve_args(func)

            return v.Call(func, *args, type=func.type.ret)

        if expr['node'] == 'ExprAttr':
            attr = expr['id']['name']

            if expr.get('safe'):
                obj = self.tmp(self.transpile(expr['expr']))

                def callback():
                    value = self.tmp(v.Extract(obj))
                    func = self.attr(node, value, attr)
                    result = _call(func)

                    if result.type == t.Void:
                        self.output(result)
                        return v.null
                    else:
                        return v.Nullable(result)

                return self.safe(expr, obj, callback, lambda: v.null)

            else:
                if attr == 'toString' and len(node['args']) == 0:
                    return self.attribute(expr, expr['expr'], attr, for_print=True)

                # TODO: remove redundant binding for method calls, like with `toString()`
                func = self.attribute(expr, expr['expr'], attr)

        else:
            func = self.transpile(expr)

            if expr['node'] == 'AtomSuper':
                obj = v.Cast(self.get(expr, 'this'), func.type.args[0].type)
                func = func.bind(obj)

        if isinstance(func, t.Class):
            cls = func
            obj = self.tmp(v.Object(cls))

            fields = {name: field for name, field in cls.members.items() if name not in cls.methods}
            constructor_type = t.Func([t.Func.Arg(name, field.type, field.default) for name, field in fields.items()])
            args = _resolve_args(v.Value(type=constructor_type))[1]
            for name, value in zip(fields, args):
                self.store(self.attr(node, obj, name), value)

            constructors = []
            while cls:
                constructors.append(cls.methods.get('<constructor>'))
                cls = cls.base

            constructors.reverse()
            for i, constructor in enumerate(constructors):
                if constructor and constructors.index(constructor) == i:
                    func = constructor.bind(obj)
                    self.output(v.Call(func, type=func.type.ret))

            return obj

        result = _call(func)
        if result.type != t.Void:
            result = self.tmp(result)
        return result

    def transpileExprUnaryOp(self, node):
        op = node['op']['text']
        value = self.transpile(node['expr'])

        if op == '!':
            if not value.type.isNullable():
                self.throw(node['op'], err.NotNullable(value.type))

            return v.Extract(value)

        return self.unaryop(node, op, value)

    def transpileExprBinaryOp(self, node):
        op = node['op']['text']
        exprs = node['exprs']

        if op == '??':
            left = self.tmp(self.transpile(exprs[0]))
            try:
                if left.type == t.Nullable(t.Unknown):
                    return self.transpile(exprs[1])
                return self.safe(node, left, lambda: v.Extract(left), lambda: self.transpile(exprs[1]))
            except err:
                self.throw(node['op'], err.NoBinaryOperator(op, left.type, self.transpile(exprs[1]).type))

        if op in {'and', 'or'}:
            result = self.tmp(v.Bool(op == 'or'), force_copy=True)

            cond1 = self.transpile(exprs[0])
            if op == 'or':
                cond1 = v.UnaryOp('!', cond1, type=t.Bool)

            block = c.Block()
            self.output(c.If(cond1, block))
            with self.block(block):
                cond2 = self.transpile(exprs[1])
                if not cond1.type == cond2.type == t.Bool:
                    self.throw(node['op'], err.NoBinaryOperator(op, cond1.type, cond2.type))
                self.store(result, cond2)

            return result

        return self.binaryop(node, op, *map(self.transpile, exprs))

    def transpileExprIsNull(self, node):
        value = self.transpile(node['expr'])
        if not value.type.isNullable():
            self.throw(node['op'], err.NotNullable(value.type))

        if value.type == t.Unknown:  # for the `null is null` case
            return v.Bool(not node.get('not'))

        return v.IsNotNull(value) if node.get('not') else v.IsNull(value)

    def transpileExprIn(self, node):
        exprs = node['exprs']

        element = self.transpile(exprs[0])
        iterable = self.transpile(exprs[1])
        if not iterable.type.isIterable():
            self.throw(exprs[1], err.NotIterable(iterable.type))

        if iterable.type == t.String:
            type = iterable.type
        elif iterable.type.isDict():
            type = iterable.type.key_type
        else:
            type = iterable.type.subtype

        if type == t.Unknown:  # for the case of empty container
            return v.Bool(node.get('not'))

        element = self.cast(node['op'], element, type)
        result = v.Call('contains', iterable, element, type=t.Bool)
        return v.UnaryOp('!', result, type=t.Bool) if node.get('not') else result

    def transpileExprCmp(self, node):
        exprs = node['exprs']
        ops = node['ops']

        result = self.tmp(v.false, force_copy=True)

        left = self.transpile(exprs[0])

        def emitIf(index):
            nonlocal left
            right = self.transpile(exprs[index])
            op_node = ops[index-1]
            op = op_node['text']

            try:
                left, right = self.unify(op_node, left, right)
                right = self.tmp(right)
            except err:
                self.throw(op_node, err.NotComparable(left.type, right.type))

            if not left.type.isComparable():
                self.throw(op_node, err.NotComparable(left.type, right.type))
            if not left.type.isOrderable() and op not in {'==', '!='}:
                self.throw(op_node, err.NoBinaryOperator(op, left.type, right.type))

            cond = v.BinaryOp(left, op, right, type=t.Bool)
            left = right

            if index == len(exprs) - 1:
                self.store(result, cond)
            else:
                block = c.Block()
                with self.block(block):
                    emitIf(index+1)
                self.output(c.If(cond, block))

        emitIf(1)

        return result

    def transpileExprCond(self, node):
        exprs = node['exprs']
        return self.cond(node, self.transpile(exprs[0]), lambda: self.transpile(exprs[1]), lambda: self.transpile(exprs[2]))

    def transpileExprRange(self, node):
        self.throw(node['op'], err.InvalidIterative())

    def transpileExprSpread(self, node):
        self.throw(node['op'], err.InvalidIterative())

    def transpileExprBy(self, node):
        self.throw(node['op'], err.InvalidIterative())

    def transpileExprLambda(self, node):
        name = self.fake_name()

        self.transpile({
            **node,
            'node': 'StmtFunc',
            'id': {
                'node': 'AtomId',
                'name': name,
            },
            'args': [{
                'id': id,
            } for id in node['ids']],
            'block': {
                'node': 'StmtReturn',
                'position': node['expr'].get('position'),
                'expr': node['expr'],
            },
            'lambda': True,
        })

        return self.get(node, name)

    def transpileExprTuple(self, node):
        elements = lmap(self.transpile, node['exprs'])
        return v.Tuple(elements)


    ### Atoms ###

    def transpileAtomInt(self, node):
        value = node['value']
        if value >= 2**63:
            self.throw(node, err.IntegerTooLarge())
        return v.Int(value)

    def transpileAtomRat(self, node):
        return self.rat(node['value'])

    def transpileAtomFloat(self, node):
        return v.Float(node['value'])

    def transpileAtomBool(self, node):
        return v.Bool(node['value'])

    def transpileAtomChar(self, node):
        return v.Char(node['value'])

    def transpileAtomString(self, node):
        expr = self.convert_string(node, node['value'])

        if expr['node'] == 'AtomString':
            return self.string(expr['value'])

        try:
            return self.transpile(expr)
        except err as e:
            self.throw({
                **node,
                'position': [e.line+node['position'][0]-1, e.column+node['position'][1]+1],
            }, str(e).partition(': ')[2][:-1])

    def transpileAtomNull(self, node):
        return self.const(v.null)

    def transpileAtomThis(self, node):
        if not self.env.get('#this'):
            self.throw(node, err.InvalidUsage('this'))
        return self.get(node, 'this')

    def transpileAtomSuper(self, node):
        func = self.env.get('#super')
        if func is None:
            self.throw(node, err.InvalidUsage('super'))
        return func

    def transpileAtomId(self, node):
        return self.get(node, node['name'])


    ### Types ###

    def transpileTypeId(self, node):
        name = node['name']

        type = {
            'Void': t.Void,
            'Int': t.Int,
            'Rat': t.Rat,
            'Float': t.Float,
            'Bool': t.Bool,
            'Char': t.Char,
            'String': t.String,
        }.get(name)

        if type is None:
            type = self.env.get(name)
            if not isinstance(type, t.Type):
                self.throw(node, err.NotType(name))
            return type

        return type

    def transpileTypeCollection(self, node):
        constructors = {'array': t.Array, 'set': t.Set, 'dict': t.Dict}
        return constructors[node['kind']](*map(self.transpile, node['subtypes']))

    def transpileTypeNullable(self, node):
        return t.Nullable(self.transpile(node['subtype']))

    def transpileTypeTuple(self, node):
        return t.Tuple(lmap(self.transpile, node['types']))

    def transpileTypeFunc(self, node):
        types = lmap(self.transpile, node['types'])
        return t.Func(types[:-1], types[-1])
