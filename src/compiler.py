
import re
from contextlib import contextmanager

import llvmlite.ir as ll

from .errors import PyxellError as err
from .parsing import parse_expr
from .types import *
from .utils import *


class CustomIRBuilder(ll.IRBuilder):

    def _set_terminator(self, term):
        self.basic_block.terminator = None  # to prevent llvmlite's AssertionError
        super()._set_terminator(term)


class Unit:

    def __init__(self, env, initialized):
        self.env = env
        self.initialized = initialized


class PyxellCompiler:

    def __init__(self):
        self.units = {}
        self._unit = None
        self._keep_env = False
        self.builder = CustomIRBuilder()
        self.module = ll.Module()
        self.builtins = {
            'malloc': ll.Function(self.module, tFunc([tInt], tPtr()).pointee, 'malloc'),
            'realloc': ll.Function(self.module, tFunc([tPtr(), tInt], tPtr()).pointee, 'realloc'),
            'memcpy': ll.Function(self.module, tFunc([tPtr(), tPtr(), tInt]).pointee, 'memcpy'),
            'putchar': ll.Function(self.module, tFunc([tChar]).pointee, 'putchar'),
        }
        self.main = ll.Function(self.module, tFunc([], tInt).pointee, 'main')
        self.builder.position_at_end(self.main.append_basic_block('entry'))

    def run(self, ast, unit):
        self.units[unit] = Unit({}, set())
        with self.unit(unit):
            if unit != 'std':
                self.env = self.units['std'].env.copy()
                self.initialized = self.units['std'].initialized.copy()
            self.compile(ast)

    def run_main(self, ast):
        self.run(ast, 'main')
        self.builder.ret(ll.Constant(tInt, 0))

    def compile(self, node):
        return getattr(self, 'compile'+node['node'])(node)

    def expr(self, code, **params):
        return self.compile(parse_expr(code.format(**params)))

    def throw(self, node, msg):
        line, column = node.get('position', (1, 1))
        raise err(msg, line, column)

    def llvm_ir(self):
        return str(self.module)


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

    @contextmanager
    def local(self):
        if self._keep_env:
            yield
            return
        env = self.env.copy()
        initialized = self.initialized.copy()
        yield
        self.env = env
        self.initialized = initialized

    @contextmanager
    def unit(self, name):
        _unit = self._unit
        self._unit = self.units[name]
        yield
        self._unit = _unit

    @contextmanager
    def no_output(self, keep_env=False):
        prev_keep_env = self._keep_env
        if keep_env:
            self._keep_env = True
        dummy_module = ll.Module()
        dummy_func = ll.Function(dummy_module, tFunc([]).pointee, 'dummy')
        dummy_label = dummy_func.append_basic_block('dummy')
        prev_label = self.builder.basic_block
        self.builder.position_at_end(dummy_label)
        yield
        self.builder.position_at_end(prev_label)
        if keep_env:
            self._keep_env = prev_keep_env

    @contextmanager
    def block(self):
        label_start = self.builder.append_basic_block()
        self.builder.branch(label_start)
        self.builder.position_at_end(label_start)
        label_end = ll.Block(self.builder.function)
        yield label_start, label_end
        self.builder.function.blocks.append(label_end)
        self.builder.position_at_end(label_end)

    def get(self, node, id, load=True):
        if id not in self.env:
            self.throw(node, err.UndeclaredIdentifier(id))
        if id not in self.initialized:
            self.throw(node, err.UninitializedIdentifier(id))
        ptr = self.env[id]
        return self.builder.load(ptr) if load else ptr

    def extract(self, ptr, *indices):
        return self.builder.load(self.builder.gep(ptr, [vInt(0), *[ll.Constant(ll.IntType(32), i) for i in indices]]))

    def insert(self, value, ptr, *indices):
        return self.builder.store(value, self.builder.gep(ptr, [vInt(0), *[ll.Constant(ll.IntType(32), i) for i in indices]]))

    def index(self, node, collection, index, lvalue=False):
        if collection.type.isCollection():
            if lvalue and not collection.type.isArray():
                self.throw(node, err.NotLvalue())

            index = self.cast(node, index, tInt)
            length = self.extract(collection, 1)
            cmp = self.builder.icmp_signed('>=', index, vInt(0))
            index = self.builder.select(cmp, index, self.builder.add(index, length))
            return self.builder.gep(self.extract(collection, 0), [index])

        self.throw(node, err.NotIndexable(collection.type))

    def safe(self, node, value, callback_notnull, callback_null):
        if not value.type.isNullable():
            self.throw(node, err.NotNullable(value.type))

        with self.builder.if_else(self.builder.icmp_unsigned('!=', value, vNull())) as (label_notnull, label_null):
            with label_notnull:
                value_notnull = callback_notnull()
                label_notnull = self.builder.basic_block
            with label_null:
                value_null = callback_null()
                label_null = self.builder.basic_block

        phi = self.builder.phi(value_notnull.type)
        phi.add_incoming(value_notnull, label_notnull)
        phi.add_incoming(value_null, label_null)
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

        if type == tInt:
            if attr == 'toString':
                value = self.get(node, 'Int_toString')
            elif attr == 'toFloat':
                value = self.get(node, 'Int_toFloat')

        elif type == tFloat:
            if attr == 'toString':
                value = self.get(node, 'Float_toString')
            elif attr == 'toInt':
                value = self.get(node, 'Float_toInt')

        elif type == tBool:
            if attr == 'toString':
                value = self.get(node, 'Bool_toString')
            elif attr == 'toInt':
                value = self.get(node, 'Bool_toInt')
            elif attr == 'toFloat':
                value = self.get(node, 'Bool_toFloat')

        elif type == tChar:
            if attr == 'toString':
                value = self.get(node, 'Char_toString')
            elif attr == 'toInt':
                value = self.get(node, 'Char_toInt')
            elif attr == 'toFloat':
                value = self.get(node, 'Char_toFloat')

        elif type.isCollection():
            if attr == 'length':
                value = self.extract(obj, 1)
            elif type == tString:
                if attr == 'toString':
                    value = self.get(node, 'String_toString')
                elif attr == 'toArray':
                    value = self.get(node, 'String_toArray')
                elif attr == 'toInt':
                    value = self.get(node, 'String_toInt')
                elif attr == 'toFloat':
                    value = self.get(node, 'String_toFloat')
            elif type.isArray():
                if attr == 'join':
                    if type.subtype == tChar:
                        value = self.get(node, 'CharArray_join')
                    elif type.subtype == tString:
                        value = self.get(node, 'StringArray_join')

        elif type.isTuple() and len(attr) == 1:
            index = ord(attr) - ord('a')
            if 0 <= index < len(type.elements):
                value = self.extract(obj, index)

        if value is None:
            self.throw(node, err.NoAttribute(type, attr))

        return value

    def call(self, name, *values):
        func = self.builder.load(self.env[name])
        return self.builder.call(func, values)

    def cast(self, node, value, type):
        if not can_cast(value.type, type):
            self.throw(node, err.IllegalAssignment(value.type, type))
        if not value.type.isNullable() and type.isNullable():
            return self.cast(node, self.nullable(value), type)
        return value if value.type == type else self.builder.bitcast(value, type)

    def unify(self, node, *values):
        if not values:
            return []
        values = list(values)

        type = values[0].type
        for value in values[1:]:
            type = unify_types(value.type, type)
            if type is None:
                self.throw(node, err.UnknownType())

        for i, value in enumerate(values):
            if value.type == tInt and type == tFloat:
                values[i] = self.builder.sitofp(value, type)
            else:
                values[i] = self.cast(node, value, type)

        return values

    def declare(self, node, type, id, redeclare=False, initialize=False):
        if type == tVoid:
            self.throw(node, err.InvalidDeclaration(type))
        if type.isUnknown():
            self.throw(node, err.UnknownType())

        if id in self.env and not redeclare:
            self.throw(node, err.RedeclaredIdentifier(id))

        if self.builder.function._name == 'main':
            ptr = ll.GlobalVariable(self.module, type, self.module.get_unique_name(id))
            ptr.initializer = type.default()
        else:
            ptr = self.builder.alloca(type)

        self.env[id] = ptr
        if initialize:
            self.initialized.add(id)

        return ptr

    def lvalue(self, node, expr, declare=None, override=False, initialize=False):
        if expr['node'] == 'AtomId':
            id = expr['id']

            if id not in self.env:
                if declare is None:
                    self.throw(node, err.UndeclaredIdentifier(id))
                self.declare(node, declare, id)
            elif override:
                self.declare(node, declare, id, redeclare=True)

            if initialize:
                self.initialized.add(id)

            return self.env[id]

        elif expr['node'] == 'ExprIndex' and not expr.get('safe'):
            return self.index(node, *map(self.compile, expr['exprs']), lvalue=True)

        self.throw(node, err.NotLvalue())

    def assign(self, node, expr, value):
        ptr = self.lvalue(node, expr, declare=value.type, override=expr.get('override', False), initialize=True)
        value = self.cast(node, value, ptr.type.pointee)
        self.builder.store(value, ptr)

    def inc(self, ptr, step=vInt(1)):
        add = self.builder.fadd if ptr.type.pointee == tFloat else self.builder.add
        self.builder.store(add(self.builder.load(ptr), step), ptr)

    def sizeof(self, type, length=vInt(1)):
        return self.builder.ptrtoint(self.builder.gep(vNull(tPtr(type)), [length]), tInt)

    def malloc(self, type, length=vInt(1)):
        size = self.sizeof(type.pointee, length)
        ptr = self.builder.call(self.builtins['malloc'], [size])
        return self.builder.bitcast(ptr, type)

    def realloc(self, ptr, length=vInt(1)):
        type = ptr.type
        size = self.sizeof(type.pointee, length)
        ptr = self.builder.bitcast(ptr, tPtr())
        ptr = self.builder.bitcast(ptr, tPtr())
        ptr = self.builder.call(self.builtins['realloc'], [ptr, size])
        return self.builder.bitcast(ptr, type)

    def memcpy(self, dest, src, length):
        type = dest.type
        dest = self.builder.bitcast(dest, tPtr())
        src = self.builder.bitcast(src, tPtr())
        size = self.sizeof(type.pointee, length)
        return self.builder.call(self.builtins['memcpy'], [dest, src, size])

    def unaryop(self, node, op, value):
        if op == '!':
            if not value.type.isNullable():
                self.throw(node, err.NotNullable(value.type))
        else:
            if op in ('+', '-'):
                types = [tInt, tFloat]
            elif op == '~':
                types = [tInt]
            elif op == 'not':
                types = [tBool]

            if value.type not in types:
                self.throw(node, err.NoUnaryOperator(op, value.type))

        if op == '!':
            return self.extract(value)
        elif op == '+':
            return value
        elif op == '-':
            if value.type == tInt:
                return self.builder.sub(vInt(0), value)
            elif value.type == tFloat:
                return self.builder.fsub(vFloat(0), value)
        elif op in ('~', 'not'):
            return self.builder.not_(value)

    def binaryop(self, node, op, left, right):
        if left.type in (tInt, tFloat) and right.type in (tInt, tFloat):
            left, right = self.unify(node, left, right)

        if op == '^':
            if left.type == right.type == tInt:
                return self.call('Int_pow', left, right)

            elif left.type == right.type == tFloat:
                return self.call('Float_pow', left, right)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '*':
            if left.type == right.type == tInt:
                return self.builder.mul(left, right)

            elif left.type == right.type == tFloat:
                return self.builder.fmul(left, right)

            elif left.type.isCollection() and right.type == tInt:
                type = left.type
                subtype = type.subtype

                src = self.extract(left, 0)
                src_length = self.extract(left, 1)
                length = self.builder.mul(src_length, right)
                dest = self.malloc(tPtr(subtype), length)

                index = self.builder.alloca(tInt)
                self.builder.store(vInt(0), index)

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

            elif left.type == tInt and right.type.isCollection():
                return self.binaryop(node, op, right, left)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '/':
            if left.type == right.type == tInt:
                v1 = self.builder.sdiv(left, right)
                v2 = self.builder.sub(v1, vInt(1))
                v3 = self.builder.xor(left, right)
                v4 = self.builder.icmp_signed('<', v3, vInt(0))
                v5 = self.builder.select(v4, v2, v1)
                v6 = self.builder.mul(v1, right)
                v7 = self.builder.icmp_signed('!=', v6, left)
                return self.builder.select(v7, v5, v1)

            elif left.type == right.type == tFloat:
                return self.builder.fdiv(left, right)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '%':
            if left.type == right.type == tInt:
                v1 = self.builder.srem(left, right)
                v2 = self.builder.add(v1, right)
                v3 = self.builder.xor(left, right)
                v4 = self.builder.icmp_signed('<', v3, vInt(0))
                v5 = self.builder.select(v4, v2, v1)
                v6 = self.builder.icmp_signed('==', v1, vInt(0))
                return self.builder.select(v6, v1, v5)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '+':
            if left.type == right.type == tInt:
                return self.builder.add(left, right)

            elif left.type == right.type == tFloat:
                return self.builder.fadd(left, right)

            elif left.type == right.type and left.type.isCollection():
                type = left.type
                subtype = type.subtype

                length1 = self.extract(left, 1)
                length2 = self.extract(right, 1)
                length = self.builder.add(length1, length2)

                array1 = self.extract(left, 0)
                array2 = self.extract(right, 0)
                array = self.malloc(tPtr(subtype), length)

                self.memcpy(array, array1, length1)
                self.memcpy(self.builder.gep(array, [length1]), array2, length2)

                result = self.malloc(type)
                self.insert(array, result, 0)
                self.insert(length, result, 1)
                return result

            elif left.type == tString and right.type == tChar:
                return self.binaryop(node, op, left, self.call('Char_toString', right))

            elif left.type == tChar and right.type == tString:
                return self.binaryop(node, op, self.call('Char_toString', left), right)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '-':
            if left.type == right.type == tInt:
                return self.builder.sub(left, right)

            elif left.type == right.type == tFloat:
                return self.builder.fsub(left, right)

            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

        else:
            if left.type == right.type == tInt:
                instruction = {
                    '<<': self.builder.shl,
                    '>>': self.builder.ashr,
                    '&': self.builder.and_,
                    '$': self.builder.xor,
                    '|': self.builder.or_,
                }[op]
                return instruction(left, right)
            else:
                self.throw(node, err.NoBinaryOperator(op, left.type, right.type))

    def cmp(self, node, op, left, right):
        try:
            left, right = self.unify(node, left, right)
        except err:
            self.throw(node, err.NotComparable(left.type, right.type))

        if left.type in (tInt, tChar):
            return self.builder.icmp_signed(op, left, right)

        elif left.type == tFloat:
            return self.builder.fcmp_ordered(op, left, right)

        elif left.type == tBool:
            return self.builder.icmp_unsigned(op, left, right)

        elif left.type.isCollection():
            array1 = self.extract(left, 0)
            array2 = self.extract(right, 0)
            length1 = self.extract(left, 1)
            length2 = self.extract(right, 1)

            index = self.builder.alloca(tInt)
            self.builder.store(vInt(0), index)

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
                cond = self.cmp(node, op + '=' if op in ('<', '>') else op, *values)

                if op == '!=':
                    self.builder.cbranch(cond, label_true, label_cont)
                else:
                    self.builder.cbranch(cond, label_cont, label_false)

                self.builder.function.blocks.append(label_cont)
                self.builder.position_at_end(label_cont)

                if op in ('<=', '>=', '<', '>'):
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

            phi = self.builder.phi(tBool)
            phi.add_incoming(vTrue, label_true)
            phi.add_incoming(vFalse, label_false)
            phi.add_incoming(length_cond, label_length)
            return phi

        elif left.type.isTuple():
            with self.block() as (label_start, label_end):
                label_true = ll.Block(self.builder.function)
                label_false = ll.Block(self.builder.function)

                for i in range(len(left.type.elements)):
                    label_cont = ll.Block(self.builder.function)

                    values = [self.extract(tuple, i) for tuple in [left, right]]
                    cond = self.cmp(node, op + '=' if op in ('<', '>') else op, *values)

                    if op == '!=':
                        self.builder.cbranch(cond, label_true, label_cont)
                    else:
                        self.builder.cbranch(cond, label_cont, label_false)

                    self.builder.function.blocks.append(label_cont)
                    self.builder.position_at_end(label_cont)

                    if op in ('<=', '>=', '<', '>'):
                        label_cont = ll.Block(self.builder.function)

                        cond2 = self.cmp(node, '!=', *values)
                        self.builder.cbranch(cond2, label_true, label_cont)

                        self.builder.function.blocks.append(label_cont)
                        self.builder.position_at_end(label_cont)

                self.builder.branch(label_end)

                for label in [label_true, label_false]:
                    self.builder.function.blocks.append(label)
                    self.builder.position_at_end(label)
                    self.builder.branch(label_end)

            phi = self.builder.phi(tBool)
            phi.add_incoming(vTrue, label_true)
            phi.add_incoming(vFalse, label_false)
            phi.add_incoming(vBool(op not in ('!=', '<', '>')), label_cont)
            return phi

        elif left.type == tUnknown:
            return vTrue

        else:
            self.throw(node, err.NotComparable(left.type, right.type))

    def write(self, str):
        for char in str:
            self.builder.call(self.builtins['putchar'], [vChar(char)])

    def print(self, node, value):
        type = value.type
        
        if type == tInt:
            self.call('writeInt', value)

        elif type == tFloat:
            self.call('writeFloat', value)

        elif type == tBool:
            self.call('writeBool', value)

        elif type == tChar:
            self.call('writeChar', value)

        elif type.isString():
            self.call('write', value)

        elif type.isArray():
            self.write('[')

            length = self.extract(value, 1)
            index = self.builder.alloca(tInt)
            self.builder.store(vInt(0), index)

            with self.block() as (label_start, label_end):
                i = self.builder.load(index)

                with self.builder.if_then(self.builder.icmp_signed('>=', i, length)):
                    self.builder.branch(label_end)

                with self.builder.if_then(self.builder.icmp_signed('>', i, vInt(0))):
                    self.write(', ')

                elem = self.builder.gep(self.extract(value, 0), [i])
                self.print(node, self.builder.load(elem))

                self.inc(index)

                self.builder.branch(label_start)

            self.write(']')

        elif type.isNullable():
            with self.builder.if_else(self.builder.icmp_signed('!=', value, vNull(type))) as (label_if, label_else):
                with label_if:
                    self.print(node, self.extract(value))
                with label_else:
                    self.write('null')

        elif value.type.isTuple():
            for i in range(len(value.type.elements)):
                if i > 0:
                    self.write(' ')
                self.print(node, self.extract(value, i))

        elif value.type == tUnknown:
            pass

        else:
            self.throw(node, err.NotPrintable(value.type))

    def string(self, lit):
        const = ll.Constant(ll.ArrayType(tChar, len(lit)), [vChar(c) for c in lit])

        array = ll.GlobalVariable(self.module, const.type, self.module.get_unique_name('str'))
        array.global_constant = True
        array.initializer = const

        memory = self.builder.gep(array, [vInt(0), vInt(0)])
        length = vInt(const.type.count)

        result = self.malloc(tString)
        self.insert(memory, result, 0)
        self.insert(length, result, 1)
        return result

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
        type = tArray(subtype)

        if length is None:
            length = vInt(len(values))

        memory = self.malloc(tPtr(subtype), length)
        for i, value in enumerate(values):
            self.builder.store(value, self.builder.gep(memory, [vInt(i)]))

        result = self.malloc(type)
        self.insert(memory, result, 0)
        self.insert(length, result, 1)
        return result

    def nullable(self, value):
        result = self.malloc(tNullable(value.type))
        self.insert(value, result)
        return result

    def tuple(self, values):
        if len(values) == 1:
            return values[0]

        type = tTuple([value.type for value in values])
        result = self.malloc(type)

        for i, value in enumerate(values):
            self.insert(value, result, i)

        return result

    def convert_lambda(self, expr):
        ids = []

        def convert_expr(expr):
            if expr is None:
                return

            nonlocal ids
            node = expr['node']

            if node in ['ExprArray', 'ExprIndex', 'ExprBinaryOp', 'ExprRange', 'ExprIs', 'ExprCmp', 'ExprLogicalOp', 'ExprCond', 'ExprTuple']:
                return {
                    **expr,
                    'exprs': lmap(convert_expr, expr['exprs']),
                }
            if node == 'ExprSlice':
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                    'slice': lmap(convert_expr, expr['slice']),
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
            if node == 'ExprCall':
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
                    'args': lmap(convert_expr, expr['args']),
                }
            if node in ['ComprehensionFilter', 'ExprAttr', 'CallArg', 'ExprUnaryOp']:
                return {
                    **expr,
                    'expr': convert_expr(expr['expr']),
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
        self.write('\n')

    def compileStmtDecl(self, node):
        type = node['type']
        id = node['id']
        expr = node['expr']
        ptr = self.declare(node, type, id, initialize=bool(expr))
        if expr:
            value = self.cast(node, self.compile(expr), type)
            self.builder.store(value, ptr)

    def compileStmtAssg(self, node):
        value = self.compile(node['expr'])

        for lvalue in node['lvalues']:
            exprs = lvalue['exprs']
            len1 = len(exprs)

            if value.type.isTuple():
                len2 = len(value.type.elements)
                if len1 > 1 and len1 != len2:
                    self.throw(node, err.CannotUnpack(value.type, len1))
            elif len1 > 1:
                self.throw(node, err.CannotUnpack(value.type, len1))

            if len1 == 1:
                self.assign(lvalue, exprs[0], value)
            else:
                for i, expr in enumerate(exprs):
                    self.assign(lvalue, expr, self.extract(value, i))

    def compileStmtAssgExpr(self, node):
        exprs = node['exprs']
        op = node['op']
        ptr = self.lvalue(node, exprs[0])
        left = self.builder.load(ptr)

        if op == '??':
            with self.builder.if_then(self.builder.icmp_unsigned('==', left, vNull())):
                right = self.compile(exprs[1])
                if not left.type.isNullable() or not can_cast(left.type.subtype, right.type):
                    self.throw(node, err.NoBinaryOperator(op, left.type, right.type))
                self.builder.store(self.nullable(right), ptr)
        else:
            right = self.compile(exprs[1])
            value = self.binaryop(node, op, left, right)
            self.builder.store(value, ptr)

    def compileStmtAppend(self, node):
        # Special instruction for array comprehension.
        array = self.compile(node['array'])
        length = self.extract(array, 1)
        index = self.compile(node['index'])

        with self.builder.if_then(self.builder.icmp_signed('==', index, length)):
            length = self.builder.shl(length, vInt(1))
            memory = self.realloc(self.extract(array, 0), length)
            self.insert(memory, array, 0)
            self.insert(length, array, 1)

        value = self.compile(node['expr'])
        self.builder.store(value, self.builder.gep(self.extract(array, 0), [index]))

        self.inc(self.lvalue(node, node['index']))

    def compileStmtIf(self, node):
        exprs = node['exprs']
        blocks = node['blocks']

        with self.block() as (label_start, label_end):
            initialized_vars = []

            def emitIfElse(index):
                if len(exprs) == index:
                    if len(blocks) > index:
                        with self.local():
                            self.compile(blocks[index])
                    return

                expr = exprs[index]
                cond = self.cast(expr, self.compile(expr), tBool)

                label_if = self.builder.append_basic_block()
                label_else = self.builder.append_basic_block()
                self.builder.cbranch(cond, label_if, label_else)

                with self.builder._branch_helper(label_if, label_end):
                    with self.local():
                        self.compile(blocks[index])
                        initialized_vars.append(self.initialized)

                with self.builder._branch_helper(label_else, label_end):
                    emitIfElse(index+1)

            emitIfElse(0)

            if len(blocks) > len(exprs):  # there is an `else` statement
                self.initialized.update(set.intersection(*initialized_vars))

    def compileStmtWhile(self, node):
        with self.block() as (label_start, label_end):
            expr = node['expr']
            cond = self.cast(expr, self.compile(expr), tBool)

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
            cond = self.cast(expr, self.compile(expr), tBool)

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
                if type not in (tInt, tFloat, tChar):
                    self.throw(iterable, err.UnknownType())
                if len(values) > 1:
                    values[1] = self.cast(iterable, values[1], type)
                if step.type != type:
                    if type == tFloat:
                        step = self.builder.sitofp(step, type)
                    else:
                        self.cast(iterable, step, tInt)
                        if type == tChar:
                            step = self.builder.trunc(step, type)
                if type == tFloat:
                    cmp = self.builder.fcmp_ordered
                    desc = cmp('<', step, vFloat(0))
                else:
                    cmp = self.builder.icmp_signed
                    desc = cmp('<', step, vInt(0))
                index = self.builder.alloca(type)
                start = values[0]
                if len(values) == 1:
                    cond = lambda v: vTrue
                elif iterable['inclusive']:
                    cond = lambda v: self.builder.select(desc, cmp('>=', v, values[1]), cmp('<=', v, values[1]))
                else:
                    cond = lambda v: self.builder.select(desc, cmp('>', v, values[1]), cmp('<', v, values[1]))
                getter = lambda v: v
            else:
                value = self.compile(iterable)
                if value.type.isString():
                    types.append(tChar)
                elif value.type.isArray():
                    types.append(value.type.subtype)
                else:
                    self.throw(node, err.NotIterable(value.type))
                desc = self.builder.icmp_signed('<', step, vInt(0))
                index = self.builder.alloca(tInt)
                array = self.extract(value, 0)
                length = self.extract(value, 1)
                end1 = self.builder.sub(length, vInt(1))
                end2 = vInt(0)
                start = self.builder.select(desc, end1, end2)
                cond = lambda v: self.builder.select(desc, self.builder.icmp_signed('>=', v, end2), self.builder.icmp_signed('<=', v, end1))
                getter = lambda v: self.builder.load(self.builder.gep(array, [v]))

            self.builder.store(start, index)
            steps.append(step)
            indices.append(index)
            conditions.append(cond)
            getters.append(getter)

        _steps = lmap(self.compile, node.get('steps', [])) or [vInt(1)]
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
                    self.throw(node, err.CannotUnpack(tTuple(types), len(vars)))

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

    def compileStmtFunc(self, node):
        id = node['id']

        args = []
        expect_default = False
        for arg in node['args']:
            type = arg['type']
            name = arg['name']
            default = arg.get('default')
            if default:
                with self.no_output():
                    self.cast(default, self.compile(default), type)
                expect_default = True
            elif expect_default:
                self.throw(arg, err.MissingDefault(name))
            args.append(Arg(type, name, default))

        ret_type = node['ret']

        func_type = tFunc(args, ret_type)
        func_def = node['block']

        if not func_def:  # `extern`
            func_ptr = ll.GlobalVariable(self.module, func_type, self.module.get_unique_name('f.'+id))
            self.env[id] = func_ptr
            self.initialized.add(id)
            return

        func = ll.Function(self.module, func_type.pointee, self.module.get_unique_name('def.'+id))
        func_ptr = ll.GlobalVariable(self.module, func_type, self.module.get_unique_name(id))
        func_ptr.initializer = func
        self.env[id] = func_ptr
        self.initialized.add(id)

        prev_label = self.builder.basic_block
        entry = func.append_basic_block('entry')
        self.builder.position_at_end(entry)

        with self.local():
            self.env['#return'] = ret_type
            self.env.pop('#continue', None)
            self.env.pop('#break', None)

            for (type, id, default), value in zip(args, func.args):
                ptr = self.declare(node, type, id, redeclare=True, initialize=True)
                self.env[id] = ptr
                self.builder.store(value, ptr)

            self.compile(func_def)

            if ret_type == tVoid:
                self.builder.ret_void()
            else:
                if '#return' not in self.initialized:
                    self.throw(node, err.MissingReturn(id))
                self.builder.ret(ret_type.default())

        self.builder.position_at_end(prev_label)

    def compileStmtReturn(self, node):
        try:
            type = self.env['#return']
        except KeyError:
            self.throw(node, err.UnexpectedStatement('return'))

        self.initialized.add('#return')

        expr = node['expr']
        if expr:
            value = self.cast(node, self.compile(expr), type)
        elif type != tVoid:
            self.throw(node, err.IllegalAssignment(tVoid, type))

        if type == tVoid:
            self.builder.ret_void()
        else:
            self.builder.ret(value)


    ### Expressions ###

    def compileExprArray(self, node):
        exprs = node['exprs']
        values = self.unify(node, *map(self.compile, exprs))
        subtype = values[0].type if values else tUnknown
        return self.array(subtype, values)

    def compileExprArrayComprehension(self, node):
        expr = node['expr']

        value, array, index = [{
            'node': 'AtomId',
            'id': f'__cpr_{name}{len(self.env)}',
        } for name in ['value', 'array', 'index']]

        stmt = inner_stmt = {
            'node': 'StmtAssg',
            'lvalues': [{
                'node': 'Lvalue',
                'exprs': [value],
            }],
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
            with self.no_output(keep_env=True):
                self.compile(stmt)
                type = self.compile(value).type

        with self.local():
            self.assign(node, array, self.array(type, [], length=vInt(4)))
            self.assign(node, index, vInt(0))

            inner_stmt['node'] = 'StmtAppend'
            inner_stmt['array'] = array
            inner_stmt['index'] = index

            self.compile(stmt)

            result = self.compile(array)
            length = self.compile(index)
            self.insert(length, result, 1)

        return result

    def compileExprIndex(self, node):
        exprs = node['exprs']

        if node.get('safe'):
            collection = self.compile(exprs[0])
            return self.safe(node, collection, lambda: self.nullable(self.builder.load(self.index(node, self.extract(collection), self.compile(exprs[1])))), vNull)

        return self.builder.load(self.index(node, *map(self.compile, exprs)))

    def compileExprSlice(self, node):
        slice = node['slice']

        array, length, start, end, step, index = [{
            'node': 'AtomId',
            'id': f'__slice_{name}{len(self.env)}',
        } for name in ['array', 'length', 'start', 'end', 'step', 'index']]

        with self.local():
            collection = self.compile(node['expr'])
            type = collection.type

            if not type.isCollection():
                self.throw(node, err.NotIndexable(type))

            self.assign(node, array, collection)
            self.assign(node, length, self.expr('{t}.length', t=array['id']))

            if slice[2] is None:
                self.assign(node, step, vInt(1))
            else:
                self.assign(node, step, self.cast(slice[2], self.compile(slice[2]), tInt))

            if slice[0] is None:
                self.assign(node, start, self.expr('{c} > 0 ? 0 : {l}', c=step['id'], l=length['id']))
            else:
                self.assign(node, start, self.cast(slice[0], self.compile(slice[0]), tInt))
                self.assign(node, start, self.expr('{a} < 0 ? {a} + {l} : {a}', a=start['id'], l=length['id']))
            self.assign(node, start, self.expr('{a} < 0 ? 0 : {a} > {l} ? {l} : {a}', a=start['id'], l=length['id']))

            if slice[1] is None:
                self.assign(node, end, self.expr('{c} > 0 ? {l} : 0', c=step['id'], l=length['id']))
            else:
                self.assign(node, end, self.cast(slice[1], self.compile(slice[1]), tInt))
                self.assign(node, end, self.expr('{b} < 0 ? {b} + {l} : {b}', b=end['id'], l=length['id']))
            self.assign(node, end, self.expr('{b} < 0 ? 0 : {b} > {l} ? {l} : {b}', b=end['id'], l=length['id']))

            self.assign(node, start, self.expr('{c} < 0 ? {a} - 1 : {a}', a=start['id'], c=step['id']))
            self.assign(node, end, self.expr('{c} < 0 ? {b} - 1 : {b}', b=end['id'], c=step['id']))

            result = self.expr('[{t}[{i}] for {i} in {a}...{b} step {c}]', t=array['id'], a=start['id'], b=end['id'], c=step['id'], i=index['id'])

        # `CharArray_asString` is used directly, because `.join` would copy the array redundantly.
        return self.builder.call(self.get(node, 'CharArray_asString'), [result]) if type == tString else result

    def compileExprAttr(self, node):
        expr = node['expr']
        attr = node['attr']

        if node.get('safe'):
            obj = self.compile(expr)
            return self.safe(node, obj, lambda: self.nullable(self.attr(node, self.extract(obj), attr)), vNull)

        obj, value = self.attribute(node, expr, attr)
        return value

    def compileExprCall(self, node):
        expr = node['expr']

        def call(obj, func):
            if not func.type.isFunc():
                self.throw(node, err.NotFunction(func.type))

            args = []
            pos_args = {}
            named_args = {}

            for i, call_arg in enumerate(node['args']):
                name = call_arg['name']
                expr = call_arg['expr']
                if name:
                    if name in named_args:
                        self.throw(node, err.RepeatedArgument(name))
                    named_args[name] = expr
                else:
                    if named_args:
                        self.throw(node, err.ExpectedNamedArgument())
                    pos_args[i] = expr

            func_args = func.type.args[1:] if obj else func.type.args
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
                    id = self.module.get_unique_name('lambda')
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
                    value = self.get(expr, id)
                else:
                    value = self.compile(expr)

                value = self.cast(expr, value, func_arg.type)
                args.append(value)

            if named_args:
                self.throw(node, err.UnexpectedArgument(next(iter(named_args))))
            if pos_args:
                self.throw(node, err.TooManyArguments(func.type))

            if obj:
                args.insert(0, obj)

            return self.builder.call(func, args)

        if expr['node'] == 'ExprAttr':
            attr = expr['attr']

            if expr.get('safe'):
                obj = self.compile(expr['expr'])

                def callback():
                    value = self.extract(obj)
                    func = self.attr(node, value, attr)
                    return self.nullable(call(value, func))

                return self.safe(node, obj, callback, vNull)
            else:
                obj, func = self.attribute(expr, expr['expr'], attr)
        else:
            obj = None
            func = self.compile(expr)

        return call(obj, func)

    def compileExprUnaryOp(self, node):
        return self.unaryop(node, node['op'], self.compile(node['expr']))

    def compileExprBinaryOp(self, node):
        op = node['op']
        exprs = node['exprs']

        if op == '??':
            left = self.compile(exprs[0])

            def callback():
                right = self.compile(exprs[1])
                if not can_cast(left.type.subtype, right.type):
                    self.throw(node, err.NoBinaryOperator(op, left.type, right.type))
                return right

            return self.safe(node, left, lambda: self.extract(left), callback)

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

        values = [self.compile(exprs[0])]

        with self.block() as (label_start, label_end):            
            self.builder.position_at_end(label_end)
            phi = self.builder.phi(tBool)
            self.builder.position_at_end(label_start)

            def emitIf(index):
                values.append(self.compile(exprs[index+1]))
                cond = self.cmp(node, ops[index], values[index], values[index+1])

                if len(exprs) == index+2:
                    phi.add_incoming(cond, self.builder.basic_block)
                    self.builder.branch(label_end)
                    return

                phi.add_incoming(vFalse, self.builder.basic_block)
                label_if = self.builder.function.append_basic_block()
                self.builder.cbranch(cond, label_if, label_end)

                with self.builder._branch_helper(label_if, label_end):
                    emitIf(index+1)

            emitIf(0)

        return phi

    def compileExprLogicalOp(self, node):
        exprs = node['exprs']
        op = node['op']

        cond1 = self.compile(exprs[0])
        
        with self.block() as (label_start, label_end):
            label_if = self.builder.function.append_basic_block()
    
            if op == 'and':
                self.builder.cbranch(cond1, label_if, label_end)
            elif op == 'or':
                self.builder.cbranch(cond1, label_end, label_if)
    
            self.builder.position_at_end(label_end)
            phi = self.builder.phi(tBool)
            if op == 'and':
                phi.add_incoming(vFalse, label_start)
            elif op == 'or':
                phi.add_incoming(vTrue, label_start)
    
            with self.builder._branch_helper(label_if, label_end):
                cond2 = self.compile(exprs[1])
                if not cond1.type == cond2.type == tBool:
                    self.throw(node, err.NoBinaryOperator(op, cond1.type, cond2.type))
                phi.add_incoming(cond2, self.builder.basic_block)

        return phi

    def compileExprCond(self, node):
        exprs = node['exprs']
        cond, *values = map(self.compile, exprs)
        cond = self.cast(exprs[0], cond, tBool)
        values = self.unify(node, *values)
        return self.builder.select(cond, *values)

    def compileExprLambda(self, node):
        self.throw(node, err.IllegalLambda())

    def compileExprTuple(self, node):
        values = lmap(self.compile, node['exprs'])
        return self.tuple(values)


    ### Atoms ###

    def compileAtomInt(self, node):
        return vInt(node['int'])

    def compileAtomFloat(self, node):
        return vFloat(node['float'])

    def compileAtomBool(self, node):
        return vBool(node['bool'])

    def compileAtomChar(self, node):
        return vChar(node['char'])

    def compileAtomString(self, node):
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
        return vNull()

    def compileAtomId(self, node):
        return self.get(node, node['id'])

    def compileAtomStub(self, node):
        self.throw(node, err.IllegalLambda())
