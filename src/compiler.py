
import ast
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
from .utils import lmap, lzip


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
        self._var_index = 0

        self._block = c.Block()
        self.main = c.FunctionBody(c.FunctionDeclaration(c.Value('int', 'main'), []), self._block)

        self.module_declarations = c.Collection()
        self.module_definitions = c.Collection()
        
        self.module = c.Module([
            c.Line(),
            self.module_declarations,
            c.Line(),
            self.module_definitions,
            c.Line(),
            self.main,
            c.Line(),
        ])

    def run(self, ast, unit):
        self.units[unit] = Unit()
        with self.unit(unit):
            if unit != 'std':
                self.env = self.units['std'].env.copy()
                self.initialized = self.units['std'].initialized.copy()
                self.levels = self.units['std'].levels.copy()
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

    def output(self, stmt, toplevel=False):
        if isinstance(stmt, (str, v.Value)):
            stmt = c.Statement(str(stmt))

        if toplevel:
            if isinstance(stmt, (c.FunctionBody, c.Struct)):
                self.module_definitions.append(stmt)
            else:
                self.module_declarations.append(stmt)
        else:
            self._block.append(stmt)

    def resolve_type(self, type):
        if type.isVar():
            return self.env[type.name]
        if type.isArray():
            return t.Array(self.resolve_type(type.subtype))
        if type.isSet():
            return t.Set(self.resolve_type(type.subtype))
        if type.isDict():
            return t.Dict(self.resolve_type(type.key_type), self.resolve_type(type.value_type))
        if type.isNullable():
            return t.Nullable(self.resolve_type(type.subtype))
        if type.isTuple():
            return t.Tuple([self.resolve_type(type) for type in type.elements])
        if type.isFunc():
            return t.Func([t.Func.Arg(self.resolve_type(arg.type), arg.name, arg.default) for arg in type.args], self.resolve_type(type.ret))
        return type


    ### Code generation ###

    def get(self, node, id):
        if id not in self.env:
            self.throw(node, err.UndeclaredIdentifier(id))

        if id in self.levels and self.levels[id] != 0 and self.levels[id] < self.level:
            self.throw(node, err.ClosureRequired(id))

        result = self.env[id]

        if isinstance(result, t.Class):
            if None in result.methods.values():
                self.throw(node, err.AbstractClass(result))
            return result

        if not isinstance(result, v.Value):
            self.throw(node, err.NotVariable(id))

        if id not in self.initialized:
            self.throw(node, err.UninitializedIdentifier(id))

        if result.isTemplate() and not result.typevars:
            result = self.function(result)

        return result

    def index(self, node, collection, index, lvalue=False):
        if collection.type.isSequence() or collection.type.isDict():
            if lvalue and collection.type == t.String:
                self.throw(node, err.NotLvalue())

            collection = self.tmp(collection)

            if collection.type.isSequence():
                index = self.tmp(self.cast(node, index, t.Int))
                index = v.Condition(
                    v.BinaryOperation(index, '<', v.Int(0)),
                    v.BinaryOperation(self.attr(node, collection, 'length'), '+', index),
                    index)
                type = collection.type.subtype

            elif collection.type.isDict():
                index = self.cast(node, index, collection.type.key_type)
                type = collection.type.value_type

            return v.Index(collection, index, type=type)

        self.throw(node, err.NotIndexable(collection.type))

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
        self.output(f'{type} {result.name}')

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

    def attribute(self, node, expr, attr):
        if expr['node'] == 'AtomId':
            id = expr['id']
            if id in self.units:
                with self.unit(id):
                    return None, self.get(node, attr)

        obj = self.tmp(self.compile(expr))
        return obj, self.attr(node, obj, attr)

    def attr(self, node, obj, attr):
        type = obj.type
        value = None

        if attr == 'toString' and type.isPrintable():
            value = v.Variable(t.Func([type], t.String), 'toString')

        elif attr == 'toInt' and type in {t.Int, t.Float, t.Bool, t.Char, t.String}:
            value = v.Variable(t.Func([type], t.Int), 'toInt')

        elif attr == 'toFloat' and type in {t.Int, t.Float, t.Bool, t.Char, t.String}:
            value = v.Variable(t.Func([type], t.Float), 'toFloat')

        elif type == t.Int:
            if attr == 'char':
                value = v.Cast(obj, t.Char)

        elif type == t.Char:
            if attr == 'code':
                value = v.Cast(obj, t.Int)

        elif type.isCollection():
            if attr == 'length':
                value = v.Cast(v.Call(v.Attribute(obj, 'size')), t.Int)
            elif attr == 'join' and type.subtype in {t.Char, t.String}:
                value = v.Variable(t.Func([type, t.Func.Arg(t.String, default={'node': 'AtomString', 'string': ''})], t.String), attr)
            elif attr == '_asString' and type.subtype == t.Char:
                value = v.Variable(t.Func([type], t.String), 'asString')

            elif type == t.String:
                if attr == 'all':
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
                if attr == 'all':
                    value = self.env['Array_all']
                elif attr == 'any':
                    value = self.env['Array_any']
                elif attr == 'filter':
                    value = self.env['Array_filter']
                elif attr == 'map':
                    value = self.env['Array_map']
                elif attr == 'reduce':
                    value = self.env['Array_reduce']
                elif attr == 'push':
                    value = v.Variable(t.Func([type, type.subtype]), attr)
                elif attr == 'insert':
                    value = v.Variable(t.Func([type, t.Int, type.subtype]), attr)
                elif attr == 'extend':
                    value = v.Variable(t.Func([type, type]), attr)
                elif attr == 'pop':
                    value = v.Variable(t.Func([type], type.subtype), attr)
                elif attr == 'erase':
                    value = v.Variable(t.Func([type, t.Int, t.Func.Arg(t.Int, default={'node': 'AtomInt', 'int': 1})]), attr)
                elif attr == 'clear':
                    value = v.Variable(t.Func([type]), attr)
                elif attr == 'reverse':
                    value = v.Variable(t.Func([type]), attr)
                elif attr == 'copy':
                    value = v.Variable(t.Func([type], type), attr)
                elif attr == 'find':
                    value = v.Variable(t.Func([type, type.subtype], t.Nullable(t.Int)), attr)
                elif attr == 'count':
                    value = v.Variable(t.Func([type, type.subtype], t.Int), attr)

            elif type.isSet():
                if attr == 'all':
                    value = self.env['Set_all']
                elif attr == 'any':
                    value = self.env['Set_any']
                elif attr == 'filter':
                    value = self.env['Set_filter']
                elif attr == 'map':
                    value = self.env['Set_map']
                elif attr == 'reduce':
                    value = self.env['Set_reduce']
                elif attr == 'add':
                    value = v.Variable(t.Func([type, type.subtype]), attr)
                elif attr == 'union':
                    value = v.Variable(t.Func([type, type]), 'union_')
                elif attr == 'subtract':
                    value = v.Variable(t.Func([type, type]), attr)
                elif attr == 'intersect':
                    value = v.Variable(t.Func([type, type]), attr)
                elif attr == 'pop':
                    value = v.Variable(t.Func([type], type.subtype), attr)
                elif attr == 'remove':
                    value = v.Variable(t.Func([type, type.subtype]), attr)
                elif attr == 'clear':
                    value = v.Variable(t.Func([type]), attr)
                elif attr == 'copy':
                    value = v.Variable(t.Func([type], type), attr)
                elif attr == 'contains':
                    value = v.Variable(t.Func([type, type.subtype], t.Bool), attr)

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
        if attr not in obj.type.members:
            self.throw(node, err.NoAttribute(obj.type, attr))
        if lvalue and attr in obj.type.methods:
            self.throw(node, err.NotLvalue())

        value = v.Attribute(obj, obj.type.members[attr].name, type=obj.type.members[attr].type)
        if attr in obj.type.methods:
            value = v.Call(f'reinterpret_cast<{value.type.ret} (*)({value.type.args_str()})>', v.Call(value), type=value.type)
        return value

    def cast(self, node, value, type):
        if not can_cast(value.type, type):
            self.throw(node, err.IllegalAssignment(value.type, type))

        if not value.type.isNullable() and type.isNullable():
            return v.Nullable(v.Cast(value, type.subtype))
        return v.Cast(value, type)

    def unify(self, node, *values):
        if not values:
            return []

        type = unify_types(*[value.type for value in values])
        if type is None:
            self.throw(node, err.UnknownType())

        return [self.cast(node, value, type) for value in values]

    def var(self, type, prefix='v'):
        var = v.Variable(type, f'{prefix}{self._var_index}')
        self._var_index += 1
        return var

    def tmp(self, value):
        if isinstance(value, v.Variable) or isinstance(value, v.Literal) and value.type in {t.Int, t.Float, t.Bool, t.Char}:
            return value
        tmp = self.var(value.type)
        self.store(tmp, value, decl='auto&&')
        return tmp

    def freeze(self, value):
        tmp = self.var(value.type)
        self.store(tmp, value, decl='auto')
        return tmp

    def declare(self, node, type, id, redeclare=False, initialize=False, check_only=False):
        if type == t.Void:
            self.throw(node, err.InvalidDeclaration(type))
        if id in self.env and not redeclare:
            self.throw(node, err.RedeclaredIdentifier(id))
        if check_only:
            return

        var = self.var(type)
        self.env[id] = var
        self.output(f'{type} {var.name}', toplevel=(self.level == 0))

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

    def store(self, left, right, decl=None):
        decl = str(decl) + ' ' if decl else ''
        self.output(f'{decl}{left} = {right}')

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

    def unaryop(self, node, op, value):
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

            elif left.type.isSequence() and right.type == t.Int:
                return v.Call('multiply', left, right, type=left.type)

            elif left.type == t.Int and right.type.isSequence():
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

        elif op == '&':
            if left.type == right.type and left.type.isSet():
                return v.Call('intersection', left, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '#':
            if left.type == right.type and left.type.isSet():
                return v.Call('symmetric_difference', left, right, type=left.type)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '+':
            if left.type == right.type and left.type in {t.Int, t.Float}:
                return v.BinaryOperation(left, op, right, type=left.type)

            elif left.type != right.type and left.type in {t.Char, t.String} and right.type in {t.Char, t.String}:
                return v.Call('concat', left, right, type=t.String)

            elif left.type == right.type and left.type.isCollection():
                return v.Call('concat', left, right, type=left.type)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '-':
            if left.type == right.type and left.type in {t.Int, t.Float}:
                return v.BinaryOperation(left, op, right, type=left.type)

            elif left.type == right.type and left.type.isSet():
                return v.Call('difference', left, right, type=left.type)

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

    def write(self, format, *values):
        args = ''.join(f', {value}' for value in values)
        self.output(f'printf("{format}"{args})')

    def print(self, node, value):
        type = value.type

        if type.isPrintable():
            self.output(v.Call('write', value))

        elif type != t.Unknown:
            self.throw(node, err.NotPrintable(type))

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

            if node in {'ExprCollection', 'ExprIndex', 'ExprBinaryOp', 'ExprRange', 'ExprIsNull', 'ExprCmp', 'ExprLogicalOp', 'ExprCond', 'ExprTuple'}:
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                }
            if node == 'ExprComprehension':
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
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

        body = template.body

        if not body:  # `extern`
            func = v.Variable(template.type, template.id)
            template.compiled[real_types] = func

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

            func = self.var(func_type, prefix='f')
            template.compiled[real_types] = func

            arg_vars = [self.var(arg.type, prefix='a') for arg in func_type.args]
            block = c.Block()
            definition = c.FunctionBody(
                c.FunctionDeclaration(
                    c.Value(str(func_type.ret), func.name),
                    [c.Value(str(arg.type), arg.name) for arg in arg_vars]),
                block)

            self.output(f'{func_type.ret} {func}({func_type.args_str()})', toplevel=True)
            self.output(definition, toplevel=True)

            with self.block(block):
                with self.local(next_level=True):
                    self.env = template.env.copy()

                    for name, type in zip(template.typevars, real_types):
                        self.env[name] = type

                    self.env['#return'] = func_type.ret
                    self.env.pop('#loop', None)

                    for arg, var in zip(func_type.args, arg_vars):
                        self.env[arg.name] = var
                        self.initialized.add(arg.name)

                    self.compile(body)

                    if func_type.ret != t.Void and '#return' not in self.initialized:
                        self.throw(body, err.MissingReturn())

        return func


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

        if value.type == t.Void:
            self.output(value)
        else:
            value = self.tmp(value)

        for lvalue in node['lvalues']:
            self.assign(lvalue, lvalue, value)

    def compileStmtAssgExpr(self, node):
        exprs = node['exprs']
        op = node['op']
        left = self.lvalue(node, exprs[0])

        if op == '??':
            block = c.Block()
            self.output(c.If(v.IsNull(left), block))
            with self.block(block):
                right = self.compile(exprs[1])
                if not left.type.isNullable() or not can_cast(right.type, left.type.subtype):
                    self.throw(node, err.NoBinaryOperator(op, left.type, right.type))
                self.store(left, v.Nullable(self.cast(node, right, left.type.subtype)))
        else:
            right = self.compile(exprs[1])
            value = self.binaryop(node, op, left, right)
            if value.type != left.type:
                self.throw(node, err.IllegalAssignment(value.type, left.type))
            self.store(left, value)

    def compileStmtAppend(self, node):
        # Special instruction for array/set/dict comprehension.
        collection = self.compile(node['collection'])
        values = lmap(self.compile, node['exprs'])

        if collection.type.isArray():
            self.output(v.Call(v.Attribute(collection, 'push_back'), *values))
        elif collection.type.isSet():
            self.output(v.Call(v.Attribute(collection, 'insert'), *values))
        elif collection.type.isDict():
            self.output(v.Call(v.Attribute(collection, 'insert_or_assign'), *values))

    def compileStmtIf(self, node):
        exprs = node['exprs']
        blocks = node['blocks']

        initialized_vars = []
        stmt = None

        for expr, block in reversed(list(zip_longest(exprs, blocks))):
            if expr:
                cond = self.cast(expr, self.compile(expr), t.Bool)

            then = c.Block()
            with self.block(then):
                with self.local():
                    self.compile(block)
                    initialized_vars.append(self.initialized)

            if expr:
                stmt = c.If(cond, then, stmt)
            else:
                stmt = then

        self.output(stmt)

        if len(blocks) > len(exprs):  # there is an `else` statement
            self.initialized.update(set.intersection(*initialized_vars))

    def compileStmtWhile(self, node):
        expr = node['expr']

        with self.local():
            self.env['#loop'] = True

            body = c.Block()
            with self.block(body):
                cond = self.cast(expr, self.compile(expr), t.Bool)
                cond = v.UnaryOperation('!', cond)
                self.output(c.If(cond, c.Block([c.Statement('break')])))

                self.compile(node['block'])

        self.output(c.While(v.true, body))

    def compileStmtUntil(self, node):
        expr = node['expr']

        with self.local():
            self.env['#loop'] = True

            second_iteration = self.var(t.Bool)
            self.store(second_iteration, v.false, 'auto')

            body = c.Block()
            with self.block(body):
                cond = self.cast(expr, self.compile(expr), t.Bool)
                cond = v.BinaryOperation(second_iteration, '&&', cond)
                self.output(c.If(cond, c.Block([c.Statement('break')])))
                self.store(second_iteration, v.true)

                self.compile(node['block'])

        self.output(c.While(v.true, body))

    def compileStmtFor(self, node):
        vars = node['vars']
        iterables = node['iterables']

        types = []
        steps = []
        indices = []
        iterators = []
        conditions = []
        getters = []

        def prepare(iterable, step):
            # It must be a function so that there are separate scopes of variables to use in lambdas.

            if iterable['node'] == 'ExprRange':
                values = lmap(self.compile, iterable['exprs'])
                type = values[0].type
                if type not in {t.Int, t.Float, t.Bool, t.Char}:
                    self.throw(iterable, err.UnknownType())
                if len(values) > 1:
                    values[1] = self.cast(iterable, values[1], type)

                types.append(type)
                index = iterator = self.var(t.Float if type == t.Float else t.Int)
                start = v.Cast(values[0], index.type)
                self.cast(node, step, index.type)

                if len(values) == 1:
                    cond = lambda x: v.true  # infinite range
                else:
                    end = self.freeze(values[1])
                    e = '=' if iterable['inclusive'] else ''
                    cond = lambda x: f'{step} < 0 ? {x} >{e} {end} : {x} <{e} {end}'

                getter = lambda x: v.Cast(x, type)

            else:
                value = self.tmp(self.compile(iterable))
                type = value.type
                if not type.isCollection():
                    self.throw(node, err.NotIterable(type))

                types.append(type.subtype)
                index = self.var(t.Int)
                self.store(index, v.Int(0), 'auto')
                iterator = self.var(None)
                start = self.tmp(v.Call(v.Attribute(value, 'begin')))

                if type.isSequence():
                    # The following doesn't work in GCC with non-random access iterators (program crashes or loops forever).
                    end = self.tmp(v.Call(v.Attribute(value, 'end')))
                    self.output(f'if ({step} < 0 && {start} != {end}) {start} = std::prev({end})')
                else:
                    # But then we don't care about the order anyway.
                    self.store(step, v.Call('abs', step))

                length = self.tmp(v.Call(v.Attribute(value, 'size')))
                cond = lambda x: f'abs({x}) < {length}'
                getter = lambda x: v.UnaryOperation('*', x, type=type.subtype)

            self.store(iterator, start, 'auto')
            indices.append(index)
            iterators.append(iterator)
            conditions.append(cond)
            getters.append(getter)

        steps = [self.freeze(self.compile(step)) for step in node.get('steps') or [{'node': 'AtomInt', 'int': 1}]]
        if len(steps) == 1:
            steps *= len(iterables)
        elif len(steps) != len(iterables):
            self.throw(node, err.InvalidLoopStep())

        for iterable, step in zip(iterables, steps):
            prepare(iterable, step)

        body = c.Block()
        with self.block(body):
            with self.local():
                self.env['#loop'] = True

                if len(vars) == 1 and len(types) > 1:
                    tuple = v.Tuple([getters[i](iterator) for i, iterator in enumerate(iterators)])
                    self.assign(node, vars[0], tuple)
                elif len(vars) > 1 and len(types) == 1:
                    for i, var in enumerate(vars):
                        tuple = getters[0](iterators[0])
                        self.assign(node, var, v.Get(tuple, i))
                elif len(vars) == len(types):
                    for var, iterator, getter in zip(vars, iterators, getters):
                        self.assign(node, var, getter(iterator))
                else:
                    self.throw(node, err.CannotUnpack(t.Tuple(types), len(vars)))

                self.compile(node['block'])

        # Advancing iterator beyond the container boundaries is UB (and crashes in practice),
        # so it must happen after the condition is checked, when we know it is safe.
        condition = ' && '.join(f'{cond(index)}' + (f' && ({index} == 0 || (std::advance({iterator}, {step}), true))' if iterator.type is None else '')
                                for index, iterator, cond, step in zip(indices, iterators, conditions, steps))
        update = ', '.join(f'{index} += {step}' for index, step in zip(indices, steps))

        self.output(c.For('', condition, update, body))

    def compileStmtLoopControl(self, node):
        stmt = node['stmt']  # `break` / `continue`

        if not self.env.get('#loop'):
            self.throw(node, err.UnexpectedStatement(stmt))

        self.output(stmt)

    def compileStmtFunc(self, node, class_type=None):
        id = node['id']

        if class_type is None:
            self.initialized.add(id)

        with self.local():
            typevars = node.get('typevars', [])
            for name in typevars:
                self.env[name] = t.Var(name)

            args = [] if class_type is None else [t.Func.Arg(class_type, 'self')]
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
                args.append(t.Func.Arg(type, name, default))

            ret_type = self.compile(node.get('ret')) or t.Void
            func_type = t.Func(args, ret_type)

            env = self.env.copy()
            func = v.FunctionTemplate(id, typevars, func_type, node['block'], env)

        if class_type is None:
            self.env[id] = env[id] = func
            self.levels[id] = self.level
        else:
            return self.function(func)

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
            if expr:
                self.output(value)
            self.output('return')
        else:
            self.output(f'return {value}')

    def compileStmtClass(self, node):
        id = node['id']
        if id in self.env:
            self.throw(node, err.RedeclaredIdentifier(id))
        self.initialized.add(id)

        base = self.compile(node['base'])
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

        fields = []
        self.output(f'struct {cls.name}', toplevel=True)
        self.output(c.Struct(cls.name + (f': {base.initializer.name}' if base else ''), fields), toplevel=True)

        for member in node['members']:
            name = member['id']

            if member['node'] == 'ClassField':
                if name in members:
                    self.throw(member, err.RepeatedMember(name))
                if name == 'toString':
                    self.throw(member, err.InvalidMember(name))

                field = self.var(self.compile(member['type']), prefix='m')
                fields.append(c.Value(field.type, field.name))
                members[name] = field

            else:
                if name in members and name not in base_members:
                    self.throw(member, err.RepeatedMember(name))

                members[name] = methods[name] = None

                if member['block']:
                    with self.local():
                        self.env['#super'] = base_methods.get(name)
                        methods[name] = func = self.compileStmtFunc(member, class_type=type)

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
                        fields.append(c.FunctionBody(c.FunctionDeclaration(c.Value(f'virtual void*', members[name].name), []), block))
                        with self.block(block):
                            self.output(f'return reinterpret_cast<void*>({func})')

        block = c.Block()
        fields.append(c.FunctionBody(c.FunctionDeclaration(c.Value('', cls.name), []), block))
        with self.block(block):
            for member in node['members']:
                name = member['id']
                default = member.get('default')
                if default:
                    value = self.cast(member, self.compile(default), members[name].type)
                    self.store(f'this->{members[name].name}', value)


    ### Expressions ###

    def compileExprCollection(self, node):
        exprs = node['exprs']
        kind = node['kind']

        if len(exprs) == 1 and exprs[0]['node'] == 'ExprRange':
            var = {
                'node': 'AtomId',
                'id': f'__range_{len(self.env)}',
            }
            return self.compile({
                'node': 'ExprComprehension',
                'kind': kind,
                'exprs': [var],
                'comprehensions': [{
                    'node': 'ComprehensionGenerator',
                    'vars': [var],
                    'iterables': [exprs[0]],
                    'steps': [node['step']] if node.get('step') else [],
                }],
            })
        elif node.get('step'):
            self.throw(node, err.InvalidSyntax())

        if kind == 'array':
            result = v.Array(self.unify(node, *map(self.compile, exprs)))
        elif kind == 'set':
            result = v.Set(self.unify(node, *map(self.compile, exprs)))
            if not result.type.subtype.isHashable():
                self.throw(node, err.NotHashable(result.type.subtype))
        elif kind == 'dict':
            result = v.Dict(lzip(self.unify(node, *map(self.compile, exprs[0::2])), self.unify(node, *map(self.compile, exprs[1::2]))))
            if not result.type.key_type.isHashable():
                self.throw(node, err.NotHashable(result.type.key_type))

        return result

    def compileExprComprehension(self, node):
        exprs = node['exprs']
        kind = node['kind']

        value, collection = [{
            'node': 'AtomId',
            'id': f'__cpr_{len(self.env)}_{name}',
        } for name in ['value', 'collection']]

        stmt = inner_stmt = {
            'node': 'StmtAssg',
            'lvalues': [value],
            'expr': {
                'node': 'ExprTuple',
                'exprs': exprs,
            },
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
                inner_stmt['_eval'] = lambda: self.compile(value).type.elements
                self.compile(stmt)
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
                self.assign(node, collection, v.Dict([], *types))

            inner_stmt['node'] = 'StmtAppend'
            inner_stmt['collection'] = collection
            inner_stmt['exprs'] = exprs

            self.compile(stmt)

            result = self.compile(collection)

        return result

    def compileExprAttr(self, node):
        expr = node['expr']
        attr = node['attr']

        if node.get('safe'):
            obj = self.tmp(self.compile(expr))
            return self.safe(node, obj, lambda: v.Nullable(self.attr(node, v.Extract(obj), attr)), lambda: v.null)

        obj, value = self.attribute(node, expr, attr)
        return value

    def compileExprIndex(self, node):
        exprs = node['exprs']

        if node.get('safe'):
            collection = self.tmp(self.compile(exprs[0]))
            return self.safe(node, collection, lambda: v.Nullable(self.index(node, v.Extract(collection), self.compile(exprs[1]))), lambda: v.null)

        return self.index(node, *map(self.compile, exprs))

    def compileExprSlice(self, node):
        slice = node['slice']

        collection = self.compile(node['expr'])
        type = collection.type
        if not type.isSequence():
            self.throw(node, err.NotIndexable(type))

        a = v.Nullable(self.cast(slice[0], self.compile(slice[0]), t.Int)) if slice[0] else v.Nullable()
        b = v.Nullable(self.cast(slice[1], self.compile(slice[1]), t.Int)) if slice[1] else v.Nullable()
        step = self.cast(slice[2], self.compile(slice[2]), t.Int) if slice[2] else v.Int(1)

        return v.Call('slice', collection, a, b, step, type=type)

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
                        self.throw(node, err.TooFewArguments())

                    expr = self.convert_lambda(expr)
                    if expr['node'] == 'ExprLambda':
                        ids = expr['ids']
                        type = func_arg.type

                        if not type.isFunc():
                            self.throw(node, err.IllegalLambda())

                        if len(ids) < len(type.args):
                            self.throw(node, err.TooFewArguments())
                        if len(ids) > len(type.args):
                            self.throw(node, err.TooManyArguments())

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
                                self.throw(node, err.TooFewArguments())
                            if len(value.type.args) > len(func_arg.type.args):
                                self.throw(node, err.TooManyArguments())

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
                    self.throw(node, err.TooManyArguments())

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
                        func = self.function(func)
                    except err as e:
                        self.throw(node, err.InvalidFunctionCall(func.id, assigned_types, str(e)[:-1]))

            return v.Call(func, *args, type=func.type.ret)

        if expr['node'] == 'ExprAttr':
            attr = expr['attr']

            if expr.get('safe'):
                obj = self.tmp(self.compile(expr['expr']))

                def callback():
                    value = self.tmp(v.Extract(obj))
                    func = self.attr(node, value, attr)
                    return v.Nullable(_call(value, func))

                return self.safe(node, obj, callback, lambda: v.null)
            else:
                obj, func = self.attribute(expr, expr['expr'], attr)

        else:
            func = self.compile(expr)

            if expr['node'] == 'AtomSuper':
                obj = v.Cast(self.get(expr, 'self'), func.type.args[0].type)
            else:
                obj = None

        if isinstance(func, t.Class):
            obj = self.tmp(v.Call(f'std::make_shared<{func.initializer.name}>', type=func))
            method = func.methods.get('<constructor>')
            if method:
                self.output(_call(obj, method))
            return obj

        result = _call(obj, func)
        if result.type != t.Void:
            result = self.tmp(result)
        return result

    def compileExprUnaryOp(self, node):
        op = node['op']
        value = self.compile(node['expr'])

        if op == '!':
            if not value.type.isNullable():
                self.throw(node, err.NotNullable(value.type))

            return v.Extract(value)

        return self.unaryop(node, op, value)

    def compileExprBinaryOp(self, node):
        op = node['op']
        exprs = node['exprs']

        if op == '??':
            left = self.tmp(self.compile(exprs[0]))
            try:
                return self.safe(node, left, lambda: v.Extract(left), lambda: self.compile(exprs[1]))
            except err:
                self.throw(node, err.NoBinaryOperator(op, left.type, self.compile(exprs[1]).type))

        return self.binaryop(node, op, *map(self.compile, exprs))

    def compileExprRange(self, node):
        self.throw(node, err.IllegalRange())

    def compileExprIsNull(self, node):
        value = self.compile(node['expr'])
        if not value.type.isNullable():
            self.throw(node, err.NotNullable(value.type))

        if value.type.isUnknown():  # for the `null is null` case
            return v.Bool(not node.get('not'))

        return v.IsNotNull(value) if node.get('not') else v.IsNull(value)

    def compileExprCmp(self, node):
        exprs = node['exprs']
        ops = node['ops']

        result = self.var(t.Bool)
        self.store(result, v.false, 'auto')

        left = self.compile(exprs[0])

        def emitIf(index):
            nonlocal left
            right = self.compile(exprs[index])
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

            cond = v.BinaryOperation(left, op, right, type=t.Bool)
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

    def compileExprLogicalOp(self, node):
        exprs = node['exprs']
        op = node['op']

        result = self.var(t.Bool)
        self.store(result, v.Bool(op == 'or'), 'auto')

        cond1 = self.compile(exprs[0])
        if op == 'or':
            cond1 = v.UnaryOperation('!', cond1, type=t.Bool)

        block = c.Block()
        self.output(c.If(cond1, block))
        with self.block(block):
            cond2 = self.compile(exprs[1])
            if not cond1.type == cond2.type == t.Bool:
                self.throw(node, err.NoBinaryOperator(op, cond1.type, cond2.type))
            self.store(result, cond2)

        return result

    def compileExprCond(self, node):
        exprs = node['exprs']
        return self.cond(node, self.compile(exprs[0]), lambda: self.compile(exprs[1]), lambda: self.compile(exprs[2]))

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
        expr = self.convert_string(node, node['string'])

        if expr['node'] == 'AtomString':
            return v.String(expr['string'])
        
        try:
            return self.compile(expr)
        except err as e:
            self.throw({
                **node,
                'position': [e.line+node['position'][0]-1, e.column+node['position'][1]+1],
            }, str(e).partition(': ')[2][:-1])

    def compileAtomNull(self, node):
        return v.null

    def compileAtomSuper(self, node):
        func = self.env.get('#super')
        if func is None:
            self.throw(node, err.IllegalSuper())
        return func

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

    def compileTypeSet(self, node):
        return t.Set(self.compile(node['subtype']))

    def compileTypeDict(self, node):
        return t.Dict(self.compile(node['key_type']), self.compile(node['value_type']))

    def compileTypeNullable(self, node):
        return t.Nullable(self.compile(node['subtype']))

    def compileTypeTuple(self, node):
        return t.Tuple(lmap(self.compile, node['elements']))

    def compileTypeFunc(self, node):
        return t.Func(lmap(self.compile, node['args']), self.compile(node['ret']) or t.Void)
