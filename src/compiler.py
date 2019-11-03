
import ast
import re
from contextlib import contextmanager

from .antlr.PyxellParser import PyxellParser
from .antlr.PyxellVisitor import PyxellVisitor
from .errors import PyxellError as err
from .parsing import parse_expr
from .types import *


class CustomIRBuilder(ll.IRBuilder):

    def _set_terminator(self, term):
        self.basic_block.terminator = None  # to prevent llvmlite's AssertionError
        super()._set_terminator(term)


class Unit:

    def __init__(self, env, initialized):
        self.env = env
        self.initialized = initialized


class PyxellCompiler(PyxellVisitor):

    def __init__(self):
        self.units = {}
        self._unit = None
        self.builder = CustomIRBuilder()
        self.module = ll.Module()
        self.main = ll.Function(self.module, tFunc([], tInt).pointee, 'main')
        self.builder.position_at_end(self.main.append_basic_block('entry'))
        self.builtins = {
            'malloc': ll.Function(self.module, tFunc([tInt], tPtr()).pointee, 'malloc'),
            'memcpy': ll.Function(self.module, tFunc([tPtr(), tPtr(), tInt]).pointee, 'memcpy'),
            'putchar': ll.Function(self.module, tFunc([tChar]).pointee, 'putchar'),
        }

    def llvm(self):
        if not self.builder.basic_block.is_terminated:
            self.builder.ret(ll.Constant(tInt, 0))
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
    def no_output(self):
        dummy_module = ll.Module()
        dummy_func = ll.Function(dummy_module, tFunc([]).pointee, 'dummy')
        dummy_label = dummy_func.append_basic_block('dummy')
        prev_label = self.builder.basic_block
        self.builder.position_at_end(dummy_label)
        yield
        self.builder.position_at_end(prev_label)

    @contextmanager
    def block(self):
        label_start = self.builder.append_basic_block()
        self.builder.branch(label_start)
        self.builder.position_at_end(label_start)
        label_end = ll.Block(self.builder.function)
        yield label_start, label_end
        self.builder.function.blocks.append(label_end)
        self.builder.position_at_end(label_end)

    def throw(self, ctx, msg):
        raise err(msg, ctx.start.line, ctx.start.column+1)

    def get(self, ctx, id, load=True):
        id = str(id)
        if id not in self.env:
            self.throw(ctx, err.UndeclaredIdentifier(id))
        if id not in self.initialized:
            self.throw(ctx, err.UninitializedIdentifier(id))
        ptr = self.env[id]
        return self.builder.load(ptr) if load else ptr

    def extract(self, value, *indices):
        return self.builder.load(self.builder.gep(value, [vInt(0), *map(vIndex, indices)]))

    def index(self, ctx, *exprs, lvalue=False):
        collection, index = [self.visit(expr) for expr in exprs]

        if collection.type.isCollection():
            if lvalue and not collection.type.isArray():
                self.throw(exprs[0], err.NotLvalue())

            index = self.cast(exprs[1], index, tInt)
            length = self.extract(collection, 1)
            cmp = self.builder.icmp_signed('>=', index, vInt(0))
            index = self.builder.select(cmp, index, self.builder.add(index, length))
            return self.builder.gep(self.extract(collection, 0), [index])

        self.throw(ctx, err.NotIndexable(collection.type))

    def attribute(self, ctx, expr, attr):
        attr = str(attr)

        if isinstance(expr, PyxellParser.ExprAtomContext):
            atom = expr.atom()
            if isinstance(atom, PyxellParser.AtomIdContext):
                id = str(atom.ID())
                if id in self.units:
                    with self.unit(id):
                        return None, self.get(ctx, attr)

        obj = self.visit(expr)
        type = obj.type
        value = None
        
        if type == tInt:
            if attr == 'toString':
                value = self.get(ctx, 'Int_toString')
            elif attr == 'toFloat':
                value = self.get(ctx, 'Int_toFloat')

        elif type == tFloat:
            if attr == 'toString':
                value = self.get(ctx, 'Float_toString')
            elif attr == 'toInt':
                value = self.get(ctx, 'Float_toInt')

        elif type == tBool:
            if attr == 'toString':
                value = self.get(ctx, 'Bool_toString')
            elif attr == 'toInt':
                value = self.get(ctx, 'Bool_toInt')
            elif attr == 'toFloat':
                value = self.get(ctx, 'Bool_toFloat')

        elif type == tChar:
            if attr == 'toString':
                value = self.get(ctx, 'Char_toString')
            elif attr == 'toInt':
                value = self.get(ctx, 'Char_toInt')
            elif attr == 'toFloat':
                value = self.get(ctx, 'Char_toFloat')

        elif type.isCollection():
            if attr == 'length':
                value = self.extract(obj, 1)
            elif type == tString:
                if attr == 'toString':
                    value = self.get(ctx, 'String_toString')
                elif attr == 'toArray':
                    value = self.get(ctx, 'String_toArray')
                elif attr == 'toInt':
                    value = self.get(ctx, 'String_toInt')
                elif attr == 'toFloat':
                    value = self.get(ctx, 'String_toFloat')
            elif type.isArray():
                if attr == 'join':
                    if type.subtype == tChar:
                        value = self.get(ctx, 'CharArray_join')
                    elif type.subtype == tString:
                        value = self.get(ctx, 'StringArray_join')

        elif type.isTuple() and len(attr) == 1:
            index = ord(attr) - ord('a')
            if 0 <= index < len(type.elements):
                value = self.extract(obj, index)

        if value is None:
            self.throw(ctx, err.NoAttribute(type, attr))

        return obj, value

    def call(self, name, *values):
        func = self.builder.load(self.env[name])
        return self.builder.call(func, values)

    def cast(self, ctx, value, type):
        if not types_compatible(value.type, type):
            self.throw(ctx, err.IllegalAssignment(value.type, type))
        return value if value.type == type else self.builder.bitcast(value, type)

    def unify(self, ctx, *values):
        if not values:
            return []
        values = list(values)

        type = values[0].type
        for value in values[1:]:
            type = unify_types(value.type, type)
            if type is None:
                self.throw(ctx, err.UnknownType())

        for i, value in enumerate(values):
            if value.type == tInt and type == tFloat:
                values[i] = self.builder.sitofp(value, type)
            else:
                values[i] = self.cast(ctx, value, type)

        return values

    def declare(self, ctx, type, id, redeclare=False, initialize=False):
        if type == tVoid:
            self.throw(ctx, err.InvalidDeclaration(type))
        if type.isUnknown():
            self.throw(ctx, err.UnknownType())

        id = str(id)
        if id in self.env and not redeclare:
            self.throw(ctx, err.RedeclaredIdentifier(id))

        if self.builder.basic_block.parent._name == 'main':
            ptr = ll.GlobalVariable(self.module, type, self.module.get_unique_name(id))
            ptr.initializer = type.default()
        else:
            ptr = self.builder.alloca(type)

        self.env[id] = ptr
        if initialize:
            self.initialized.add(id)

        return ptr

    def lvalue(self, ctx, expr, declare=None, initialize=False):
        if isinstance(expr, PyxellParser.ExprAtomContext):
            atom = expr.atom()
            if not isinstance(atom, PyxellParser.AtomIdContext):
                self.throw(ctx, err.NotLvalue())

            id = str(atom.ID())
            if id not in self.env:
                if declare is None:
                    self.throw(ctx, err.UndeclaredIdentifier(id))
                self.declare(ctx, declare, id)

            if initialize:
                self.initialized.add(id)

            return self.env[id]

        elif isinstance(expr, PyxellParser.ExprIndexContext):
            return self.index(ctx, *expr.expr(), lvalue=True)

        self.throw(ctx, err.NotLvalue())

    def assign(self, ctx, expr, value):
        ptr = self.lvalue(ctx, expr, declare=value.type, initialize=True)
        value = self.cast(ctx, value, ptr.type.pointee)
        self.builder.store(value, ptr)

    def inc(self, ptr, step=vInt(1)):
        add = self.builder.fadd if ptr.type.pointee == tFloat else self.builder.add
        self.builder.store(add(self.builder.load(ptr), step), ptr)

    def sizeof(self, type, length=vInt(1)):
        return self.builder.ptrtoint(self.builder.gep(vNull(type), [length]), tInt)

    def malloc(self, type, length=vInt(1)):
        size = self.sizeof(type.pointee, length)
        ptr = self.builder.call(self.builtins['malloc'], [size])
        return self.builder.bitcast(ptr, type)

    def memcpy(self, dest, src, length):
        type = dest.type
        dest = self.builder.bitcast(dest, tPtr())
        src = self.builder.bitcast(src, tPtr())
        size = self.sizeof(type.pointee, length)
        return self.builder.call(self.builtins['memcpy'], [dest, src, size])

    def unaryop(self, ctx, op, value):
        if op in ('+', '-'):
            types = [tInt, tFloat]
        elif op == '~':
            types = [tInt]
        elif op == 'not':
            types = [tBool]

        if value.type not in types:
            self.throw(ctx, err.NoUnaryOperator(op, value.type))

        if op == '+':
            return value
        elif op == '-':
            if value.type == tInt:
                return self.builder.sub(vInt(0), value)
            elif value.type == tFloat:
                return self.builder.fsub(vFloat(0), value)
        elif op in ('~', 'not'):
            return self.builder.not_(value)

    def binaryop(self, ctx, op, left, right):
        if left.type in (tInt, tFloat) and right.type in (tInt, tFloat):
            left, right = self.unify(ctx, left, right)

        if op == '^':
            if left.type == right.type == tInt:
                return self.call('Int_pow', left, right)

            elif left.type == right.type == tFloat:
                return self.call('Float_pow', left, right)

            else:
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

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

                value = self.malloc(type)
                self.builder.store(dest, self.builder.gep(value, [vInt(0), vIndex(0)]))
                self.builder.store(length, self.builder.gep(value, [vInt(0), vIndex(1)]))
                return value

            elif left.type == tInt and right.type.isCollection():
                return self.binaryop(ctx, op, right, left)

            else:
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

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
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

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
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

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

                value = self.malloc(type)
                self.builder.store(array, self.builder.gep(value, [vInt(0), vIndex(0)]))
                self.builder.store(length, self.builder.gep(value, [vInt(0), vIndex(1)]))
                return value

            elif left.type == tString and right.type == tChar:
                return self.binaryop(ctx, op, left, self.call('Char_toString', right))

            elif left.type == tChar and right.type == tString:
                return self.binaryop(ctx, op, self.call('Char_toString', left), right)

            else:
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

        elif op == '-':
            if left.type == right.type == tInt:
                return self.builder.sub(left, right)

            elif left.type == right.type == tFloat:
                return self.builder.fsub(left, right)

            else:
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

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
                self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

    def cmp(self, ctx, op, left, right):
        try:
            left, right = self.unify(ctx, left, right)
        except err:
            self.throw(ctx, err.NotComparable(left.type, right.type))

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
                cond = self.cmp(ctx, op + '=' if op in ('<', '>') else op, *values)

                if op == '!=':
                    self.builder.cbranch(cond, label_true, label_cont)
                else:
                    self.builder.cbranch(cond, label_cont, label_false)

                self.builder.function.blocks.append(label_cont)
                self.builder.position_at_end(label_cont)

                if op in ('<=', '>=', '<', '>'):
                    label_cont = ll.Block(self.builder.function)

                    cond2 = self.cmp(ctx, '!=', *values)
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
                    cond = self.cmp(ctx, op + '=' if op in ('<', '>') else op, *values)

                    if op == '!=':
                        self.builder.cbranch(cond, label_true, label_cont)
                    else:
                        self.builder.cbranch(cond, label_cont, label_false)

                    self.builder.function.blocks.append(label_cont)
                    self.builder.position_at_end(label_cont)

                    if op in ('<=', '>=', '<', '>'):
                        label_cont = ll.Block(self.builder.function)

                        cond2 = self.cmp(ctx, '!=', *values)
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
            self.throw(ctx, err.NotComparable(left.type, right.type))

    def write(self, str):
        for char in str:
            self.builder.call(self.builtins['putchar'], [vChar(char)])

    def print(self, ctx, value):
        if value.type == tInt:
            self.call('writeInt', value)

        elif value.type == tFloat:
            self.call('writeFloat', value)

        elif value.type == tBool:
            self.call('writeBool', value)

        elif value.type == tChar:
            self.call('writeChar', value)

        elif value.type.isString():
            self.call('write', value)

        elif value.type.isArray():
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
                self.print(ctx, self.builder.load(elem))

                self.inc(index)

                self.builder.branch(label_start)

            self.write(']')

        elif value.type.isTuple():
            for i in range(len(value.type.elements)):
                if i > 0:
                    self.write(' ')
                self.print(ctx, self.extract(value, i))

        elif value.type == tUnknown:
            pass

        else:
            self.throw(ctx, err.NotPrintable(value.type))

    def string(self, lit):
        const = ll.Constant(ll.ArrayType(tChar, len(lit)), [vChar(c) for c in lit])
        result = self.malloc(tString)

        array = ll.GlobalVariable(self.module, const.type, self.module.get_unique_name('str'))
        array.global_constant = True
        array.initializer = const
        memory = self.builder.gep(array, [vInt(0), vInt(0)])

        self.builder.store(memory, self.builder.gep(result, [vInt(0), vIndex(0)]))
        self.builder.store(vInt(const.type.count), self.builder.gep(result, [vInt(0), vIndex(1)]))

        return result

    def array(self, subtype, values):
        type = tArray(subtype)
        result = self.malloc(type)

        memory = self.malloc(tPtr(subtype), vInt(len(values)))
        for i, value in enumerate(values):
            self.builder.store(value, self.builder.gep(memory, [vInt(i)]))

        self.builder.store(memory, self.builder.gep(result, [vInt(0), vIndex(0)]))
        self.builder.store(vInt(len(values)), self.builder.gep(result, [vInt(0), vIndex(1)]))

        return result

    def tuple(self, values):
        if len(values) == 1:
            return values[0]

        type = tTuple([value.type for value in values])
        result = self.malloc(type)

        for i, value in enumerate(values):
            self.builder.store(value, self.builder.gep(result, [vInt(0), vIndex(i)]))

        return result


    ### Program ###

    def visitProgram(self, ctx, unit=None):
        self.units[unit] = Unit({}, set())
        with self.unit(unit):
            if unit != 'std':
                self.env = self.units['std'].env.copy()
                self.initialized = self.units['std'].initialized.copy()
            self.visitChildren(ctx)


    ### Statements ###

    def visitStmtUse(self, ctx):
        name = ctx.name.text
        if name not in self.units:
            self.throw(ctx, err.InvalidModule(name))

        unit = self.units[name]
        if ctx.only:
            for id in ctx.only.ID():
                id = str(id)
                if id not in unit.env:
                    self.throw(ctx.only, err.UndeclaredIdentifier(id))
                self.env[id] = unit.env[id]
                if id in unit.initialized:
                    self.initialized.add(id)
        elif ctx.hiding:
            hidden = set()
            for id in ctx.hiding.ID():
                id = str(id)
                if id not in unit.env:
                    self.throw(ctx.hiding, err.UndeclaredIdentifier(id))
                hidden.add(id)
            self.env.update({x: unit.env[x] for x in unit.env.keys() - hidden})
            self.initialized.update(unit.initialized - hidden)
        elif ctx.as_:
            self.units[ctx.as_.text] = unit
        else:
            self.env.update(unit.env)
            self.initialized.update(unit.initialized)

    def visitStmtPrint(self, ctx):
        expr = ctx.tuple_expr()
        if expr:
            value = self.visit(expr)
            self.print(expr, value)
        self.write('\n')

    def visitStmtDecl(self, ctx):
        type = self.visit(ctx.typ())
        id = ctx.ID()
        expr = ctx.tuple_expr()
        ptr = self.declare(ctx, type, id, initialize=bool(expr))
        if expr:
            value = self.cast(ctx, self.visit(expr), type)
            self.builder.store(value, ptr)

    def visitStmtAssg(self, ctx):
        value = self.visit(ctx.tuple_expr())

        for lvalue in ctx.lvalue():
            exprs = lvalue.expr()
            len1 = len(exprs)

            if value.type.isTuple():
                len2 = len(value.type.elements)
                if len1 > 1 and len1 != len2:
                    self.throw(ctx, err.CannotUnpack(value.type, len1))
            elif len1 > 1:
                self.throw(ctx, err.CannotUnpack(value.type, len1))

            if len1 == 1:
                self.assign(lvalue, exprs[0], value)
            else:
                for i, expr in enumerate(exprs):
                    self.assign(lvalue, expr, self.extract(value, i))

    def visitStmtAssgExpr(self, ctx):
        ptr = self.lvalue(ctx, ctx.expr(0))
        value = self.binaryop(ctx, ctx.op.text, self.builder.load(ptr), self.visit(ctx.expr(1)))
        self.builder.store(value, ptr)

    def visitStmtIf(self, ctx):
        exprs = ctx.expr()
        blocks = ctx.do_block()

        with self.block() as (label_start, label_end):
            initialized_vars = []

            def emitIfElse(index):
                if len(exprs) == index:
                    if len(blocks) > index:
                        with self.local():
                            self.visit(blocks[index])
                    return

                expr = exprs[index]
                cond = self.cast(expr, self.visit(expr), tBool)

                label_if = self.builder.append_basic_block()
                label_else = self.builder.append_basic_block()
                self.builder.cbranch(cond, label_if, label_else)

                with self.builder._branch_helper(label_if, label_end):
                    with self.local():
                        self.visit(blocks[index])
                        initialized_vars.append(self.initialized)

                with self.builder._branch_helper(label_else, label_end):
                    emitIfElse(index+1)

            emitIfElse(0)

            if len(blocks) > len(exprs):  # there is an `else` statement
                self.initialized.update(set.intersection(*initialized_vars))

    def visitStmtWhile(self, ctx):
        with self.block() as (label_start, label_end):
            expr = ctx.expr()
            cond = self.cast(expr, self.visit(expr), tBool)

            label_while = self.builder.append_basic_block()
            self.builder.cbranch(cond, label_while, label_end)
            self.builder.position_at_end(label_while)

            with self.local():
                self.env['#continue'] = label_start
                self.env['#break'] = label_end

                self.visit(ctx.do_block())

            self.builder.branch(label_start)

    def visitStmtUntil(self, ctx):
        with self.block() as (label_start, label_end):
            with self.local():
                self.env['#continue'] = label_start
                self.env['#break'] = label_end

                self.visit(ctx.do_block())

            expr = ctx.expr()
            cond = self.cast(expr, self.visit(expr), tBool)

            self.builder.cbranch(cond, label_end, label_start)

    def visitStmtFor(self, ctx):
        exprs = ctx.tuple_expr()
        vars = exprs[0].expr()
        iterables = exprs[1].expr()

        types = []
        steps = []
        indices = []
        conditions = []
        getters = []

        def prepare(iterable, step):  # must be a function so that lambdas work properly

            if isinstance(iterable, PyxellParser.ExprRangeContext):
                values = [self.visit(expr) for expr in iterable.expr()]
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
                elif iterable.dots.text == '..':
                    cond = lambda v: self.builder.select(desc, cmp('>=', v, values[1]), cmp('<=', v, values[1]))
                elif iterable.dots.text == '...':
                    cond = lambda v: self.builder.select(desc, cmp('>', v, values[1]), cmp('<', v, values[1]))
                getter = lambda v: v
            else:
                value = self.visit(iterable)
                if value.type.isString():
                    types.append(tChar)
                elif value.type.isArray():
                    types.append(value.type.subtype)
                else:
                    self.throw(ctx, err.NotIterable(value.type))
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

        _steps = [vInt(1)]
        if len(exprs) > 2:
            _steps = [self.visit(expr) for expr in exprs[2].expr()]
        if len(_steps) == 1:
            _steps *= len(iterables)
        if len(exprs) > 2 and len(_steps) != len(iterables):
            self.throw(ctx, err.InvalidLoopStep())

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
                    self.assign(exprs[0], vars[0], tuple)
                elif len(vars) > 1 and len(types) == 1:
                    for i, var in enumerate(vars):
                        tuple = getters[0](self.builder.load(indices[0]))
                        self.assign(exprs[0], var, self.extract(tuple, i))
                elif len(vars) == len(types):
                    for var, index, getter in zip(vars, indices, getters):
                        self.assign(exprs[0], var, getter(self.builder.load(index)))
                else:
                    self.throw(exprs[0], err.CannotUnpack(tTuple(types), len(vars)))

                self.visit(ctx.do_block())

            self.builder.function.blocks.append(label_cont)
            self.builder.branch(label_cont)
            self.builder.position_at_end(label_cont)

            for index, step, type in zip(indices, steps, types):
                self.inc(index, step)

            self.builder.branch(label_start)

    def visitStmtLoopControl(self, ctx):
        stmt = ctx.s.text  # `break` / `continue`

        try:
            label = self.env[f'#{stmt}']
        except KeyError:
            self.throw(ctx, err.UnexpectedStatement(stmt))

        self.builder.branch(label)

    def visitStmtFunc(self, ctx):
        id = str(ctx.ID())

        args = []
        expect_default = False
        for arg in ctx.func_arg():
            type = self.visit(arg.typ())
            name = str(arg.ID())
            default = arg.default
            if default:
                with self.no_output():
                    self.cast(default, self.visit(default), type)
                expect_default = True
            elif expect_default:
                self.throw(arg, err.MissingDefault(name))
            args.append(Arg(type, name, arg.default))

        ret_type = self.visit(ctx.ret) if ctx.ret else tVoid

        func_type = tFunc(args, ret_type)
        func_def = ctx.def_block()

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
                ptr = self.declare(ctx, type, id, redeclare=True, initialize=True)
                self.env[id] = ptr
                self.builder.store(value, ptr)

            self.visit(func_def)

            if ret_type == tVoid:
                self.builder.ret_void()
            else:
                if '#return' not in self.initialized:
                    self.throw(ctx, err.MissingReturn(id))
                self.builder.ret(ret_type.default())

        self.builder.position_at_end(prev_label)

    def visitStmtReturn(self, ctx):
        try:
            type = self.env['#return']
        except KeyError:
            self.throw(ctx, err.UnexpectedStatement('return'))

        self.initialized.add('#return')

        expr = ctx.tuple_expr()
        if expr:
            value = self.cast(ctx, self.visit(expr), type)
            self.builder.ret(value)
        else:
            if type != tVoid:
                self.throw(ctx, err.IllegalAssignment(tVoid, type))
            self.builder.ret_void()


    ### Expressions ###

    def visitExprParentheses(self, ctx):
        return self.visit(ctx.tuple_expr())

    def visitExprIndex(self, ctx):
        return self.builder.load(self.index(ctx, *ctx.expr()))

    def visitExprAttr(self, ctx):
        obj, value = self.attribute(ctx, ctx.expr(), ctx.ID())
        return value

    def visitExprCall(self, ctx):
        expr = ctx.expr()

        if isinstance(expr, PyxellParser.ExprAttrContext):
            obj, func = self.attribute(expr, expr.expr(), expr.ID())
        else:
            obj = None
            func = self.visit(expr)

        if not func.type.isFunc():
            self.throw(ctx, err.NotFunction(func.type))

        args = []
        pos_args = {}
        named_args = {}

        for i, call_arg in enumerate(ctx.call_arg()):
            name = call_arg.ID()
            expr = call_arg.expr()
            if name:
                name = str(name)
                if name in named_args:
                    self.throw(ctx, err.RepeatedArgument(name))
                named_args[name] = expr
            else:
                if named_args:
                    self.throw(ctx, err.ExpectedNamedArgument())
                pos_args[i] = expr

        func_args = func.type.args[1:] if obj else func.type.args
        for i, func_arg in enumerate(func_args):
            name = func_arg.name
            if name in named_args:
                if i in pos_args:
                    self.throw(ctx, err.RepeatedArgument(name))
                expr = named_args.pop(name)
            elif i in pos_args:
                expr = pos_args.pop(i)
            elif func_arg.default:
                expr = func_arg.default
            else:
                self.throw(ctx, err.TooFewArguments(func.type))

            value = self.cast(expr, self.visit(expr), func_arg.type)
            args.append(value)

        if named_args:
            self.throw(ctx, err.UnexpectedArgument(next(iter(named_args))))
        if pos_args:
            self.throw(ctx, err.TooManyArguments(func.type))

        if obj:
            args.insert(0, obj)

        return self.builder.call(func, args)

    def visitExprUnaryOp(self, ctx):
        return self.unaryop(ctx, ctx.op.text, self.visit(ctx.expr()))

    def visitExprBinaryOp(self, ctx):
        return self.binaryop(ctx, ctx.op.text, self.visit(ctx.expr(0)), self.visit(ctx.expr(1)))

    def visitExprRange(self, ctx):
        self.throw(ctx, err.UnknownType())

    def visitExprCmp(self, ctx):
        exprs = []
        ops = []
        while True:
            exprs.append(ctx.expr(0))
            ops.append(ctx.op.text)
            if not isinstance(ctx.expr(1), PyxellParser.ExprCmpContext):
                break
            ctx = ctx.expr(1)
        exprs.append(ctx.expr(1))

        values = [self.visit(exprs[0])]

        with self.block() as (label_start, label_end):            
            self.builder.position_at_end(label_end)
            phi = self.builder.phi(tBool)
            self.builder.position_at_end(label_start)

            def emitIf(index):
                values.append(self.visit(exprs[index+1]))
                cond = self.cmp(ctx, ops[index], values[index], values[index+1])

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

    def visitExprLogicalOp(self, ctx):
        op = ctx.op.text

        cond1 = self.visit(ctx.expr(0))
        
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
                cond2 = self.visit(ctx.expr(1))
                if not cond1.type == cond2.type == tBool:
                    self.throw(ctx, err.NoBinaryOperator(op, cond1.type, cond2.type))
                phi.add_incoming(cond2, self.builder.basic_block)

        return phi

    def visitExprCond(self, ctx):
        exprs = ctx.expr()
        cond, *values = [self.visit(expr) for expr in exprs]

        cond = self.cast(exprs[0], cond, tBool)
        values = self.unify(ctx, *values)

        return self.builder.select(cond, *values)

    def visitExprTuple(self, ctx):
        exprs = ctx.expr()
        values = [self.visit(expr) for expr in exprs]
        return self.tuple(values)

    def visitExprInterpolation(self, ctx):
        return self.visit(ctx.tuple_expr())


    ### Atoms ###

    def visitAtomInt(self, ctx):
        return vInt(ctx.INT())

    def visitAtomFloat(self, ctx):
        return vFloat(ctx.FLOAT())

    def visitAtomBool(self, ctx):
        return vBool(ctx.getText() == 'true')

    def visitAtomChar(self, ctx):
        lit = ast.literal_eval(str(ctx.CHAR()))
        return vChar(lit)

    def visitAtomString(self, ctx):
        lit = ast.literal_eval(str(ctx.STRING()))
        parts = re.split(r'{([^}]+)}', lit)

        if len(parts) > 1:
            lits, tags = parts[::2], parts[1::2]
            values = [None] * len(parts)

            for i, lit in enumerate(lits):
                values[i*2] = self.string(lit)

            for i, tag in enumerate(tags):
                try:
                    expr = parse_expr(tag)
                except err:
                    self.throw(ctx, err.InvalidExpression(tag))
                try:
                    obj, func = self.attribute(ctx, expr, 'toString')
                except err as e:
                    self.throw(ctx, str(e).partition(': ')[2][:-1])

                values[i*2+1] = self.builder.call(func, [obj])

            return self.call('StringArray_join', self.array(tString, values), self.string(''))

        else:
            return self.string(lit)

    def visitAtomArray(self, ctx):
        exprs = ctx.expr()
        values = self.unify(ctx, *[self.visit(expr) for expr in exprs])
        subtype = values[0].type if values else tUnknown
        return self.array(subtype, values)

    def visitAtomId(self, ctx):
        return self.get(ctx, ctx.ID())


    ### Types ###

    def visitTypePrimitive(self, ctx):
        return {
            'Void': tVoid,
            'Int': tInt,
            'Float': tFloat,
            'Bool': tBool,
            'Char': tChar,
            'String': tString,
        }[ctx.getText()]

    def visitTypeParentheses(self, ctx):
        return self.visit(ctx.typ())

    def visitTypeArray(self, ctx):
        return tArray(self.visit(ctx.typ()))

    def visitTypeTuple(self, ctx):
        types = []
        while True:
            types.append(self.visit(ctx.typ(0)))
            if not isinstance(ctx.typ(1), PyxellParser.TypeTupleContext):
                break
            ctx = ctx.typ(1)
        types.append(self.visit(ctx.typ(1)))
        return tTuple(types)

    def visitTypeFunc(self, ctx):
        types = []
        while True:
            types.append(self.visit(ctx.typ(0)))
            if not isinstance(ctx.typ(1), PyxellParser.TypeFuncContext):
                break
            ctx = ctx.typ(1)
        types.append(self.visit(ctx.typ(1)))
        return tFunc(types[:-1], types[-1])

    def visitTypeFunc0(self, ctx):
        return tFunc([], self.visit(ctx.typ()))
