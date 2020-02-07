
import re
from collections import defaultdict
from contextlib import contextmanager
from itertools import zip_longest

import cgen as c

from . import values as v
from . import types as t
from .errors import PyxellError as err
from .parsing import parse_expr
from .types import can_cast, get_type_variables, type_variables_assignment, unify_types
from .utils import *


class Unit:

    def __init__(self):
        self.env = {}
        self.initialized = set()
        self.levels = {}


class PyxellCompiler:

    def __init__(self):
        self.units = {}
        self._unit = None
        self.level = 0
        self._tmp_index = 0

        self._block = c.Block()
        self.main = c.FunctionBody(c.FunctionDeclaration(c.Value('int', 'main'), []), self._block)

        self.module = c.Module([
            c.Line(),
            c.Include('lib/base.hpp', system=False),
            c.Line(),
            self.main,
            c.Line()
        ])

    def run(self, ast, unit):
        self.units[unit] = Unit()
        with self.unit(unit):
            # if unit != 'std':
            #     self.env = self.units['std'].env.copy()
            #     self.initialized = self.units['std'].initialized.copy()
            #     self.levels = self.units['std'].levels.copy()
            self.compile(ast)

    def run_main(self, ast):
        self.run(ast, 'main')
        return str(self.module)

    def compile(self, node):
        if not isinstance(node, dict):
            return node
        result = getattr(self, 'compile'+node['node'])(node)
        if '_eval' in node:
            node['_eval'] = node['_eval']()
        return result

    def expr(self, code, **params):
        return self.compile(parse_expr(code.format(**params)))

    def throw(self, node, msg):
        line, column = node.get('position', (1, 1))
        raise err(msg, line, column)


    ### Helpers ###

    @property
    def env(self):
        return self._unit.env

    @env.setter
    def env(self, env):
        self._unit.env = env

    @property
    def initialized(self):
        return self._unit.initialized

    @initialized.setter
    def initialized(self, initialized):
        self._unit.initialized = initialized

    @property
    def levels(self):
        return self._unit.levels

    @levels.setter
    def levels(self, levels):
        self._unit.levels = levels

    @contextmanager
    def local(self, next_level=False):
        env = self.env.copy()
        initialized = self.initialized.copy()
        levels = self.levels.copy()
        if next_level:
            self.level += 1
        yield
        self.env = env
        self.initialized = initialized
        self.levels = levels
        if next_level:
            self.level -= 1

    @contextmanager
    def unit(self, name):
        _unit = self._unit
        self._unit = self.units[name]
        yield
        self._unit = _unit

    @contextmanager
    def block(self, block):
        _block = self._block
        self._block = block
        yield
        self._block = _block

    @contextmanager
    def no_output(self):
        with self.block(c.Block()):
            yield

    def output(self, line):
        if isinstance(line, (str, v.Value)):
            line = c.Statement(str(line))
        self._block.append(line)

    def resolve_type(self, type):
        if type.isVar():
            return self.env[type.name]
        if type.isArray():
            return t.Array(self.resolve_type(type.subtype))
        if type.isNullable():
            return t.Nullable(self.resolve_type(type.subtype))
        if type.isTuple():
            return t.Tuple([self.resolve_type(type) for type in type.elements])
        if type.isFunc():
            return t.Func([Arg(self.resolve_type(arg.type), arg.name, arg.default) for arg in type.args], self.resolve_type(type.ret))
        return type


    ### Code generation ###

    def get(self, node, id):
        if id not in self.env:
            self.throw(node, err.UndeclaredIdentifier(id))

        if id in self.levels and self.levels[id] != 0 and self.levels[id] < self.level:
            self.throw(node, err.ClosureRequired(id))

        result = self.env[id]

        if isinstance(result, t.Type) and result.isClass():
            if not result.constructor:
                self.throw(node, err.AbstractClass(result))
            result = result.constructor

        if not isinstance(result, v.Value):
            self.throw(node, err.NotVariable(id))

        if id not in self.initialized:
            self.throw(node, err.UninitializedIdentifier(id))

        return result

    def extract(self, ptr, *indices, load=True):
        ptr = self.builder.gep(ptr, [v.Int(0), *[ll.Constant(ll.IntType(32), i) for i in indices]])
        return self.builder.load(ptr) if load else ptr

    def insert(self, value, ptr, *indices):
        return self.builder.store(value, self.builder.gep(ptr, [v.Int(0), *[ll.Constant(ll.IntType(32), i) for i in indices]]))

    def index(self, node, collection, index, lvalue=False):
        if collection.type.isCollection():
            if lvalue and not collection.type.isArray():
                self.throw(node, err.NotLvalue())

            if collection.type == t.String:
                subtype = t.Char
            elif collection.type.isArray():
                subtype = collection.type.subtype

            return v.Index(collection, index, type=subtype)

        self.throw(node, err.NotIndexable(collection.type))

    def safe(self, node, value, callback_notnull, callback_null):
        if not value.type.isNullable():
            self.throw(node, err.NotNullable(value.type))

        with self.builder.if_else(self.builder.icmp_unsigned('!=', value, v.Null())) as (label_notnull, label_null):
            with label_notnull:
                value_notnull = callback_notnull()
                label_notnull = self.builder.basic_block
            with label_null:
                value_null = callback_null()
                label_null = self.builder.basic_block

        type = unify_types(value_notnull.type, value_null.type)
        if type is None:
            self.throw(node, err.UnknownType())

        phi = self.builder.phi(type)
        phi.add_incoming(self.cast(node, value_notnull, type), label_notnull)
        phi.add_incoming(self.cast(node, value_null, type), label_null)
        return phi

    def attribute(self, node, expr, attr):
        if expr['node'] == 'AtomId':
            id = expr['id']
            if id in self.units:
                with self.unit(id):
                    return None, self.get(node, attr)

        obj = self.compile(expr)
        return obj, self.attr(node, obj, attr)

    def attr(self, node, obj, attr):
        type = obj.type
        value = None

        if type == t.Int:
            if attr == 'toString':
                value = self.env['Int_toString']
            elif attr == 'toFloat':
                value = self.env['Int_toFloat']
            elif attr == 'char':
                value = self.builder.trunc(obj, t.Char)

        elif type == t.Float:
            if attr == 'toString':
                value = self.env['Float_toString']
            elif attr == 'toInt':
                value = self.env['Float_toInt']

        elif type == t.Bool:
            if attr == 'toString':
                value = self.env['Bool_toString']
            elif attr == 'toInt':
                value = self.env['Bool_toInt']
            elif attr == 'toFloat':
                value = self.env['Bool_toFloat']

        elif type == t.Char:
            if attr == 'toString':
                value = self.env['Char_toString']
            elif attr == 'toInt':
                value = self.env['Char_toInt']
            elif attr == 'toFloat':
                value = self.env['Char_toFloat']
            elif attr == 'code':
                value = self.builder.zext(obj, t.Int)

        elif type.isCollection():
            if attr == 'length':
                value = v.Cast(v.Call(v.Attribute(obj, 'size')), t.Int)
            elif type == t.String:
                if attr == 'toString':
                    value = self.env['String_toString']
                elif attr == 'toArray':
                    value = self.env['String_toArray']
                elif attr == 'toInt':
                    value = self.env['String_toInt']
                elif attr == 'toFloat':
                    value = self.env['String_toFloat']
                elif attr == 'all':
                    value = self.env['String_all']
                elif attr == 'any':
                    value = self.env['String_any']
                elif attr == 'filter':
                    value = self.env['String_filter']
                elif attr == 'map':
                    value = self.env['String_map']
                elif attr == 'reduce':
                    value = self.env['String_reduce']
            elif type.isArray():
                if attr == 'join':
                    if type.subtype == t.Char:
                        value = self.env['CharArray_join']
                    elif type.subtype == t.String:
                        value = self.env['StringArray_join']
                elif attr == 'all':
                    value = self.env['Array_all']
                elif attr == 'any':
                    value = self.env['Array_any']
                elif attr == 'filter':
                    value = self.env['Array_filter']
                elif attr == 'map':
                    value = self.env['Array_map']
                elif attr == 'reduce':
                    value = self.env['Array_reduce']

        elif type.isTuple() and len(attr) == 1:
            index = ord(attr) - ord('a')
            if 0 <= index < len(type.elements):
                value = v.Get(obj, index)

        elif type.isClass():
            value = self.member(node, obj, attr)

        if value is None:
            self.throw(node, err.NoAttribute(type, attr))

        return value

    def member(self, node, obj, attr, lvalue=False):
        if lvalue and not obj.type.isClass():
            self.throw(node, err.NotLvalue())

        try:
            index = list(obj.type.members.keys()).index(attr)
        except ValueError:
            self.throw(node, err.NoAttribute(obj.type, attr))

        if lvalue and attr in obj.type.methods:
            self.throw(node, err.NotLvalue())

        ptr = self.extract(obj, index, load=False)
        return ptr if lvalue else self.builder.load(ptr)

    def call(self, node, name, *values):
        return self.builder.call(self.get(node, name), values)

    def cast(self, node, value, type):
        if not can_cast(value.type, type):
            self.throw(node, err.IllegalAssignment(value.type, type))
        if not value.type.isNullable() and type.isNullable():
            return self.cast(node, self.nullable(value), type)

        if value.type == type:
            return value
        else:
            return v.Cast(value, type)

    def unify(self, node, *values):
        if not values:
            return []

        type = unify_types(*[value.type for value in values])
        if type is None:
            self.throw(node, err.UnknownType())

        return [self.cast(node, value, type) for value in values]

    def tmp(self, value):
        if isinstance(value, v.Variable):
            return value
        tmp = v.Variable(value.type, f'tmp{self._tmp_index}')
        self._tmp_index += 1
        self.store(tmp, value)
        return tmp

    def declare(self, node, type, id, redeclare=False, initialize=False, check_only=False):
        if type == t.Void:
            self.throw(node, err.InvalidDeclaration(type))
        if id in self.env and not redeclare:
            self.throw(node, err.RedeclaredIdentifier(id))
        if check_only:
            return

        self.output(f'{type} {id}')
        self.env[id] = v.Variable(type, id)

        if initialize:
            self.initialized.add(id)
        self.levels[id] = self.level

        return self.env[id]

    def lvalue(self, node, expr, declare=None, override=False, initialize=False):
        if expr['node'] == 'AtomId':
            id = expr['id']

            if id not in self.env:
                if declare is None:
                    self.throw(node, err.UndeclaredIdentifier(id))
                self.declare(node, declare, id)
            elif override:
                self.declare(node, declare, id, redeclare=True)
            elif not isinstance(self.env[id], v.Value) or getattr(self.env[id], 'final', False):
                self.throw(node, err.IllegalRedefinition(id))

            if initialize:
                self.initialized.add(id)

            return self.env[id]

        elif expr['node'] == 'ExprAttr' and not expr.get('safe'):
            return self.member(node, self.compile(expr['expr']), expr['attr'], lvalue=True)

        elif expr['node'] == 'ExprIndex' and not expr.get('safe'):
            return self.index(node, *map(self.compile, expr['exprs']), lvalue=True)

        else:
            self.throw(node, err.NotLvalue())

    def store(self, left, right):
        spec = 'auto&& ' if isinstance(left, v.Variable) and left.name not in self.env else ''
        self.output(f'{spec}{left} = {right}')

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
        else:
            var = self.lvalue(node, expr, declare=type, override=expr.get('override', False), initialize=True)
            value = self.cast(node, value, var.type)
            self.store(var, value)

    def inc(self, ptr, step=v.Int(1)):
        add = self.builder.fadd if ptr.type.pointee == t.Float else self.builder.add
        self.builder.store(add(self.builder.load(ptr), step), ptr)

    def sizeof(self, type, length=v.Int(1)):
        return self.builder.ptrtoint(self.builder.gep(v.Null(t.Ptr(type)), [length]), t.Int)

    def malloc(self, type, length=v.Int(1)):
        size = self.sizeof(type.pointee, length)
        ptr = self.builder.call(self.builtins['malloc'], [size])
        return self.builder.bitcast(ptr, type)

    def realloc(self, ptr, length=v.Int(1)):
        type = ptr.type
        size = self.sizeof(type.pointee, length)
        ptr = self.builder.bitcast(ptr, t.Ptr())
        ptr = self.builder.bitcast(ptr, t.Ptr())
        ptr = self.builder.call(self.builtins['realloc'], [ptr, size])
        return self.builder.bitcast(ptr, type)

    def memcpy(self, dest, src, length):
        type = dest.type
        dest = self.builder.bitcast(dest, t.Ptr())
        src = self.builder.bitcast(src, t.Ptr())
        size = self.sizeof(type.pointee, length)
        return self.builder.call(self.builtins['memcpy'], [dest, src, size])

    def unaryop(self, node, op, value):
        if op == '!':
            if not value.type.isNullable():
                self.throw(node, err.NotNullable(value.type))
        else:
            if op in {'+', '-'}:
                types = [t.Int, t.Float]
            elif op == '~':
                types = [t.Int]
            elif op == 'not':
                types = [t.Bool]

            if value.type not in types:
                self.throw(node, err.NoUnaryOperator(op, value.type))

        op = {
            'not': '!',
        }.get(op, op)

        return v.UnaryOperation(op, value, type=value.type)

    def binaryop(self, node, op, left, right):
        if op in {'^', '/'} or left.type != right.type and left.type in {t.Int, t.Float} and right.type in {t.Int, t.Float}:
            if left.type == t.Int:
                left = self.cast(node, left, t.Float)
            if right.type == t.Int:
                right = self.cast(node, right, t.Float)

        if op == '^':
            if left.type == right.type == t.Float:
                return v.Call('pow', left, right, type=t.Float)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '^^':
            if left.type == right.type == t.Int:
                return v.Call('pow', left, right, type=t.Int)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '*':
            if left.type == right.type and left.type in {t.Int, t.Float}:
                return v.BinaryOperation(left, op, right, type=left.type)

            elif left.type.isCollection() and right.type == t.Int:
                type = left.type
                subtype = type.subtype

                src = self.extract(left, 0)
                src_length = self.extract(left, 1)
                length = self.builder.mul(src_length, right)
                dest = self.malloc(t.Ptr(subtype), length)

                index = self.builder.alloca(t.Int)
                self.builder.store(v.Int(0), index)

                with self.block() as (label_start, label_end):
                    i = self.builder.load(index)
                    self.memcpy(self.builder.gep(dest, [i]), src, src_length)
                    self.builder.store(self.builder.add(i, src_length), index)

                    cond = self.builder.icmp_signed('<', self.builder.load(index), length)
                    self.builder.cbranch(cond, label_start, label_end)

                result = self.malloc(type)
                self.insert(dest, result, 0)
                self.insert(length, result, 1)
                return result

            elif left.type == t.Int and right.type.isCollection():
                return self.binaryop(node, op, right, left)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '/':
            if left.type == right.type == t.Float:
                return v.BinaryOperation(left, op, right, type=t.Float)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '//':
            if left.type == right.type == t.Int:
                return v.Call('floordiv', left, right, type=t.Int)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '%':
            if left.type == right.type == t.Int:
                return v.Call('mod', left, right, type=t.Int)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '+':
            if left.type == right.type and left.type in {t.Int, t.Float, t.String}:
                return v.BinaryOperation(left, op, right, type=left.type)

            elif left.type != right.type and left.type in {t.Char, t.String} and right.type in {t.Char, t.String}:
                return v.BinaryOperation(left, op, right, type=t.String)

            elif left.type == right.type and left.type.isCollection():
                type = left.type
                subtype = type.subtype

                length1 = self.extract(left, 1)
                length2 = self.extract(right, 1)
                length = self.builder.add(length1, length2)

                array1 = self.extract(left, 0)
                array2 = self.extract(right, 0)
                array = self.malloc(t.Ptr(subtype), length)

                self.memcpy(array, array1, length1)
                self.memcpy(self.builder.gep(array, [length1]), array2, length2)

                result = self.malloc(type)
                self.insert(array, result, 0)
                self.insert(length, result, 1)
                return result

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '-':
            if left.type == right.type and left.type in {t.Int, t.Float}:
                return v.BinaryOperation(left, op, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '|':
            if left.type == right.type == t.Int:
                return v.BinaryOperation(v.BinaryOperation(right, '%', left), '==', v.Int(0), type=t.Bool)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        else:
            if left.type == right.type == t.Int:
                op = {
                    '&&': '&',
                    '##': '^',
                    '||': '|',
                }.get(op, op)
                return v.BinaryOperation(left, op, right, type=t.Int)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

    def cmp(self, node, op, left, right):
        try:
            left, right = self.unify(node, left, right)
        except err:
            self.throw(node, err.NotComparable(left.type, right.type))

        return v.BinaryOperation(left, op, right, type=t.Bool)

        if left.type in {t.Int, t.Char}:
            return self.builder.icmp_signed(op, left, right)

        elif left.type == t.Float:
            return self.builder.fcmp_ordered(op, left, right)

        elif left.type == t.Bool:
            return self.builder.icmp_unsigned(op, left, right)

        elif left.type.isCollection():
            array1 = self.extract(left, 0)
            array2 = self.extract(right, 0)
            length1 = self.extract(left, 1)
            length2 = self.extract(right, 1)

            index = self.builder.alloca(t.Int)
            self.builder.store(v.Int(0), index)

            with self.block() as (label_start, label_end):
                label_true = ll.Block(self.builder.function)
                label_false = ll.Block(self.builder.function)
                label_cont = ll.Block(self.builder.function)
                label_length = ll.Block(self.builder.function)

                i = self.builder.load(index)

                for length in [length1, length2]:
                    label = ll.Block(self.builder.function)
                    self.builder.cbranch(self.builder.icmp_signed('<', i, length), label, label_length)
                    self.builder.function.blocks.append(label)
                    self.builder.position_at_end(label)

                values = [self.builder.load(self.builder.gep(array, [i])) for array in [array1, array2]]
                cond = self.cmp(node, op+'=' if op in {'<', '>'} else op, *values)

                if op == '!=':
                    self.builder.cbranch(cond, label_true, label_cont)
                else:
                    self.builder.cbranch(cond, label_cont, label_false)

                self.builder.function.blocks.append(label_cont)
                self.builder.position_at_end(label_cont)

                if op in {'<=', '>=', '<', '>'}:
                    label_cont = ll.Block(self.builder.function)

                    cond2 = self.cmp(node, '!=', *values)
                    self.builder.cbranch(cond2, label_true, label_cont)

                    self.builder.function.blocks.append(label_cont)
                    self.builder.position_at_end(label_cont)

                self.inc(index)

                self.builder.branch(label_start)

                for label in [label_true, label_false]:
                    self.builder.function.blocks.append(label)
                    self.builder.position_at_end(label)
                    self.builder.branch(label_end)

                self.builder.function.blocks.append(label_length)
                self.builder.position_at_end(label_length)

                length_cond = self.builder.icmp_signed(op, length1, length2)
                self.builder.branch(label_end)

            phi = self.builder.phi(t.Bool)
            phi.add_incoming(v.true, label_true)
            phi.add_incoming(v.false, label_false)
            phi.add_incoming(length_cond, label_length)
            return phi

        elif left.type.isClass():
            if op not in {'==', '!='}:
                self.throw(node, err.NotComparable(left.type, right.type))

            return self.builder.icmp_unsigned(op, left, right)

        elif left.type == t.Unknown:
            return v.true

        else:
            self.throw(node, err.NotComparable(left.type, right.type))

    def write(self, format, *values):
        args = ''.join(f', {value}' for value in values)
        self.output(f'printf("{format}"{args})')

    def print(self, node, value):
        type = value.type

        if type in {t.Int, t.Float, t.Bool, t.Char, t.String} or type.isTuple():
            self.output(v.Call('write', value))

        elif type.isArray():
            self.write('[')

            length = self.extract(value, 1)
            index = self.builder.alloca(t.Int)
            self.builder.store(v.Int(0), index)

            with self.block() as (label_start, label_end):
                i = self.builder.load(index)

                with self.builder.if_then(self.builder.icmp_signed('>=', i, length)):
                    self.builder.branch(label_end)

                with self.builder.if_then(self.builder.icmp_signed('>', i, v.Int(0))):
                    self.write(', ')

                elem = self.builder.gep(self.extract(value, 0), [i])
                self.print(node, self.builder.load(elem))

                self.inc(index)

                self.builder.branch(label_start)

            self.write(']')

        elif type.isNullable():
            with self.builder.if_else(self.builder.icmp_signed('!=', value, v.Null(type))) as (label_if, label_else):
                with label_if:
                    self.print(node, self.extract(value))
                with label_else:
                    self.write('null')

        elif type.isClass():
            try:
                method = self.attr(node, value, "toString")
            except err:
                method = None

            if not (method and method.type.isFunc() and len(method.type.args) == 1 and method.type.ret == t.String):
                self.throw(node, err.NotPrintable(type))

            self.print(node, self.builder.call(method, [value]))

        elif type != t.Unknown:
            self.throw(node, err.NotPrintable(type))

    def convert_string(self, node, lit):
        parts = re.split(r'{([^}]+)}', lit)

        if len(parts) == 1:
            return node

        lits, tags = parts[::2], parts[1::2]
        exprs = [None] * len(parts)

        for i, lit in enumerate(lits):
            exprs[i*2] = {
                'node': 'AtomString',
                'string': lit,
            }

        for i, tag in enumerate(tags):
            try:
                expr = parse_expr(tag)
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
                    'node': 'ExprArray',
                    'exprs': exprs,
                },
                'attr': 'join',
            },
            'args': [],
        }

    def array(self, subtype, values, length=None):
        type = t.Array(subtype)

        if length is None:
            length = v.Int(len(values))

        memory = self.malloc(t.Ptr(subtype), length)
        for i, value in enumerate(values):
            self.builder.store(value, self.builder.gep(memory, [v.Int(i)]))

        result = self.malloc(type)
        self.insert(memory, result, 0)
        self.insert(length, result, 1)
        return result

    def nullable(self, value):
        result = self.malloc(t.Nullable(value.type))
        self.insert(value, result)
        return result

    def convert_lambda(self, expr):
        ids = []

        def convert_expr(expr):
            if expr is None:
                return

            nonlocal ids
            node = expr['node']

            if node in {'ExprArray', 'ExprIndex', 'ExprBinaryOp', 'ExprRange', 'ExprIs', 'ExprCmp', 'ExprLogicalOp', 'ExprCond', 'ExprTuple'}:
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                }
            if node == 'ExprArrayComprehension':
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                    'comprehensions': lmap(convert_expr, expr['comprehensions']),
                }
            if node == 'ComprehensionGenerator':
                return {
                    **expr,
                    'iterables': lmap(convert_expr, expr['iterables']),
                    'steps': lmap(convert_expr, expr['steps']),
                }
            if node in {'ComprehensionFilter', 'ExprAttr', 'CallArg', 'ExprUnaryOp'}:
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
                    'args': lmap(convert_expr, expr['args']),
                }
            if node == 'AtomString':
                expr = self.convert_string(expr, expr['string'])
                if expr['node'] == 'AtomString':
                    return expr
                return convert_expr(expr)
            if node == 'AtomStub':
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

    def function(self, template):
        real_types = tuple(self.env.get(name) for name in template.typevars)

        if real_types in template.compiled:
            return template.compiled[real_types]

        id = template.id
        body = template.body

        if not body:  # `extern`
            func_ptr = ll.GlobalVariable(self.module, template.type, self.module.get_unique_name('f.'+id))
            template.compiled[real_types] = func_ptr

        else:
            unknown_ret_type_variables = {name: t.Var(name) for name in get_type_variables(template.type.ret) if not isinstance(self.env.get(name), t.Type)}

            # Try to resolve any unresolved type variables in the return type by fake-compiling the function.
            if unknown_ret_type_variables:
                for name in unknown_ret_type_variables:
                    self.env[name] = t.Var(name)

                func_type = self.resolve_type(template.type)

                with self.local():
                    with self.no_output():
                        self.env = template.env.copy()

                        self.env['#return'] = func_type.ret

                        for arg in func_type.args:
                            ptr = self.declare(body, arg.type, arg.name, redeclare=True, initialize=True)
                            self.env[arg.name] = ptr

                        self.compile(body)

                    ret = self.env['#return']

                # This is safe, since any type assignment errors have been found during the compilation.
                self.env.update(type_variables_assignment(ret, func_type.ret))

            real_types = tuple(self.env[name] for name in template.typevars)
            func_type = self.resolve_type(template.type)

            func = ll.Function(self.module, func_type.pointee, self.module.get_unique_name('def.'+id))

            func_ptr = ll.GlobalVariable(self.module, func_type, self.module.get_unique_name(id))
            func_ptr.initializer = func
            template.compiled[real_types] = func_ptr

            prev_label = self.builder.basic_block
            entry = func.append_basic_block('entry')
            self.builder.position_at_end(entry)

            with self.local(next_level=True):
                self.env = template.env.copy()

                for name, type in zip(template.typevars, real_types):
                    self.env[name] = type

                self.env['#return'] = func_type.ret
                self.env.pop('#continue', None)
                self.env.pop('#break', None)

                for arg, value in zip(func_type.args, func.args):
                    ptr = self.declare(body, arg.type, arg.name, redeclare=True, initialize=True)
                    self.env[arg.name] = ptr
                    self.builder.store(value, ptr)

                self.compile(body)

                if func_type.ret == t.Void:
                    self.builder.ret_void()
                else:
                    if '#return' not in self.initialized:
                        self.throw(body, err.MissingReturn())
                    self.builder.ret(func_type.ret.default())

            self.builder.position_at_end(prev_label)

        return func_ptr


    ### Statements ###

    def compileBlock(self, node):
        for stmt in node['stmts']:
            self.compile(stmt)

    def compileStmtUse(self, node):
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
                if id in unit.initialized:
                    self.initialized.add(id)
        elif kind == 'hiding':
            hidden = set()
            for id in ids:
                if id not in unit.env:
                    self.throw(node, err.UndeclaredIdentifier(id))
                hidden.add(id)
            self.env.update({x: unit.env[x] for x in unit.env.keys() - hidden})
            self.initialized.update(unit.initialized - hidden)
        elif kind == 'as':
            self.units[ids[0]] = unit
        else:
            self.env.update(unit.env)
            self.initialized.update(unit.initialized)

    def compileStmtSkip(self, node):
        pass

    def compileStmtPrint(self, node):
        expr = node['expr']
        if expr:
            value = self.compile(expr)
            self.print(expr, value)
        self.write('\\n')

    def compileStmtDecl(self, node):
        type = self.resolve_type(self.compile(node['type']))
        id = node['id']
        expr = node['expr']
        var = self.declare(node, type, id, initialize=bool(expr))

        if expr:
            value = self.cast(node, self.compile(expr), type)
            self.store(var, value)

    def compileStmtAssg(self, node):
        value = self.compile(node['expr'])

        for lvalue in node['lvalues']:
            self.assign(lvalue, lvalue, value)

    def compileStmtAssgExpr(self, node):
        exprs = node['exprs']
        op = node['op']
        left = self.lvalue(node, exprs[0])

        if op == '??':
            with self.builder.if_then(self.builder.icmp_unsigned('==', left, v.Null())):
                right = self.compile(exprs[1])
                if not left.type.isNullable() or not can_cast(right.type, left.type.subtype):
                    self.throw(node, err.NoBinaryOperator(op, left.type, right.type))
                self.builder.store(self.nullable(self.cast(node, right, left.type.subtype)), ptr)
        else:
            right = self.compile(exprs[1])
            value = self.binaryop(node, op, left, right)
            if value.type != left.type:
                self.throw(node, err.IllegalAssignment(value.type, left.type))
            self.store(left, value)

    def compileStmtAppend(self, node):
        # Special instruction for array comprehension.
        array = self.compile(node['array'])
        length = self.extract(array, 1)
        index = self.compile(node['index'])

        with self.builder.if_then(self.builder.icmp_signed('==', index, length)):
            length = self.builder.shl(length, v.Int(1))
            memory = self.realloc(self.extract(array, 0), length)
            self.insert(memory, array, 0)
            self.insert(length, array, 1)

        value = self.compile(node['expr'])
        self.builder.store(value, self.builder.gep(self.extract(array, 0), [index]))

        self.inc(self.lvalue(node, node['index']))

    def compileStmtIf(self, node):
        exprs = node['exprs']
        blocks = node['blocks']

        initialized_vars = []
        else_ = None

        for expr, block in reversed(list(zip_longest(exprs, blocks))):
            if expr:
                cond = self.cast(expr, self.compile(expr), t.Bool)

            then_ = c.Block()
            with self.block(then_):
                with self.local():
                    self.compile(block)
                    initialized_vars.append(self.initialized)

            if expr:
                else_ = c.If(cond, then_, else_)
            else:
                else_ = then_

        self.output(else_)

        if len(blocks) > len(exprs):  # there is an `else` statement
            self.initialized.update(set.intersection(*initialized_vars))

    def compileStmtWhile(self, node):
        with self.block() as (label_start, label_end):
            expr = node['expr']
            cond = self.cast(expr, self.compile(expr), t.Bool)

            label_while = self.builder.append_basic_block()
            self.builder.cbranch(cond, label_while, label_end)
            self.builder.position_at_end(label_while)

            with self.local():
                self.env['#continue'] = label_start
                self.env['#break'] = label_end

                self.compile(node['block'])

            self.builder.branch(label_start)

    def compileStmtUntil(self, node):
        with self.block() as (label_start, label_end):
            with self.local():
                self.env['#continue'] = label_start
                self.env['#break'] = label_end

                self.compile(node['block'])

            expr = node['expr']
            cond = self.cast(expr, self.compile(expr), t.Bool)

            self.builder.cbranch(cond, label_end, label_start)

    def compileStmtFor(self, node):
        vars = node['vars']
        iterables = node['iterables']

        types = []
        steps = []
        indices = []
        conditions = []
        getters = []

        def prepare(iterable, step):
            # It must be a function so that lambdas have separate scopes.
            if iterable['node'] == 'ExprRange':
                values = lmap(self.compile, iterable['exprs'])
                type = values[0].type
                types.append(type)
                if type not in {t.Int, t.Float, t.Bool, t.Char}:
                    self.throw(iterable, err.UnknownType())
                if len(values) > 1:
                    values[1] = self.cast(iterable, values[1], type)
                if type == t.Float:
                    if step.type not in {t.Float, t.Int}:
                        self.throw(node, err.IllegalAssignment(step.type, t.Float))
                    if step.type == t.Int:
                        step = self.builder.sitofp(step, type)
                    cmp = self.builder.fcmp_ordered
                    desc = cmp('<', step, v.Float(0))
                else:
                    if step.type != t.Int:
                        self.throw(node, err.IllegalAssignment(step.type, t.Int))
                    values = [self.builder.zext(v, t.Int) for v in values]
                    cmp = self.builder.icmp_signed
                    desc = cmp('<', step, v.Int(0))
                index = self.builder.alloca(type if type == t.Float else t.Int)
                start = values[0]
                if len(values) == 1:
                    cond = lambda v: v.true
                elif iterable['inclusive']:
                    cond = lambda v: self.builder.select(desc, cmp('>=', v, values[1]), cmp('<=', v, values[1]))
                else:
                    cond = lambda v: self.builder.select(desc, cmp('>', v, values[1]), cmp('<', v, values[1]))
                getter = lambda v: v if type in {t.Int, t.Float} else self.builder.trunc(v, type)
            else:
                value = self.compile(iterable)
                if value.type == t.String:
                    types.append(t.Char)
                elif value.type.isArray():
                    types.append(value.type.subtype)
                else:
                    self.throw(node, err.NotIterable(value.type))
                desc = self.builder.icmp_signed('<', step, v.Int(0))
                index = self.builder.alloca(t.Int)
                array = self.extract(value, 0)
                length = self.extract(value, 1)
                end1 = self.builder.sub(length, v.Int(1))
                end2 = v.Int(0)
                start = self.builder.select(desc, end1, end2)
                cond = lambda v: self.builder.select(desc, self.builder.icmp_signed('>=', v, end2), self.builder.icmp_signed('<=', v, end1))
                getter = lambda v: self.builder.load(self.builder.gep(array, [v]))

            self.builder.store(start, index)
            steps.append(step)
            indices.append(index)
            conditions.append(cond)
            getters.append(getter)

        _steps = lmap(self.compile, node.get('steps', [])) or [v.Int(1)]
        if len(_steps) == 1:
            _steps *= len(iterables)
        elif len(_steps) != len(iterables):
            self.throw(node, err.InvalidLoopStep())

        for iterable, step in zip(iterables, _steps):
            prepare(iterable, step)

        with self.block() as (label_start, label_end):
            label_cont = ll.Block(self.builder.function)

            for index, cond in zip(indices, conditions):
                label = ll.Block(self.builder.function)
                self.builder.cbranch(cond(self.builder.load(index)), label, label_end)
                self.builder.function.blocks.append(label)
                self.builder.position_at_end(label)

            with self.local():
                self.env['#continue'] = label_cont
                self.env['#break'] = label_end

                if len(vars) == 1 and len(types) > 1:
                    tuple = self.tuple([getters[i](self.builder.load(index)) for i, index in enumerate(indices)])
                    self.assign(node, vars[0], tuple)
                elif len(vars) > 1 and len(types) == 1:
                    for i, var in enumerate(vars):
                        tuple = getters[0](self.builder.load(indices[0]))
                        self.assign(node, var, self.extract(tuple, i))
                elif len(vars) == len(types):
                    for var, index, getter in zip(vars, indices, getters):
                        self.assign(node, var, getter(self.builder.load(index)))
                else:
                    self.throw(node, err.CannotUnpack(t.Tuple(types), len(vars)))

                self.compile(node['block'])

            self.builder.function.blocks.append(label_cont)
            self.builder.branch(label_cont)
            self.builder.position_at_end(label_cont)

            for index, step, type in zip(indices, steps, types):
                self.inc(index, step)

            self.builder.branch(label_start)

    def compileStmtLoopControl(self, node):
        stmt = node['stmt']  # `break` / `continue`

        try:
            label = self.env[f'#{stmt}']
        except KeyError:
            self.throw(node, err.UnexpectedStatement(stmt))

        self.builder.branch(label)

    def compileStmtFunc(self, node, class_type=None):
        id = node['id']

        if class_type is None:
            self.initialized.add(id)

        with self.local():
            typevars = node.get('typevars', [])
            for name in typevars:
                self.env[name] = t.Var(name)

            args = [] if class_type is None else [Arg(class_type, 'self')]
            expect_default = False
            for arg in node['args']:
                type = self.compile(arg['type'])
                self.declare(arg, type, "", check_only=True)
                name = arg['name']
                default = arg.get('default')
                if default:
                    expect_default = True
                elif expect_default:
                    self.throw(arg, err.MissingDefault(name))
                args.append(Arg(type, name, default))

            ret_type = self.compile(node.get('ret')) or t.Void
            func_type = t.Func(args, ret_type)

            env = self.env.copy()
            func = FunctionTemplate(id, typevars, func_type, node['block'], env)

        if class_type is None:
            self.env[id] = env[id] = func
            self.levels[id] = self.level

        return func

    def compileStmtReturn(self, node):
        try:
            type = self.env['#return']
        except KeyError:
            self.throw(node, err.UnexpectedStatement('return'))

        self.initialized.add('#return')

        expr = node['expr']
        if expr:
            value = self.compile(expr)

            # Update unresolved type variables in the return type.
            d = type_variables_assignment(value.type, type)
            if d is None:
                self.throw(node, err.IllegalAssignment(value.type, type))
            if d:
                self.env.update(d)
                type = self.env['#return'] = self.resolve_type(type)

            value = self.cast(node, value, type)

        elif type != t.Void:
            self.throw(node, err.IllegalAssignment(t.Void, type))

        if type == t.Void:
            self.builder.ret_void()
        else:
            self.builder.ret(value)

    def compileStmtClass(self, node):
        id = node['id']
        if id in self.env:
            self.throw(node, err.RedeclaredIdentifier(id))
        self.initialized.add(id)

        base = self.compile(node['base'])
        if base and not base.isClass():
            self.throw(node, err.NotClass(base))

        declared_members = set()
        for member in node['members']:
            name = member['id']
            if name in declared_members:
                self.throw(member, err.RepeatedMember(name))
            declared_members.add(name)

        members = base.members.copy() if base else {}
        for member in node['members']:
            members[member['id']] = member

        type = t.Class(self.module.context, id, base, members)
        self.env[id] = type

        member_types = {}
        methods = {}

        for name, member in members.items():
            if member['node'] == 'ClassField':
                member_types[name] = self.compile(member['type'])
            elif member['node'] in {'ClassMethod', 'ClassConstructor'}:
                if member['block']:
                    with self.local():
                        if base:
                            self.env['#super'] = base.methods.get(name)
                        func = self.compileStmtFunc(member, class_type=type)
                    member_types[name] = func.type
                    methods[name] = func
                else:
                    methods[name] = None

            if base:
                original_field = base.members.get(name)
                if original_field and original_field['node'] == 'ClassField':
                    original_type = self.compile(original_field['type'])
                    new_type = member_types[name]
                    if not can_cast(new_type, original_type):
                        self.throw(member, err.IllegalOverride(original_type, new_type))

        type.methods = methods
        type.pointee.set_body(*member_types.values())

        if None in methods.values():  # abstract class
            return

        constructor_method = methods.get('<constructor>')
        constructor_type = t.Func(constructor_method.type.args[1:] if constructor_method else [], type)
        constructor = ll.Function(self.module, constructor_type.pointee, self.module.get_unique_name('def.'+id))

        constructor_ptr = ll.GlobalVariable(self.module, constructor_type, self.module.get_unique_name(id))
        constructor_ptr.initializer = constructor
        type.constructor = constructor_ptr

        prev_label = self.builder.basic_block
        entry = constructor.append_basic_block('entry')
        self.builder.position_at_end(entry)

        obj = self.malloc(type)

        for i, (name, member) in enumerate(members.items()):
            if member['node'] == 'ClassField':
                default = member.get('default')
                if default:
                    value = self.cast(member, self.compile(default), member_types[name])
                    self.insert(value, obj, i)
            elif member['node'] == 'ClassMethod':
                self.insert(self.builder.load(self.function(methods[name])), obj, i)

        if constructor_method:
            self.builder.call(self.builder.load(self.function(constructor_method)), [obj, *constructor.args])

        self.builder.ret(obj)

        self.builder.position_at_end(prev_label)


    ### Expressions ###

    def compileExprArray(self, node):
        exprs = node['exprs']

        if len(exprs) == 1 and exprs[0]['node'] == 'ExprRange':
            var = {
                'node': 'AtomId',
                'id': f'__range_{len(self.env)}',
            }
            return self.compile({
                'node': 'ExprArrayComprehension',
                'expr': var,
                'comprehensions': [{
                    'node': 'ComprehensionGenerator',
                    'vars': [var],
                    'iterables': [exprs[0]],
                    'steps': [node['step']] if node.get('step') else [],
                }],
            })
        elif node.get('step'):
            self.throw(node, err.InvalidSyntax())

        values = self.unify(node, *map(self.compile, exprs))
        subtype = values[0].type if values else t.Unknown
        return self.array(subtype, values)

    def compileExprArrayComprehension(self, node):
        expr = node['expr']

        value, array, index = [{
            'node': 'AtomId',
            'id': f'__cpr_{len(self.env)}_{name}',
        } for name in ['value', 'array', 'index']]

        stmt = inner_stmt = {
            'node': 'StmtAssg',
            'lvalues': [value],
            'expr': expr,
        }

        for i, cpr in reversed(list(enumerate(node['comprehensions']))):
            if cpr['node'] == 'ComprehensionGenerator':
                stmt = {
                    **cpr,
                    'node': 'StmtFor',
                    'vars': [{**var, 'override': True} for var in cpr['vars']],
                    'block': stmt,
                }
            elif cpr['node'] == 'ComprehensionFilter':
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
                inner_stmt['_eval'] = lambda: self.compile(value).type
                self.compile(stmt)
                type = inner_stmt.pop('_eval')

        with self.local():
            self.assign(node, array, self.array(type, [], length=v.Int(4)))
            self.assign(node, index, v.Int(0))

            inner_stmt['node'] = 'StmtAppend'
            inner_stmt['array'] = array
            inner_stmt['index'] = index

            self.compile(stmt)

            result = self.compile(array)
            length = self.compile(index)
            self.insert(length, result, 1)

        return result

    def compileExprAttr(self, node):
        expr = node['expr']
        attr = node['attr']

        if node.get('safe'):
            obj = self.compile(expr)
            return self.safe(node, obj, lambda: self.nullable(self.attr(node, self.extract(obj), attr)), v.Null)

        obj, value = self.attribute(node, expr, attr)
        return value

    def compileExprIndex(self, node):
        exprs = node['exprs']

        if node.get('safe'):
            collection = self.compile(exprs[0])
            return self.safe(node, collection, lambda: self.nullable(self.index(node, self.extract(collection), self.compile(exprs[1]))), v.Null)

        return self.index(node, *map(self.compile, exprs))

    def compileExprSlice(self, node):
        slice = node['slice']

        array, length, start, end, step, index = [{
            'node': 'AtomId',
            'id': f'__slice_{len(self.env)}_{name}',
        } for name in ['array', 'length', 'start', 'end', 'step', 'index']]

        with self.local():
            collection = self.compile(node['expr'])
            type = collection.type

            if not type.isCollection():
                self.throw(node, err.NotIndexable(type))

            self.assign(node, array, collection)
            self.assign(node, length, self.expr('{t}.length', t=array['id']))

            if slice[2] is None:
                self.assign(node, step, v.Int(1))
            else:
                self.assign(node, step, self.cast(slice[2], self.compile(slice[2]), t.Int))

            if slice[0] is None:
                self.assign(node, start, self.expr('{c} > 0 ? 0 : {l}', c=step['id'], l=length['id']))
            else:
                self.assign(node, start, self.cast(slice[0], self.compile(slice[0]), t.Int))
                self.assign(node, start, self.expr('{a} < 0 ? {a} + {l} : {a}', a=start['id'], l=length['id']))
            self.assign(node, start, self.expr('{a} < 0 ? 0 : {a} > {l} ? {l} : {a}', a=start['id'], l=length['id']))

            if slice[1] is None:
                self.assign(node, end, self.expr('{c} > 0 ? {l} : 0', c=step['id'], l=length['id']))
            else:
                self.assign(node, end, self.cast(slice[1], self.compile(slice[1]), t.Int))
                self.assign(node, end, self.expr('{b} < 0 ? {b} + {l} : {b}', b=end['id'], l=length['id']))
            self.assign(node, end, self.expr('{b} < 0 ? 0 : {b} > {l} ? {l} : {b}', b=end['id'], l=length['id']))

            self.assign(node, start, self.expr('{c} < 0 ? {a} - 1 : {a}', a=start['id'], c=step['id']))
            self.assign(node, end, self.expr('{c} < 0 ? {b} - 1 : {b}', b=end['id'], c=step['id']))

            result = self.expr('[{t}[{i}] for {i} in {a}...{b} step {c}]', t=array['id'], a=start['id'], b=end['id'], c=step['id'], i=index['id'])

        # `CharArray_asString` is used directly, because `.join` would copy the array redundantly.
        return self.builder.call(self.get(node, 'CharArray_asString'), [result]) if type == t.String else result

    def compileExprCall(self, node):
        expr = node['expr']

        def _call(obj, func):
            if not func.type.isFunc():
                self.throw(node, err.NotFunction(func.type))

            func_args = func.type.args[1:] if obj else func.type.args
            func_named_args = {func_arg.name for func_arg in func_args}

            args = []
            pos_args = {}
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
                    pos_args[i] = expr

            with self.local():
                type_variables = defaultdict(list)

                for i, func_arg in enumerate(func_args):
                    name = func_arg.name
                    if name in named_args:
                        if i in pos_args:
                            self.throw(node, err.RepeatedArgument(name))
                        expr = named_args.pop(name)
                    elif i in pos_args:
                        expr = pos_args.pop(i)
                    elif func_arg.default:
                        expr = func_arg.default
                    else:
                        self.throw(node, err.TooFewArguments(func.type))

                    expr = self.convert_lambda(expr)
                    if expr['node'] == 'ExprLambda':
                        ids = expr['ids']
                        type = func_arg.type

                        if not type.isFunc():
                            self.throw(node, err.IllegalLambda())

                        if len(ids) < len(type.args):
                            self.throw(node, err.TooFewArguments(type))
                        if len(ids) > len(type.args):
                            self.throw(node, err.TooManyArguments(type))

                        id = f'__lambda_{len(self.env)}'
                        self.compile({
                            **expr,
                            'node': 'StmtFunc',
                            'id': id,
                            'args': [{
                                'type': arg.type,
                                'name': name,
                            } for arg, name in zip(type.args, ids)],
                            'ret': type.ret,
                            'block': {
                                **expr,
                                'node': 'StmtReturn',
                                'expr': expr['expr'],
                            },
                        })
                        expr = {
                            'node': 'AtomId',
                            'id': id,
                        }
                        args.append(expr)

                    else:
                        value = self.compile(expr)

                        if value.isTemplate():
                            if not func_arg.type.isFunc():
                                self.throw(node, err.IllegalAssignment(value.type, func_arg.type))

                            if len(value.type.args) < len(func_arg.type.args):
                                self.throw(node, err.TooFewArguments(func_arg.type))
                            if len(value.type.args) > len(func_arg.type.args):
                                self.throw(node, err.TooManyArguments(func_arg.type))

                            id = f'__lambda_generic_{len(self.env)}'
                            self.compile({
                                **expr,
                                'node': 'StmtFunc',
                                'id': id,
                                'args': [{
                                    'type': arg1.type,
                                    'name': arg2.name,
                                } for arg1, arg2 in zip(func_arg.type.args, value.type.args)],
                                'ret': func_arg.type.ret,
                                'block': value.body,
                            })
                            expr = {
                                'node': 'AtomId',
                                'id': id,
                            }
                            args.append(expr)

                        else:
                            d = type_variables_assignment(value.type, func_arg.type)
                            if d is None:
                                self.throw(node, err.IllegalAssignment(value.type, func_arg.type))

                            for name, type in d.items():
                                type_variables[name].append(type)

                            args.append(value)

                if obj:
                    for name, type in type_variables_assignment(obj.type, func.type.args[0].type).items():
                        type_variables[name].append(type)

                assigned_types = {}

                for name, types in type_variables.items():
                    type = unify_types(*types)
                    if type is None:
                        self.throw(node, err.InvalidArgumentTypes(t.Var(name)))

                    self.env[name] = assigned_types[name] = type

                if pos_args:
                    self.throw(node, err.TooManyArguments(func.type))

                try:
                    args = [self.cast(node, self.compile(arg), self.resolve_type(func_arg.type)) for arg, func_arg in zip(args, func_args)]
                except KeyError:
                    # Not all type variables have been resolved.
                    self.throw(node, err.UnknownType())
                except err as e:
                    if not func.isTemplate():
                        raise
                    self.throw(node, err.InvalidFunctionCall(func.id, assigned_types, str(e)[:-1]))

                if obj:
                    args.insert(0, obj)

                if func.isTemplate():
                    try:
                        func = self.builder.load(self.function(func))
                    except err as e:
                        self.throw(node, err.InvalidFunctionCall(func.id, assigned_types, str(e)[:-1]))

            return self.builder.call(func, args)

        if expr['node'] == 'ExprAttr':
            attr = expr['attr']

            if expr.get('safe'):
                obj = self.compile(expr['expr'])

                def callback():
                    value = self.extract(obj)
                    func = self.attr(node, value, attr)
                    return self.nullable(_call(value, func))

                return self.safe(node, obj, callback, v.Null)
            else:
                obj, func = self.attribute(expr, expr['expr'], attr)

        else:
            func = self.compile(expr)

            if expr['node'] == 'AtomSuper':
                obj = self.builder.bitcast(self.get(expr, 'self'), func.type.args[0].type)
            else:
                obj = None

        return _call(obj, func)

    def compileExprUnaryOp(self, node):
        return self.unaryop(node, node['op'], self.compile(node['expr']))

    def compileExprBinaryOp(self, node):
        op = node['op']
        exprs = node['exprs']

        if op == '??':
            left = self.compile(exprs[0])
            try:
                return self.safe(node, left, lambda: self.extract(left), lambda: self.compile(exprs[1]))
            except err:
                self.throw(node, err.NoBinaryOperator(op, left.type, self.compile(exprs[1]).type))

        return self.binaryop(node, op, *map(self.compile, exprs))

    def compileExprRange(self, node):
        self.throw(node, err.IllegalRange())

    def compileExprIs(self, node):
        left, right = map(self.compile, node['exprs'])
        if not left.type.isNullable() or not right.type.isNullable() or unify_types(left.type, right.type) is None:
            self.throw(node, err.NoStrictComparison(left.type, right.type))

        left, right = self.unify(node, left, right)
        return self.builder.icmp_unsigned('!=' if node.get('not') else '==', left, right)

    def compileExprCmp(self, node):
        exprs = node['exprs']
        ops = node['ops']

        return self.cmp(node, ops[0], *map(self.compile, exprs))

        with self.block() as (label_start, label_end):
            self.builder.position_at_end(label_end)
            phi = self.builder.phi(t.Bool)
            self.builder.position_at_end(label_start)

            def emitIf(index):
                values.append(self.compile(exprs[index+1]))
                cond = self.cmp(node, ops[index], values[index], values[index+1])

                if len(exprs) == index+2:
                    phi.add_incoming(cond, self.builder.basic_block)
                    self.builder.branch(label_end)
                    return

                phi.add_incoming(v.false, self.builder.basic_block)
                label_if = self.builder.function.append_basic_block()
                self.builder.cbranch(cond, label_if, label_end)

                with self.builder._branch_helper(label_if, label_end):
                    emitIf(index+1)

            emitIf(0)

        return phi

    def compileExprLogicalOp(self, node):
        exprs = node['exprs']
        op = {
            'and': '&&',
            'or': '||',
        }[node['op']]

        values = lmap(self.compile, exprs)
        return v.BinaryOperation(values[0], op, values[1], type=t.Bool)

        cond1 = self.compile(exprs[0])

        with self.block() as (label_start, label_end):
            label_if = self.builder.function.append_basic_block()

            if op == 'and':
                self.builder.cbranch(cond1, label_if, label_end)
            elif op == 'or':
                self.builder.cbranch(cond1, label_end, label_if)

            self.builder.position_at_end(label_end)
            phi = self.builder.phi(t.Bool)
            if op == 'and':
                phi.add_incoming(v.false, label_start)
            elif op == 'or':
                phi.add_incoming(v.true, label_start)

            with self.builder._branch_helper(label_if, label_end):
                cond2 = self.compile(exprs[1])
                if not cond1.type == cond2.type == t.Bool:
                    self.throw(node, err.NoBinaryOperator(op, cond1.type, cond2.type))
                phi.add_incoming(cond2, self.builder.basic_block)

        return phi

    def compileExprCond(self, node):
        exprs = node['exprs']
        cond, *values = map(self.compile, exprs)
        cond = self.cast(exprs[0], cond, t.Bool)
        values = self.unify(node, *values)
        return v.TernaryOperation(cond, '?', values[0], ':', values[1], type=values[0].type)

    def compileExprLambda(self, node):
        self.throw(node, err.IllegalLambda())

    def compileExprTuple(self, node):
        elements = lmap(self.compile, node['exprs'])
        return v.Tuple(elements)


    ### Atoms ###

    def compileAtomInt(self, node):
        return v.Int(node['int'])

    def compileAtomFloat(self, node):
        return v.Float(node['float'])

    def compileAtomBool(self, node):
        return v.Bool(node['bool'])

    def compileAtomChar(self, node):
        return v.Char(node['char'])

    def compileAtomString(self, node):
        return v.String(node['string'])

        expr = self.convert_string(node, node['string'])
        if expr['node'] == 'AtomString':
            return self.string(expr['string'])
        try:
            return self.compile(expr)
        except err as e:
            self.throw({
                **node,
                'position': [e.line+node['position'][0]-1, e.column+node['position'][1]+1],
            }, str(e).partition(': ')[2][:-1])

    def compileAtomNull(self, node):
        return v.Null()

    def compileAtomSuper(self, node):
        func = self.env.get('#super')
        if func is None:
            self.throw(node, err.IllegalSuper())
        return self.builder.load(self.function(func))

    def compileAtomId(self, node):
        return self.get(node, node['id'])

    def compileAtomStub(self, node):
        self.throw(node, err.IllegalLambda())


    ### Types ###

    def compileTypeName(self, node):
        name = node['name']

        type = {
            'Void': t.Void,
            'Int': t.Int,
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

    def compileTypeArray(self, node):
        return t.Array(self.compile(node['subtype']))

    def compileTypeNullable(self, node):
        return t.Nullable(self.compile(node['subtype']))

    def compileTypeTuple(self, node):
        return t.Tuple(lmap(self.compile, node['elements']))

    def compileTypeFunc(self, node):
        return t.Func(lmap(self.compile, node['args']), self.compile(node['ret']) or t.Void)
