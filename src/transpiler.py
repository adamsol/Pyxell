
import ast
import re
from collections import defaultdict
from contextlib import contextmanager
from itertools import zip_longest

from . import codegen as c
from . import types as t
from . import values as v
from .errors import NotSupportedError, PyxellError as err
from .parsing import parse_expr
from .types import can_cast, has_type_variables, type_variables_assignment, unify_types
from .utils import lmap


class Unit:

    def __init__(self):
        self.env = {}


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

    def run(self, ast, unit):
        self.units[unit] = Unit()
        with self.unit(unit):
            if unit != 'std':
                self.env = self.units['std'].env.copy()
            self.transpile(ast)

    def run_main(self, ast):
        self.run(ast, 'main')
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
        line, column = node.get('position', (1, 1))
        raise err(msg, line, column)

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
        yield
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
        if isinstance(stmt, (v.Value, c.Var, c.Const)):
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

    def fake_id(self, prefix='$id'):
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

    def default(self, node, type, nullptr_allowed=False):
        if type == t.Int:
            return v.Int(0)
        elif type == t.Rat:
            return self.rat(0)
        elif type == t.Float:
            return v.Float(0)
        elif type == t.Bool:
            return v.false
        elif type == t.Char:
            return v.Char('\0')
        elif type == t.String:
            return self.string('')
        elif type.isArray():
            return v.Array([], type.subtype)
        elif type.isSet():
            return v.Set([], type.subtype)
        elif type.isDict():
            return v.Dict([], [], type.key_type, type.value_type)
        elif type.isNullable():
            return v.Nullable(None, type.subtype)
        elif type.isTuple():
            return v.Tuple([self.default(node, t, nullptr_allowed) for t in type.elements])
        elif type.isFunc():
            return v.Lambda(type, [''] * len(type.args), self.default(node, type.ret, nullptr_allowed) if type.ret != t.Void else c.Block())
        elif type.isClass() and nullptr_allowed:
            return v.Literal('nullptr', type=type)

        self.throw(node, err.NotDefaultable(type))

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

            elif collection.type.isDict():
                index = self.cast(exprs[1], index, collection.type.key_type)
                type = collection.type.value_type

                it = self.tmp(v.Call(v.Attribute(collection, 'find'), index))
                end = v.Call(v.Attribute(collection, 'end'))

                block = c.Block()
                self.output(c.If(f'{it} == {end}', block))
                with self.block(block):
                    default = self.default(node, type, nullptr_allowed=True)
                    self.output(c.Statement(it, '=', v.Call(v.Attribute(collection, 'insert_or_assign'), it, index, default)))

                return v.Attribute(it, 'second', type=type)

        self.throw(exprs[0], err.NotIndexable(collection.type))

    def cond(self, node, pred, callback_true, callback_false):
        pred = self.cast(node, pred, t.Bool)

        block_true = c.Block()
        block_false = c.Block()

        with self.block(block_true):
            value_true = callback_true()
        with self.block(block_false):
            value_false = callback_false()

        type = unify_types(value_true.type, value_false.type)
        if type is None:
            self.throw(node, err.UnknownType())

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
            self.throw(node, err.NotNullable(value.type))

        return self.cond(node, v.IsNotNull(value), callback_notnull, callback_null)

    def attribute(self, node, expr, attr, for_print=False):
        if expr['node'] == 'AtomId':
            id = expr['id']
            if id in self.units:
                with self.unit(id):
                    return self.get(node, attr)

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

        elif attr == 'toInt' and type in {t.Int, t.Rat, t.Float, t.Bool, t.Char, t.String}:
            value = v.Variable(t.Func([type], t.Int), 'toInt')
        elif attr == 'toRat' and type in {t.Int, t.Rat, t.Bool, t.Char, t.String}:
            value = v.Variable(t.Func([type], t.Rat), 'toRat')
        elif attr == 'toFloat' and type in {t.Int, t.Rat, t.Float, t.Bool, t.Char, t.String}:
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
            elif attr == 'join' and type.subtype in {t.Char, t.String}:
                value = v.Variable(t.Func([type, t.Func.Arg(t.String, default=self.string(''))], t.String), attr)
            elif attr == '_asString' and type.subtype == t.Char:
                value = v.Variable(t.Func([type], t.String), 'asString')

            elif type == t.String:
                value = {
                    'all': self.env['String_all'],
                    'any': self.env['String_any'],
                    'filter': self.env['String_filter'],
                    'map': self.env['String_map'],
                    'fold': self.env['String_fold'],
                    'reduce': self.env['String_reduce'],
                    'split': v.Variable(t.Func([type, type], t.Array(type)), attr),
                    'find': v.Variable(t.Func([type, type, t.Func.Arg(t.Int, default=v.Int(0))], t.Nullable(t.Int)), attr),
                    'count': v.Variable(t.Func([type, type.subtype], t.Int), attr),
                    'startsWith': v.Variable(t.Func([type, type], t.Bool), attr),
                    'endsWith': v.Variable(t.Func([type, type], t.Bool), attr),
                }.get(attr)

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
                    'erase': v.Variable(t.Func([type, t.Int, t.Func.Arg(t.Int, default=v.Int(1))]), attr),
                    'clear': v.Variable(t.Func([type]), attr),
                    'reverse': v.Variable(t.Func([type]), attr),
                    'sort': v.Variable(t.Func([type, t.Func.Arg(t.Bool, 'reverse', default=v.false), t.Func.Arg(t.Func([type.subtype], t.Var('K')), 'key', default={'node': 'AtomPlaceholder'})], type), attr),
                    'copy': v.Variable(t.Func([type], type), attr),
                    'find': v.Variable(t.Func([type, type.subtype], t.Nullable(t.Int)), attr),
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
                    'contains': v.Variable(t.Func([type, type.subtype], t.Bool), attr),
                }.get(attr)

            elif type.isDict():
                value = {
                    'all': self.env['Dict_all'],
                    'any': self.env['Dict_any'],
                    'filter': self.env['Dict_filter'],
                    'map': self.env['Dict_map'],
                    'fold': self.env['Dict_fold'],
                    'update': v.Variable(t.Func([type, type]), attr),
                    'get': v.Variable(t.Func([type, type.key_type], t.Nullable(type.value_type)), attr),
                    'pop': v.Variable(t.Func([type, type.key_type], t.Nullable(type.value_type)), attr),
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
            self.throw(node, err.NoAttribute(type, attr))

        if value.type.isFunc() and not isinstance(value, v.Lambda) and (not type.isClass() or attr in type.methods):
            if for_print:
                value = v.Call(value, obj, type=t.String)
            else:
                value = value.bind(obj)

        return value

    def member(self, node, obj, attr, lvalue=False):
        if attr not in obj.type.members:
            self.throw(node, err.NoAttribute(obj.type, attr))
        if lvalue and attr in obj.type.methods:
            self.throw(node, err.NotLvalue())

        value = v.Attribute(obj, obj.type.members[attr], type=obj.type.members[attr].type)
        if attr in obj.type.methods:
            value = v.Call(f'reinterpret_cast<{value.type.ret} (*)({value.type.args_str()})>', v.Call(value), type=value.type)
        return value

    def cast(self, node, value, type):
        def _cast(value, type):
            # Special case to handle generic functions and lambdas.
            if value.isTemplate():
                if value.bound:
                    type = t.Func([value.bound.type] + type.args, type.ret)
                d = type_variables_assignment(type, value.type)
                if d is None:
                    self.throw(node, err.NoConversion(value.type, type))
                return self.function(value, d)

            # This is the only place where containers are not covariant during type checking.
            if not can_cast(value.type, type, covariance=False):
                self.throw(node, err.NoConversion(value.type, type))

            if not value.type.isNullable() and type.isNullable():
                return v.Nullable(v.Cast(value, type.subtype))
            return v.Cast(value, type)

        return _cast(value, type)

    def unify(self, node, *values):
        if not values:
            return []

        type = unify_types(*[value.type for value in values])
        if type is None:
            self.throw(node, err.UnknownType())

        return [self.cast(node, value, type) for value in values]

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
        return v.Variable(type, self.fake_id(prefix))

    def tmp(self, value, force_var=False):
        if isinstance(value, v.Variable) or not force_var and isinstance(value, v.Literal) and value.type in {t.Int, t.Float, t.Bool, t.Char}:
            return value
        if isinstance(value, v.Value) and value.isTemplate():
            return value
        tmp = self.var(value.type)
        self.store(tmp, value, decl='auto&&')
        return tmp

    def freeze(self, value):
        tmp = self.var(value.type)
        self.store(tmp, value, decl='auto')
        return tmp

    def declare(self, node, type, id, redeclare=False):
        if not type.hasValue() or type.isVar():
            self.throw(node, err.InvalidDeclaration(type))
        if id in self.env and not redeclare:
            self.throw(node, err.RedefinedIdentifier(id))

        var = self.var(type)
        self.env[id] = var
        self.output(c.Var(var), toplevel=(self.env.get('#return') is None))

        return self.env[id]

    def lvalue(self, node, expr, declare=None, override=False):
        if expr['node'] == 'AtomId':
            id = expr['id']

            if id not in self.env:
                if declare is None:
                    self.throw(node, err.UndeclaredIdentifier(id))
                self.declare(node, declare, id)
            elif override:
                self.declare(node, declare, id, redeclare=True)
            elif not isinstance(self.env[id], v.Value) or getattr(self.env[id], 'final', False):
                self.throw(node, err.RedefinedIdentifier(id))

            return self.env[id]

        elif expr['node'] == 'ExprAttr' and not expr.get('safe'):
            obj = self.transpile(expr['expr'])
            attr = expr['attr']
            if obj.type.isTuple():
                return self.attr(node, obj, attr)
            elif obj.type.isClass():
                return self.member(node, obj, attr, lvalue=True)
            else:
                self.throw(node, err.NotLvalue())

        elif expr['node'] == 'ExprIndex' and not expr.get('safe'):
            return self.index(node, *map(self.transpile, expr['exprs']), lvalue=True)

        elif expr['node'] == 'AtomPlaceholder':
            return None

        else:
            self.throw(node, err.NotLvalue())

    def store(self, left, right, decl=None):
        self.output(c.Statement(decl, left, '=', right))

    def assign(self, node, expr, value):
        type = value.type

        if type.isFunc():
            type = t.Func([arg.type for arg in type.args], type.ret)

        exprs = expr['exprs'] if expr['node'] == 'ExprTuple' else [expr]
        len1 = len(exprs)

        if type.isTuple():
            len2 = len(type.elements)
            if len1 > 1 and len1 != len2:
                self.throw(node, err.CannotUnpack(type, len1))
        elif len1 > 1:
            self.throw(node, err.CannotUnpack(type, len1))

        if len1 > 1:
            value = self.tmp(value)
            for i, expr in enumerate(exprs):
                self.assign(node, expr, v.Get(value, i))
        elif value.isTemplate() and expr['node'] == 'AtomId' and expr['id'] not in self.env:
            id = expr['id']
            self.env[id] = value
        else:
            var = self.lvalue(node, expr, declare=type, override=expr.get('override', False))
            if var is None:
                return
            value = self.cast(node, value, var.type)
            self.store(var, value)
            type.literal = False

    def unaryop(self, node, op, value):
        if op in {'+', '-'}:
            types = {t.Int, t.Rat, t.Float}
        elif op == 'not':
            types = {t.Bool}

        if value.type not in types:
            self.throw(node, err.NoUnaryOperator(op, value.type))

        op = {
            'not': '!',
        }.get(op, op)

        return v.UnaryOp(op, value, type=value.type)

    def binaryop(self, node, op, left, right):
        types = [left.type, right.type]

        if op != '^' and left.type in {t.Int, t.Rat} and right.type in {t.Int, t.Rat} and t.Rat in {left.type, right.type}:
            left = self.cast(node, left, t.Rat)
            right = self.cast(node, right, t.Rat)
        if left.type.isNumber() and right.type.isNumber() and t.Float in {left.type, right.type}:
            left = self.cast(node, left, t.Float)
            right = self.cast(node, right, t.Float)

        if op == '^':
            if left.type in {t.Int, t.Rat} and right.type == t.Int:
                return v.Call('pow', v.Cast(left, t.Rat), right, type=t.Rat)
            elif left.type.isNumber() and right.type == t.Rat:
                return v.Call('pow', v.Cast(left, t.Float), v.Cast(right, t.Float), type=t.Float)
            elif left.type == right.type == t.Float:
                return v.Call('pow', left, right, type=t.Float)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '^^':
            if left.type == right.type == t.Int:
                return v.Call('pow', left, right, type=t.Int)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '/':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.BinaryOp(v.Cast(left, t.Rat), op, v.Cast(right, t.Rat), type=t.Rat)
            elif left.type == right.type == t.Float:
                return v.BinaryOp(left, op, right, type=t.Float)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '//':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.Call('floordiv', left, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '%':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.Call('mod', left, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '*':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            elif left.type.isSequence() and right.type == t.Int:
                return v.Call('multiply', left, right, type=left.type)

            elif left.type == t.Int and right.type.isSequence():
                return self.binaryop(node, op, right, left)

            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '&':
            if left.type == right.type and left.type.isSet():
                return v.Call('intersection', left, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '+':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            elif left.type != right.type and left.type in {t.Char, t.Int} and right.type in {t.Char, t.Int}:
                return v.Cast(v.BinaryOp(left, op, right), t.Char)

            elif left.type != right.type and left.type in {t.Char, t.String} and right.type in {t.Char, t.String}:
                return v.Call('concat', v.Cast(left, t.String), v.Cast(right, t.String), type=t.String)

            elif left.type == right.type and left.type.isCollection():
                return v.Call('concat', left, right, type=left.type)

            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '-':
            if left.type == right.type and left.type.isNumber():
                return v.BinaryOp(left, op, right, type=left.type)

            elif left.type == right.type and left.type == t.Char:
                return v.BinaryOp(v.Cast(left, t.Int), op, v.Cast(right, t.Int), type=t.Int)

            elif left.type == t.Char and right.type == t.Int:
                return v.Cast(v.BinaryOp(left, op, right), t.Char)

            elif left.type == right.type and left.type.isSet():
                return v.Call('difference', left, right, type=left.type)

            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        elif op == '%%':
            if left.type == right.type and left.type in {t.Int, t.Rat}:
                return v.BinaryOp(v.BinaryOp(left, '%', right), '==', v.Int(0) if left.type == t.Int else self.rat(0), type=t.Bool)
            else:
                self.throw(node, err.NoBinaryOperator(op, *types))

        else:
            self.throw(node, err.NoBinaryOperator(op, *types))

    def convert_string(self, node, string):
        string = re.sub('{{', '\\\\u007B', string)
        string = re.sub('}}', '\\\\u007D'[::-1], string[::-1])[::-1]
        parts = re.split(r'{([^}]+)}', string)

        if len(parts) == 1:
            return {
                **node,
                'string': string,
            }

        lits, tags = parts[::2], parts[1::2]
        exprs = [None] * len(parts)

        for i, lit in enumerate(lits):
            exprs[i*2] = {
                'node': 'AtomString',
                'string': lit,
            }

        for i, tag in enumerate(tags):
            try:
                expr = parse_expr(ast.literal_eval(f'"{tag}"'))
            except err as e:
                self.throw({
                    **node,
                    'position': [e.line+node['position'][0]-1, e.column+node['position'][1]+1],
                }, err.InvalidSyntax())

            exprs[i*2+1] = {
                'node': 'ExprCall',
                'expr': {
                    'node': 'ExprAttr',
                    'expr': expr,
                    'attr': 'toString',
                },
                'args': [],
            }

        return {
            'node': 'ExprCall',
            'expr': {
                'node': 'ExprAttr',
                'expr': {
                    'node': 'ExprCollection',
                    'kind': 'array',
                    'exprs': exprs,
                },
                'attr': 'join',
            },
            'args': [],
        }

    def convert_lambda(self, expr):
        ids = []

        def convert_expr(expr):
            if expr is None:
                return

            nonlocal ids
            node = expr['node']

            if node in {'ExprCollection', 'DictPair', 'ExprIndex', 'ExprBinaryOp', 'ExprIn', 'ExprCmp', 'ExprLogicalOp', 'ExprCond', 'ExprRange', 'ExprBy', 'ExprTuple'}:
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                }
            if node == 'ExprDict':
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
                expr = self.convert_string(expr, expr['string'])
                if expr['node'] == 'AtomString':
                    return expr
                return convert_expr(expr)
            if node == 'AtomPlaceholder':
                id = f'${len(ids)}'
                ids.append(id)
                return {
                    **expr,
                    'node': 'AtomId',
                    'id': id,
                }
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

        if not body:  # `extern`
            func = v.Variable(template.type, template.id)
            template.cache[real_types] = func

        else:
            with self.local():
                self.env = template.env.copy()
                self.env.update(assigned_types)

                func_type = self.resolve_type(template.type)

                func = self.var(func_type, prefix='f')
                template.cache[real_types] = func

                arg_vars = [self.var(arg.type, prefix='a') for arg in func_type.args]
                block = c.Block()

                with self.block(block):
                    self.env['#return'] = func_type.ret
                    self.env.pop('#loop', None)

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

                    self.transpile(body)

                    if func_type.ret.hasValue():
                        self.output(c.Statement('return', self.default(body, func_type.ret, nullptr_allowed=True)))

            if template.lambda_:
                # The closure is created every time the function is used (except for recursive calls),
                # so current values of variables are captured, possibly different than in the moment of definition.
                del template.cache[real_types]
                self.store(func, v.Lambda(func_type, arg_vars, block, capture_vars=[func]), decl=func_type)
            else:
                self.output(c.Statement(func_type.ret, f'{func}({func_type.args_str()})'), toplevel=True)
                self.output(c.Function(func_type.ret, func, arg_vars, block), toplevel=True)

        return func.bind(template.bound)


    ### Statements ###

    def transpileBlock(self, node):
        for stmt in node['stmts']:
            self.transpile(stmt)

    def transpileStmtUse(self, node):
        name = node['name']
        if name not in self.units:
            self.throw(node, err.InvalidModule(name))

        unit = self.units[name]
        kind, *ids = node['detail']
        if kind == 'only':
            for id in ids:
                if id not in unit.env:
                    self.throw(node, err.UndeclaredIdentifier(id))
                self.env[id] = unit.env[id]
        elif kind == 'hiding':
            hidden = set()
            for id in ids:
                if id not in unit.env:
                    self.throw(node, err.UndeclaredIdentifier(id))
                hidden.add(id)
            self.env.update({x: unit.env[x] for x in unit.env.keys() - hidden})
        elif kind == 'as':
            self.units[ids[0]] = unit
        else:
            self.env.update(unit.env)

    def transpileStmtSkip(self, node):
        pass

    def transpileStmtPrint(self, node):
        values = lmap(self.transpile, node['exprs'])

        for i, value in enumerate(values):
            if not value.type.isPrintable():
                self.throw(node, err.NotPrintable(value.type))

            if i > 0:
                self.output(c.Statement(v.Call('write', self.string(' '))))
            self.output(c.Statement(v.Call('write', self.attr(node, value, 'toString', for_print=True))))

        self.output(c.Statement(v.Call('write', self.string('\\n'))))  # std::endl is very slow

    def transpileStmtDecl(self, node):
        type = self.resolve_type(self.transpile(node['type']))
        id = node['id']
        expr = node['expr']
        var = self.declare(node, type, id)

        if expr:
            value = self.cast(node, self.transpile(expr), type)
        else:
            value = self.default(node, type, nullptr_allowed=True)

        self.store(var, value)

    def transpileStmtAssg(self, node):
        value = self.transpile(node['expr'], void_allowed=(len(node['lvalues']) == 0))

        if value.type == t.Void:
            self.output(value)
        else:
            value = self.tmp(value)

        for lvalue in node['lvalues']:
            self.assign(lvalue, lvalue, value)

    def transpileStmtAssgExpr(self, node):
        exprs = node['exprs']
        op = node['op']
        left = self.lvalue(node, exprs[0])
        if left is None:
            self.throw(node, err.InvalidUsage('_'))

        if op == '??':
            block = c.Block()
            self.output(c.If(v.IsNull(left), block))
            with self.block(block):
                right = self.transpile(exprs[1])
                if not left.type.isNullable() or not can_cast(right.type, left.type.subtype):
                    self.throw(node, err.NoBinaryOperator(op, left.type, right.type))
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

        stmt = None

        for expr, block in reversed(list(zip_longest(exprs, blocks))):
            if expr:
                cond = self.cast(expr, self.transpile(expr), t.Bool)

            then = c.Block()
            with self.block(then):
                with self.local():
                    self.transpile(block)

            if expr:
                stmt = c.If(cond, then, stmt)
            else:
                stmt = then

        self.output(stmt)

    def transpileStmtWhile(self, node):
        expr = node['expr']

        with self.local():
            self.env['#loop'] = True

            body = c.Block()
            with self.block(body):
                cond = self.cast(expr, self.transpile(expr), t.Bool)
                cond = v.UnaryOp('!', cond)
                self.output(c.If(cond, c.Statement('break')))

                self.transpile(node['block'])

        self.output(c.While(v.true, body))

    def transpileStmtUntil(self, node):
        expr = node['expr']

        with self.local():
            self.env['#loop'] = True

            second_iteration = self.var(t.Bool)
            self.store(second_iteration, v.false, 'auto')

            body = c.Block()
            with self.block(body):
                cond = self.cast(expr, self.transpile(expr), t.Bool)
                cond = v.BinaryOp(second_iteration, '&&', cond)
                self.output(c.If(cond, c.Statement('break')))
                self.store(second_iteration, v.true)

                self.transpile(node['block'])

        self.output(c.While(v.true, body))

    def transpileStmtFor(self, node):
        vars = node['vars']
        iterables = node['iterables']

        types = []
        conditions = []
        updates = []
        getters = []

        def prepare(iterable):
            # It must be a function so that there are separate scopes of variables to use in lambdas.

            if iterable['node'] == 'ExprBy':
                step_expr = iterable['exprs'][1]
                step = self.freeze(self.transpile(step_expr))
                iterable = iterable['exprs'][0]
            else:
                step_expr = None
                step = self.freeze(v.Int(1))

            if iterable['node'] == 'ExprRange':
                values = lmap(self.transpile, iterable['exprs'])
                values = self.unify(iterable, *values)
                type = values[0].type
                if type not in {t.Int, t.Rat, t.Float, t.Bool, t.Char}:
                    self.throw(iterable, err.UnknownType())

                types.append(type)
                index = iterator = self.var({t.Rat: t.Rat, t.Float: t.Float}.get(type, t.Int))
                start = v.Cast(values[0], index.type)
                self.cast(step_expr, step, index.type)

                if len(values) == 1:
                    cond = lambda: v.true  # infinite range
                else:
                    end = self.freeze(values[1])
                    eq = '=' if iterable['inclusive'] else ''
                    neg = self.tmp(v.BinaryOp(step, '<', v.Cast(v.Int(0), step.type), type=t.Bool))
                    cond = lambda: v.TernaryOp(neg, f'{index} >{eq} {end}', f'{index} <{eq} {end}')

                update = lambda: v.BinaryOp(index, '+=', step)
                getter = lambda: v.Cast(index, type)

            else:
                value = self.tmp(self.transpile(iterable))
                type = value.type
                if not type.isIterable():
                    self.throw(iterable, err.NotIterable(type))

                types.append(type.subtype)
                iterator = self.var(None)
                start = self.tmp(v.Call(v.Attribute(value, 'begin')))
                end = self.tmp(v.Call(v.Attribute(value, 'end')))

                if type.isSequence():
                    self.output(c.If(f'{step} < 0 && {start} != {end}', c.Statement(start, '=', v.Call('std::prev', end))))
                    index = self.tmp(v.Int(0), force_var=True)
                    length = self.tmp(v.Call(v.Attribute(value, 'size')))
                    cond = lambda: f'{index} < {length}'
                    update = lambda: f'{index} += std::abs({step}), {iterator} += {step}'
                else:
                    self.store(step, f'std::abs({step})')
                    cond = lambda: f'{iterator} != {end}'
                    update = lambda: f'safe_advance({iterator}, {end}, {step})'

                getter = lambda: v.UnaryOp('*', iterator, type=type.subtype)

            self.store(iterator, start, 'auto')
            conditions.append(cond)
            updates.append(update)
            getters.append(getter)

        for iterable in iterables:
            prepare(iterable)

        body = c.Block()
        with self.block(body):
            with self.local():
                self.env['#loop'] = True

                if len(vars) == 1 and len(types) > 1:
                    tuple = v.Tuple([getter() for getter in getters])
                    self.assign(node, vars[0], tuple)
                elif len(vars) > 1 and len(types) == 1:
                    if not types[0].isTuple():
                        self.throw(node, err.CannotUnpack(types[0], len(vars)))
                    tuple = getters[0]()
                    for i, var in enumerate(vars):
                        self.assign(node, var, v.Get(tuple, i))
                elif len(vars) == len(types):
                    for var, getter in zip(vars, getters):
                        self.assign(node, var, getter())
                else:
                    self.throw(node, err.CannotUnpack(t.Tuple(types), len(vars)))

                self.transpile(node['block'])

        condition = ' && '.join(str(cond()) for cond in conditions)
        update = ', '.join(str(update()) for update in updates)
        self.output(c.For('', condition, update, body))

    def transpileStmtLoopControl(self, node):
        stmt = node['stmt']  # `break` / `continue`

        if not self.env.get('#loop'):
            self.throw(node, err.InvalidUsage(stmt))

        self.output(c.Statement(stmt))

    def transpileStmtFunc(self, node, class_type=None):
        id = node['id']
        if class_type is None and id in self.env:
            self.throw(node, err.RedefinedIdentifier(id))

        with self.local():
            typevars = node.get('typevars', [])
            for name in typevars:
                self.env[name] = t.Var(name)

            args = [] if class_type is None else [t.Func.Arg(class_type, 'this')]
            for arg in node['args']:
                type = self.transpile(arg['type'])
                if not type.hasValue():
                    self.throw(arg['type'], err.InvalidDeclaration(type))
                name = arg['name']
                default = arg.get('default')
                variadic = arg.get('variadic')
                if variadic:
                    if any(arg.variadic for arg in args):
                        self.throw(arg, err.RepeatedVariadic())
                    type = t.Array(type)
                args.append(t.Func.Arg(type, name, default, variadic))

            ret_type = self.transpile(node.get('ret')) or t.Void
            if node.get('generator'):
                self.require('generators')
                ret_type = t.Generator(ret_type)
            func_type = t.Func(args, ret_type)

            env = self.env.copy()

            lambda_ = node.get('lambda') or self.env.get('#return') is not None
            func = v.FunctionTemplate(id, typevars, func_type, node['block'], env, lambda_)

        if class_type is None:
            self.env[id] = env[id] = func
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
        id = node['id']
        if id in self.env:
            self.throw(node, err.RedefinedIdentifier(id))

        base = self.transpile(node['base'])
        if base and not base.isClass():
            self.throw(node, err.NotClass(base))

        base_members = base.members if base else {}
        members = dict(base_members)
        base_methods = base.methods if base else {}
        methods = dict(base_methods)

        type = t.Class(id, base, members, methods)
        self.env[id] = type

        cls = self.var(t.Func([], type), prefix='c')
        type.initializer = cls

        fields = c.Block()
        self.output(c.Statement('struct', cls), toplevel=True)
        self.output(c.Struct(cls, fields, base=(base.initializer if base else None)), toplevel=True)

        for member in node['members']:
            if member['node'] == 'ClassField':
                name = member['id']
                if name in members:
                    self.throw(member, err.RepeatedMember(name))
                if name == 'toString':
                    self.throw(member, err.InvalidMember(name))

                field = self.var(self.transpile(member['type']), prefix='m')

                default = member.get('default')
                if default:
                    field.default = self.cast(member, self.transpile(default), field.type)
                else:
                    field.default = self.default(member, field.type, nullptr_allowed=True)

                fields.append(c.Statement(c.Var(field)))
                members[name] = field

        if not any(member['id'] == 'toString' for member in node['members']) and (not base or 'toString' in base.default_methods):
            node['members'].append({
                'node': 'ClassMethod',
                'id': 'toString',
                'args': [],
                'ret': t.String,
                'block': {
                    'node': 'StmtReturn',
                    'expr': self.string(f'{id} object'),
                },
            })
            type.default_methods.add('toString')

        for member in node['members']:
            if member['node'] != 'ClassField':
                name = member['id']
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
        exprs = node['exprs']
        kind = node['kind']
        types = []

        with self.no_output():
            for expr in exprs:
                if expr['node'] in {'ExprRange', 'ExprBy'}:
                    if expr['node'] == 'ExprBy':
                        if expr['exprs'][0]['node'] != 'ExprRange':
                            self.throw(node, err.InvalidSyntax())
                        expr = expr['exprs'][0]
                    values = lmap(self.transpile, expr['exprs'])
                    types.extend(value.type for value in values)

                elif expr['node'] == 'ExprSpread':
                    expr = expr['expr']
                    if expr['node'] == 'ExprBy':
                        expr = expr['exprs'][0]
                    value = self.transpile(expr)
                    if not value.type.isIterable():
                        self.throw(node, err.NotIterable(value.type))
                    types.append(value.type.subtype)

                else:
                    value = self.transpile(expr)
                    types.append(value.type)

        type = t.Unknown
        type.literal = True
        if types:
            type = unify_types(*types)
            if type is None:
                self.throw(node, err.UnknownType())
            type.literal = all(t.literal for t in types)

        if kind == 'array':
            result = self.tmp(v.Array([], type))
        elif kind == 'set':
            if not type.isHashable():
                self.throw(node, err.NotHashable(type))
            result = self.tmp(v.Set([], type))
        result.type.literal = True

        for expr in exprs:
            if expr['node'] in {'ExprRange', 'ExprSpread', 'ExprBy'}:
                if expr['node'] == 'ExprSpread':
                    expr = expr['expr']

                var = {
                    'node': 'AtomId',
                    'position': expr['position'],
                    'id': self.fake_id(),
                }
                self.transpile({
                    'node': 'StmtFor',
                    'vars': [var],
                    'iterables': [expr],
                    'block': {
                        'node': 'StmtAppend',
                        'collection': result,
                        'exprs': [var],
                    },
                })
            else:
                self.transpile({
                    'node': 'StmtAppend',
                    'collection': result,
                    'exprs': [expr],
                })

        return result

    def transpileExprDict(self, node):
        items = node['items']
        types = [], []

        with self.no_output():
            for item in items:
                if item['node'] == 'DictSpread':
                    expr = item['expr']
                    if expr['node'] == 'ExprBy':
                        expr = expr['exprs'][0]
                    value = self.transpile(expr)
                    if not value.type.isDict():
                        self.throw(node, err.NotDictionary(value.type))
                    types[0].append(value.type.key_type)
                    types[1].append(value.type.value_type)

                elif item['node'] == 'DictPair':
                    values = lmap(self.transpile, item['exprs'])
                    for i in range(2):
                        types[i].append(values[i].type)

        key_type = value_type = t.Unknown
        key_type.literal = value_type.literal = True
        if types[0]:
            key_type = unify_types(*types[0])
            value_type = unify_types(*types[1])
            if key_type is None or value_type is None:
                self.throw(node, err.UnknownType())
            key_type.literal = all(t.literal for t in types[0])
            value_type.literal = all(t.literal for t in types[1])

        if not key_type.isHashable():
            self.throw(node, err.NotHashable(key_type))
        result = self.tmp(v.Dict([], [], key_type, value_type))
        result.type.literal = True

        for item in items:
            if item['node'] == 'DictSpread':
                vars = [{
                    'node': 'AtomId',
                    'id': self.fake_id(),
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
            elif item['node'] == 'DictPair':
                self.transpile({
                    'node': 'StmtAppend',
                    'collection': result,
                    'exprs': item['exprs'],
                })

        return result

    def transpileExprComprehension(self, node):
        exprs = node['exprs']
        kind = node['kind']

        value, collection = [{
            'node': 'AtomId',
            'id': self.fake_id(),
        } for _ in range(2)]

        stmt = inner_stmt = {
            'node': 'StmtAssg',
            'lvalues': [value],
            'expr': {
                'node': 'ExprTuple',
                'exprs': exprs,
            },
        }

        for i, cpr in reversed(list(enumerate(node['comprehensions']))):
            if cpr['node'] == 'ComprehensionIteration':
                stmt = {
                    **cpr,
                    'node': 'StmtFor',
                    'vars': [{**var, 'override': True} for var in cpr['vars']],
                    'block': stmt,
                }
            elif cpr['node'] == 'ComprehensionPredicate':
                if i == 0:
                    self.throw(cpr, err.InvalidSyntax())
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
                self.assign(node, collection, v.Array([], types[0]))
            elif kind == 'set':
                if not types[0].isHashable():
                    self.throw(node, err.NotHashable(types[0]))
                self.assign(node, collection, v.Set([], types[0]))
            elif kind == 'dict':
                if not types[0].isHashable():
                    self.throw(node, err.NotHashable(types[0]))
                self.assign(node, collection, v.Dict([], [], *types))

            inner_stmt['node'] = 'StmtAppend'
            inner_stmt['collection'] = collection
            inner_stmt['exprs'] = exprs

            self.transpile(stmt)

            result = self.transpile(collection)

        result.type.literal = True
        return result

    def transpileExprAttr(self, node):
        expr = node['expr']
        attr = node['attr']

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
            self.throw(node, err.NotIndexable(type))

        a = v.Nullable(self.cast(slice[0], self.transpile(slice[0]), t.Int)) if slice[0] else v.null
        b = v.Nullable(self.cast(slice[1], self.transpile(slice[1]), t.Int)) if slice[1] else v.null
        step = self.cast(slice[2], self.transpile(slice[2]), t.Int) if slice[2] else v.Int(1)

        return v.Call('slice', collection, a, b, step, type=type)

    def transpileExprCall(self, node):
        expr = node['expr']

        def _resolve_args(func):
            if not func.type.isFunc():
                self.throw(node, err.NotFunction(func.type))

            obj = None
            if func.isTemplate() and func.bound:
                obj = func.bound

            func_args = func.type.args[1:] if obj else func.type.args[:]
            func_named_args = {func_arg.name for func_arg in func_args}

            args = []
            pos_args = []
            named_args = {}

            for i, call_arg in enumerate(node['args']):
                name = call_arg['name']
                expr = call_arg['expr']
                if name:
                    if name in named_args:
                        self.throw(node, err.RepeatedArgument(name))
                    if name not in func_named_args:
                        self.throw(node, err.UnexpectedArgument(name))
                    named_args[name] = expr
                else:
                    if named_args:
                        self.throw(node, err.ExpectedNamedArgument())
                    pos_args.append(expr)

            with self.local():
                type_variables = defaultdict(list)

                for i, func_arg in enumerate(func_args):
                    name = func_arg.name

                    if name in named_args:
                        if i < len(pos_args):
                            self.throw(node, err.RepeatedArgument(name))

                        expr = named_args.pop(name)

                    elif func_arg.variadic and (pos_args or not func_arg.default):
                        expr = {
                            'node': 'ExprCollection',
                            'kind': 'array',
                            'exprs': pos_args[i:],
                        }
                        pos_args = []

                    elif i < len(pos_args):
                        expr = pos_args[i]
                        pos_args[i] = None

                    elif func_arg.default:
                        if isinstance(func_arg.default, v.Value):
                            args.append(func_arg.default)
                            continue
                        else:
                            expr = func_arg.default

                    else:
                        if name is None:
                            self.throw(node, err.TooFewArguments())
                        else:
                            self.throw(node, err.MissingArgument(name))

                    value = self.transpile(expr)

                    if not value.isTemplate():
                        d = type_variables_assignment(value.type, func_arg.type)
                        if d is None:
                            self.throw(node, err.NoConversion(value.type, func_arg.type))

                        for name, type in d.items():
                            type_variables[name].append(type)

                    args.append(value)

                if any(arg is not None for arg in pos_args):
                    self.throw(node, err.TooManyArguments())

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
                        self.throw(node, err.InvalidArgumentTypes(t.Var(name)))

                    self.env[name] = assigned_types[name] = type

                try:
                    for i in range(len(args)):
                        type = self.resolve_type(func_args[i].type)
                        args[i] = self.cast(node, args[i], type)
                        d = type_variables_assignment(args[i].type, func_args[i].type)
                        assigned_types.update(d)
                        self.env.update(d)
                except err as e:
                    if not func.isTemplate():
                        raise
                    self.throw(node, err.InvalidFunctionCall(func.id, assigned_types, str(e)[:-1]))

                if func.isTemplate():
                    try:
                        func = self.function(func, assigned_types)
                    except err as e:
                        self.throw(node, err.InvalidFunctionCall(func.id, assigned_types, str(e)[:-1]))

                return func, args

        def _call(func):
            func, args = _resolve_args(func)

            return v.Call(func, *args, type=func.type.ret)

        if expr['node'] == 'ExprAttr':
            attr = expr['attr']

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

                return self.safe(node, obj, callback, lambda: v.null)

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
            constructor_type = t.Func([t.Func.Arg(field.type, name, field.default) for name, field in fields.items()])
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
        op = node['op']
        value = self.transpile(node['expr'])

        if op == '!':
            if not value.type.isNullable():
                self.throw(node, err.NotNullable(value.type))

            return v.Extract(value)

        return self.unaryop(node, op, value)

    def transpileExprBinaryOp(self, node):
        op = node['op']
        exprs = node['exprs']

        if op == '??':
            left = self.tmp(self.transpile(exprs[0]))
            try:
                if left.type == t.Nullable(t.Unknown):
                    return self.transpile(exprs[1])
                return self.safe(node, left, lambda: v.Extract(left), lambda: self.transpile(exprs[1]))
            except err:
                self.throw(node, err.NoBinaryOperator(op, left.type, self.transpile(exprs[1]).type))

        return self.binaryop(node, op, *map(self.transpile, exprs))

    def transpileExprIsNull(self, node):
        value = self.transpile(node['expr'])
        if not value.type.isNullable():
            self.throw(node, err.NotNullable(value.type))

        if value.type == t.Unknown:  # for the `null is null` case
            return v.Bool(not node.get('not'))

        return v.IsNotNull(value) if node.get('not') else v.IsNull(value)

    def transpileExprIn(self, node):
        exprs = node['exprs']

        element = self.transpile(exprs[0])
        iterable = self.transpile(exprs[1])
        if not iterable.type.isIterable():
            self.throw(node, err.NotIterable(iterable.type))

        if iterable.type == t.String:
            type = iterable.type
        elif iterable.type.isDict():
            type = iterable.type.key_type
        else:
            type = iterable.type.subtype

        if type == t.Unknown:  # for the case of empty container
            return v.Bool(node.get('not'))

        element = self.cast(node, element, type)
        result = v.Call('contains', iterable, element, type=t.Bool)
        return v.UnaryOp('!', result, type=t.Bool) if node.get('not') else result

    def transpileExprCmp(self, node):
        exprs = node['exprs']
        ops = node['ops']

        result = self.var(t.Bool)
        self.store(result, v.false, 'auto')

        left = self.transpile(exprs[0])

        def emitIf(index):
            nonlocal left
            right = self.transpile(exprs[index])
            op = ops[index-1]

            try:
                left, right = self.unify(node, left, right)
                right = self.tmp(right)
            except err:
                self.throw(node, err.NotComparable(left.type, right.type))

            if not left.type.isComparable():
                self.throw(node, err.NotComparable(left.type, right.type))
            if not left.type.isOrderable() and op not in {'==', '!='}:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

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

    def transpileExprLogicalOp(self, node):
        exprs = node['exprs']
        op = node['op']

        result = self.var(t.Bool)
        self.store(result, v.Bool(op == 'or'), 'auto')

        cond1 = self.transpile(exprs[0])
        if op == 'or':
            cond1 = v.UnaryOp('!', cond1, type=t.Bool)

        block = c.Block()
        self.output(c.If(cond1, block))
        with self.block(block):
            cond2 = self.transpile(exprs[1])
            if not cond1.type == cond2.type == t.Bool:
                self.throw(node, err.NoBinaryOperator(op, cond1.type, cond2.type))
            self.store(result, cond2)

        return result

    def transpileExprCond(self, node):
        exprs = node['exprs']
        return self.cond(node, self.transpile(exprs[0]), lambda: self.transpile(exprs[1]), lambda: self.transpile(exprs[2]))

    def transpileExprRange(self, node):
        self.throw(node, err.InvalidSyntax())

    def transpileExprSpread(self, node):
        self.throw(node, err.InvalidSyntax())

    def transpileExprBy(self, node):
        self.throw(node, err.InvalidSyntax())

    def transpileExprLambda(self, node):
        id = self.fake_id()
        typevars = [f'$T{i}' for i in range(len(node['ids'])+1)]

        if node.get('block'):
            block = node['block']
        else:
            block = {
                **node,
                'node': 'StmtReturn',
                'expr': node['expr'],
            }

        self.transpile({
            **node,
            'node': 'StmtFunc',
            'id': id,
            'typevars': typevars,
            'args': [{
                'type': {
                    'node': 'TypeName',
                    'name': typevars[i],
                },
                'name': name,
            } for i, name in enumerate(node['ids'], 1)],
            'ret': {
                'node': 'TypeName',
                'name': typevars[0],
            },
            'block': block,
            'lambda': node.get('block') is None,
        })

        return self.get(node, id)

    def transpileExprTuple(self, node):
        elements = lmap(self.transpile, node['exprs'])
        return v.Tuple(elements)


    ### Atoms ###

    def transpileAtomInt(self, node):
        value = node['int']
        if value < 2**63:
            return v.Int(value)
        else:
            return self.rat(value)

    def transpileAtomRat(self, node):
        return self.rat(node['rat'])

    def transpileAtomFloat(self, node):
        return v.Float(node['float'])

    def transpileAtomBool(self, node):
        return v.Bool(node['bool'])

    def transpileAtomChar(self, node):
        return v.Char(node['char'])

    def transpileAtomString(self, node):
        expr = self.convert_string(node, node['string'])

        if expr['node'] == 'AtomString':
            return self.string(expr['string'])

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

    def transpileAtomDefault(self, node):
        return self.default(node, self.resolve_type(self.transpile(node['type'])))

    def transpileAtomId(self, node):
        return self.get(node, node['id'])


    ### Types ###

    def transpileTypeName(self, node):
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

    def transpileTypeArray(self, node):
        return t.Array(self.transpile(node['subtype']))

    def transpileTypeSet(self, node):
        return t.Set(self.transpile(node['subtype']))

    def transpileTypeDict(self, node):
        return t.Dict(self.transpile(node['key_type']), self.transpile(node['value_type']))

    def transpileTypeNullable(self, node):
        return t.Nullable(self.transpile(node['subtype']))

    def transpileTypeTuple(self, node):
        return t.Tuple(lmap(self.transpile, node['elements']))

    def transpileTypeFunc(self, node):
        return t.Func(lmap(self.transpile, node['args']), self.transpile(node['ret']) or t.Void)
