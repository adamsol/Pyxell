
import ast
from contextlib import contextmanager

from .antlr.PyxellParser import PyxellParser
from .antlr.PyxellVisitor import PyxellVisitor
from .errors import PyxellError as err
from .types import *


class PyxellCompiler(PyxellVisitor):

    def __init__(self):
        self.env = {}
        self.initialized = set()
        self.builder = ll.IRBuilder()
        self.module = ll.Module()
        self.builtins = {
            'malloc': ll.Function(self.module, tFunc([tInt], tPtr()).pointee, 'malloc'),
            'memcpy': ll.Function(self.module, tFunc([tPtr(), tPtr(), tInt]).pointee, 'memcpy'),
            'write': ll.Function(self.module, tFunc([tString]).pointee, 'func.write'),
            'writeInt': ll.Function(self.module, tFunc([tInt]).pointee, 'func.writeInt'),
            'writeFloat': ll.Function(self.module, tFunc([tFloat]).pointee, 'func.writeFloat'),
            'writeBool': ll.Function(self.module, tFunc([tBool]).pointee, 'func.writeBool'),
            'writeChar': ll.Function(self.module, tFunc([tChar]).pointee, 'func.writeChar'),
            'putchar': ll.Function(self.module, tFunc([tChar]).pointee, 'putchar'),
            'Int_pow': ll.Function(self.module, tFunc([tInt, tInt], tInt).pointee, 'func.Int_pow'),
            'Float_pow': ll.Function(self.module, tFunc([tFloat, tFloat], tFloat).pointee, 'func.Float_pow'),
        }


    ### Helpers ###

    @contextmanager
    def local(self):
        env = self.env.copy()
        initialized = self.initialized.copy()
        yield
        self.env = env
        self.initialized = initialized

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

    def get(self, ctx, id):
        id = str(id)
        if id not in self.env:
            self.throw(ctx, err.UndeclaredIdentifier(id))
        if id not in self.initialized:
            self.throw(ctx, err.UninitializedIdentifier(id))
        return self.env[id]

    def index(self, ctx, *exprs):
        collection, index = [self.visit(expr) for expr in exprs]

        if collection.type.isCollection():
            index = self.cast(exprs[1], index, tInt)
            length = self.builder.extract_value(collection, [1])
            cmp = self.builder.icmp_signed('>=', index, vInt(0))
            index = self.builder.select(cmp, index, self.builder.add(index, length))
            return self.builder.gep(self.builder.extract_value(collection, [0]), [index])
        else:
            self.throw(ctx, err.NotIndexable(collection.type))

    def cast(self, ctx, value, type):
        if value.type != type:
            self.throw(ctx, err.IllegalAssignment(value.type, type))
        return value

    def unify(self, ctx, *values):
        if all(value.type == values[0].type for value in values):
            return values
        elif all(value.type in (tInt, tFloat) for value in values):
            return [(self.builder.sitofp(value, tFloat) if value.type == tInt else value) for value in values]
        else:
            self.throw(ctx, err.UnknownType())

    def declare(self, ctx, type, id, redeclare=False, initialize=False):
        if type == tVoid:
            self.throw(ctx, err.InvalidDeclaration(type))
        id = str(id)
        if id in self.env and not redeclare:
            self.throw(ctx, err.RedeclaredIdentifier(id))
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
            return self.index(ctx, *expr.expr())
        else:
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
        size = self.sizeof(type, length)
        ptr = self.builder.call(self.builtins['malloc'], [size])
        return self.builder.bitcast(ptr, tPtr(type))

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
                return self.builder.call(self.builtins['Int_pow'], [left, right])

            elif left.type == right.type == tFloat:
                return self.builder.call(self.builtins['Float_pow'], [left, right])

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

                src = self.builder.extract_value(left, [0])
                src_length = self.builder.extract_value(left, [1])
                length = self.builder.mul(src_length, right)
                dest = self.malloc(subtype, length)

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
                return self.builder.load(value)

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

                length1 = self.builder.extract_value(left, [1])
                length2 = self.builder.extract_value(right, [1])
                length = self.builder.add(length1, length2)

                array1 = self.builder.extract_value(left, [0])
                array2 = self.builder.extract_value(right, [0])
                array = self.malloc(subtype, length)

                self.memcpy(array, array1, length1)
                self.memcpy(self.builder.gep(array, [length1]), array2, length2)

                value = self.malloc(type)
                self.builder.store(array, self.builder.gep(value, [vInt(0), vIndex(0)]))
                self.builder.store(length, self.builder.gep(value, [vInt(0), vIndex(1)]))
                return self.builder.load(value)

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
        if left.type in (tInt, tFloat) and right.type in (tInt, tFloat):
            left, right = self.unify(ctx, left, right)

        if left.type != right.type:
            self.throw(ctx, err.NotComparable(left.type, right.type))

        if left.type in (tInt, tChar):
            return self.builder.icmp_signed(op, left, right)

        elif left.type == tFloat:
            return self.builder.fcmp_ordered(op, left, right)

        elif left.type == tBool:
            return self.builder.icmp_unsigned(op, left, right)

        elif left.type.isCollection():
            array1 = self.builder.extract_value(left, [0])
            array2 = self.builder.extract_value(right, [0])
            length1 = self.builder.extract_value(left, [1])
            length2 = self.builder.extract_value(right, [1])

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

                    values = [self.builder.extract_value(tuple, i) for tuple in [left, right]]
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

        else:
            self.throw(ctx, err.NotComparable(left.type, right.type))

    def write(self, str):
        for char in str:
            self.builder.call(self.builtins['putchar'], [vChar(char)])

    def print(self, ctx, value):
        if value.type == tInt:
            self.builder.call(self.builtins['writeInt'], [value])

        elif value.type == tFloat:
            self.builder.call(self.builtins['writeFloat'], [value])

        elif value.type == tBool:
            self.builder.call(self.builtins['writeBool'], [value])

        elif value.type == tChar:
            self.builder.call(self.builtins['writeChar'], [value])

        elif value.type.isString():
            self.builder.call(self.builtins['write'], [value])

        elif value.type.isArray():
            self.write('[')

            length = self.builder.extract_value(value, [1])
            index = self.builder.alloca(tInt)
            self.builder.store(vInt(0), index)

            with self.block() as (label_start, label_end):
                with self.builder.if_then(self.builder.icmp_signed('>', self.builder.load(index), vInt(0))):
                    self.write(', ')

                elem = self.builder.gep(self.builder.extract_value(value, [0]), [self.builder.load(index)])
                self.print(ctx, self.builder.load(elem))

                self.inc(index)

                cond = self.builder.icmp_signed('<', self.builder.load(index), length)
                self.builder.cbranch(cond, label_start, label_end)

            self.write(']')

        elif value.type.isTuple():
            for i in range(len(value.type.elements)):
                if i > 0:
                    self.write(' ')
                elem = self.builder.extract_value(value, [i])
                self.print(ctx, elem)

        else:
            self.throw(ctx, err.NotPrintable(value.type))

    def tuple(self, values):
        if len(values) == 1:
            return values[0]

        type = tTuple([value.type for value in values])
        tuple = self.malloc(type)

        for i, value in enumerate(values):
            ptr = self.builder.gep(tuple, [vInt(0), vIndex(i)])
            self.builder.store(value, ptr)

        return self.builder.load(tuple)


    ### Program ###

    def visitProgram(self, ctx):
        func = ll.Function(self.module, tFunc([], tInt).pointee, 'main')
        entry = func.append_basic_block('entry')
        self.builder.position_at_end(entry)
        self.visitChildren(ctx)
        self.builder.position_at_end(func.blocks[-1])
        self.builder.ret(ll.Constant(tInt, 0))


    ### Statements ###

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
                    self.assign(lvalue, expr, self.builder.extract_value(value, [i]))

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
                array = self.builder.extract_value(value, [0])
                length = self.builder.extract_value(value, [1])
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
                        self.assign(exprs[0], var, self.builder.extract_value(tuple, [i]))
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

        args = [(self.visit(arg.typ()), arg.ID()) for arg in ctx.arg()]
        arg_types = [arg[0] for arg in args]

        ret_type = self.visit(ctx.ret) if ctx.ret else tVoid

        func_type = tFunc(arg_types, ret_type)
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

            for (type, id), value in zip(args, func.args):
                ptr = self.declare(ctx, type, id, redeclare=True, initialize=True)
                self.env[id] = ptr
                self.builder.store(value, ptr)

            self.visit(ctx.def_block())

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
        value = self.visit(ctx.expr())
        id = str(ctx.ID())

        if value.type.isCollection():
            if id != "length":
                self.throw(ctx, err.NoAttribute(value.type, id))

            return self.builder.extract_value(value, [1])

        elif value.type.isTuple():
            if len(id) > 1:
                self.throw(ctx, err.NoAttribute(value.type, id))

            index = ord(id) - ord('a')
            if not 0 <= index < len(value.type.elements):
                self.throw(ctx, err.NoAttribute(value.type, id))

            return self.builder.extract_value(value, [index])

        self.throw(ctx, err.NoAttribute(value.type, id))

    def visitExprCall(self, ctx):
        exprs = ctx.expr()

        func = self.visit(exprs[0])
        if not func.type.isFunc():
            self.throw(ctx, err.NotFunction(func.type))

        exprs = exprs[1:]
        if len(exprs) < len(func.type.args):
            self.throw(ctx, err.TooFewArguments(func.type))
        if len(exprs) > len(func.type.args):
            self.throw(ctx, err.TooManyArguments(func.type))
        args = [self.cast(expr, self.visit(expr), type) for expr, type in zip(exprs, func.type.args)]

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
        values = [vChar(c) for c in lit]
        const = ll.Constant(ll.ArrayType(tChar, len(lit)), values)

        string = self.malloc(tString)

        pointer = self.builder.gep(string, [vInt(0), vIndex(0)])
        array = ll.GlobalVariable(self.module, const.type, self.module.get_unique_name('str'))
        array.global_constant = True
        array.initializer = const
        self.builder.store(self.builder.gep(array, [vInt(0), vInt(0)]), pointer)

        length = self.builder.gep(string, [vInt(0), vIndex(1)])
        self.builder.store(vInt(const.type.count), length)

        return self.builder.load(string)

    def visitAtomArray(self, ctx):
        exprs = ctx.expr()
        values = self.unify(ctx, *[self.visit(expr) for expr in exprs])

        subtype = values[0].type
        type = tArray(subtype)
        array = self.malloc(type)

        pointer = self.builder.gep(array, [vInt(0), vIndex(0)])
        memory = self.malloc(subtype, vInt(len(values)))
        for i, value in enumerate(values):
            self.builder.store(value, self.builder.gep(memory, [vInt(i)]))
        self.builder.store(memory, pointer)

        length = self.builder.gep(array, [vInt(0), vIndex(1)])
        self.builder.store(vInt(len(values)), length)

        return self.builder.load(array)

    def visitAtomId(self, ctx):
        return self.builder.load(self.get(ctx, ctx.ID()))


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
