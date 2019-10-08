
import ast
from contextlib import contextmanager

from .antlr.PyxellParser import PyxellParser
from .antlr.PyxellVisitor import PyxellVisitor
from .errors import PyxellError as err
from .types import *


class PyxellCompiler(PyxellVisitor):

    def __init__(self):
        self.env = {}
        self.builder = ll.IRBuilder()
        self.module = ll.Module()
        self.builtins = {
            'malloc': ll.Function(self.module, tFunc([tInt], tPtr()), 'malloc'),
            'write': ll.Function(self.module, tFunc([tString]), 'func.write'),
            'writeInt': ll.Function(self.module, tFunc([tInt]), 'func.writeInt'),
            'writeBool': ll.Function(self.module, tFunc([tBool]), 'func.writeBool'),
            'writeChar': ll.Function(self.module, tFunc([tChar]), 'func.writeChar'),
            'putchar': ll.Function(self.module, tFunc([tChar]), 'putchar'),
            'Int_pow': ll.Function(self.module, tFunc([tInt, tInt], tInt), 'func.Int_pow'),
        }


    ### Helpers ###

    @contextmanager
    def local(self):
        tmp = self.env.copy()
        yield
        self.env = tmp

    def throw(self, ctx, msg):
        raise err(msg, ctx.start.line, ctx.start.column+1)

    def get(self, ctx, id):
        try:
            return self.env[str(id)]
        except KeyError:
            self.throw(ctx, err.UndeclaredIdentifier(id))

    def cast(self, ctx, value, type):
        if value.type != type:
            raise self.throw(ctx, err.IllegalAssignment(value.type, type))

        return value

    def assign(self, ctx, id, value):
        id = str(id)

        try:
            var = self.env[id]
        except KeyError:
            var = self.env[id] = self.builder.alloca(value.type)
        else:
            value = self.cast(ctx, value, var.type.pointee)

        self.builder.store(value, var)

    def unaryop(self, ctx, op, value):
        if op in ('+', '-', '~'):
            type = tInt
        elif op == 'not':
            type = tBool

        if value.type != type:
            self.throw(ctx, err.NoUnaryOperator(op, value.type))

        if op == '+':
            return value
        elif op == '-':
            return self.builder.neg(value)
        elif op in ('~', 'not'):
            return self.builder.not_(value)

    def binaryop(self, ctx, op, left, right):
        if not left.type == right.type == tInt:
            self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

        if op == '^':
            return self.builder.call(self.builtins['Int_pow'], [left, right])
        elif op == '/':
            v1 = self.builder.sdiv(left, right)
            v2 = self.builder.sub(v1, vInt(1))
            v3 = self.builder.xor(left, right)
            v4 = self.builder.icmp_signed('<', v3, vInt(0))
            v5 = self.builder.select(v4, v2, v1)
            v6 = self.builder.mul(v1, right)
            v7 = self.builder.icmp_signed('!=', v6, left)
            return self.builder.select(v7, v5, v1)
        elif op == '%':
            v1 = self.builder.srem(left, right)
            v2 = self.builder.add(v1, right)
            v3 = self.builder.xor(left, right)
            v4 = self.builder.icmp_signed('<', v3, vInt(0))
            v5 = self.builder.select(v4, v2, v1)
            v6 = self.builder.icmp_signed('==', v1, vInt(0))
            return self.builder.select(v6, v1, v5)
        else:
            instruction = {
                '*': self.builder.mul,
                '+': self.builder.add,
                '-': self.builder.sub,
                '<<': self.builder.shl,
                '>>': self.builder.ashr,
                '&': self.builder.and_,
                '$': self.builder.xor,
                '|': self.builder.or_,
            }[op]
            return instruction(left, right)

    def cmp(self, ctx, op, left, right):
        if left.type != right.type:
            self.throw(ctx, err.NotComparable(left.type, right.type))

        if left.type in (tInt, tChar):
            return self.builder.icmp_signed(op, left, right)
        elif left.type == tBool:
            return self.builder.icmp_unsigned(op, left, right)
        else:
            self.throw(ctx, err.NotComparable(left.type, right.type))

    def print(self, ctx, value):
        if value.type == tInt:
            self.builder.call(self.builtins['writeInt'], [value])
        elif value.type == tBool:
            self.builder.call(self.builtins['writeBool'], [value])
        elif value.type == tChar:
            self.builder.call(self.builtins['writeChar'], [value])
        elif value.type.isString():
            self.builder.call(self.builtins['write'], [value])
        elif value.type.isTuple():
            for i in range(len(value.type.elements)):
                if i > 0:
                    self.builder.call(self.builtins['putchar'], [vChar(' ')])
                elem = self.builder.extract_value(value, [i])
                self.print(ctx, elem)
        else:
            self.throw(ctx, err.NotPrintable(value.type))

    def malloc(self, type):
        size = self.builder.gep(vNull(type), [vIndex(1)])
        size = self.builder.ptrtoint(size, tInt)
        ptr = self.builder.call(self.builtins['malloc'], [size])
        return self.builder.bitcast(ptr, tPtr(type))


    ### Program ###

    def visitProgram(self, ctx):
        func = ll.Function(self.module, tFunc([], tInt), 'main')
        entry = func.append_basic_block()
        self.builder.position_at_end(entry)
        self.visitChildren(ctx)
        self.builder.position_at_end(func.blocks[-1])
        self.builder.ret(ll.Constant(tInt, 0))


    ### Statements ###

    def visitStmtPrint(self, ctx):
        expr = ctx.expr()
        if expr:
            value = self.visit(expr)
            self.print(expr, value)

        self.builder.call(self.builtins['putchar'], [vChar('\n')])

    def visitStmtAssg(self, ctx):
        value = self.visit(ctx.expr())

        for lvalue in ctx.lvalue():
            ids = self.visit(lvalue)
            len1 = len(ids)

            if value.type.isTuple():
                len2 = len(value.type.elements)
                if len1 > 1 and len1 != len2:
                    self.throw(ctx, err.CannotUnpack(value.type, len1))
            elif len1 > 1:
                self.throw(ctx, err.CannotUnpack(value.type, len1))

            if len1 == 1:
                self.assign(ctx, ids[0], value)
            else:
                for i, id in enumerate(ids):
                    self.assign(ctx, id, self.builder.extract_value(value, [i]))

    def visitLvalue(self, ctx):
        return ctx.ID()

    def visitStmtAssgExpr(self, ctx):
        var = self.get(ctx, ctx.ID())
        value = self.binaryop(ctx, ctx.op.text, self.builder.load(var), self.visit(ctx.expr()))
        self.builder.store(value, var)

    def visitStmtIf(self, ctx):
        exprs = ctx.expr()
        blocks = ctx.block()

        bbend = ll.Block(self.builder.function)

        def emitIfElse(index):
            if len(exprs) == index:
                if len(blocks) > index:
                    with self.local():
                        self.visit(blocks[index])
                return

            expr = exprs[index]
            cond = self.visit(expr)
            if cond.type != tBool:
                self.throw(expr, err.IllegalAssignment(cond.type, tBool))

            bbif = self.builder.append_basic_block()
            bbelse = self.builder.append_basic_block()
            self.builder.cbranch(cond, bbif, bbelse)

            with self.builder._branch_helper(bbif, bbend):
                with self.local():
                    self.visit(blocks[index])

            with self.builder._branch_helper(bbelse, bbend):
                emitIfElse(index+1)

        emitIfElse(0)

        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)

    def visitStmtWhile(self, ctx):
        bbstart = self.builder.append_basic_block()
        self.builder.branch(bbstart)
        self.builder.position_at_end(bbstart)

        expr = ctx.expr()
        cond = self.visit(expr)
        if cond.type != tBool:
            self.throw(expr, err.IllegalAssignment(cond.type, tBool))

        bbwhile = self.builder.append_basic_block()
        bbend = ll.Block(self.builder.function)
        self.builder.cbranch(cond, bbwhile, bbend)

        self.builder.position_at_end(bbwhile)
        with self.local():
            self.visit(ctx.block())
        self.builder.branch(bbstart)

        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)

    def visitStmtUntil(self, ctx):
        bbuntil = self.builder.append_basic_block()
        self.builder.branch(bbuntil)
        bbend = ll.Block(self.builder.function)

        self.builder.position_at_end(bbuntil)
        with self.local():
            self.visit(ctx.block())

        expr = ctx.expr()
        cond = self.visit(expr)
        if cond.type != tBool:
            self.throw(expr, err.IllegalAssignment(cond.type, tBool))

        self.builder.cbranch(cond, bbend, bbuntil)

        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)


    ### Expressions ###

    def visitExprParentheses(self, ctx):
        return self.visit(ctx.expr())

    def visitExprIndex(self, ctx):
        exprs = ctx.expr()

        index = self.visit(exprs[1])
        if index.type != tInt:
            self.throw(exprs[1], err.IllegalAssignment(index.type, tInt))

        value = self.visit(exprs[0])

        if value.type.isString():
            return self.builder.load(self.builder.gep(self.builder.extract_value(value, [0]), [index]))

        self.throw(ctx, err.NotIndexable(value.type))

    def visitExprAttr(self, ctx):
        value = self.visit(ctx.expr())
        id = str(ctx.ID())

        if value.type.isString():
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

    def visitExprUnaryOp(self, ctx):
        return self.unaryop(ctx, ctx.op.text, self.visit(ctx.expr()))

    def visitExprBinaryOp(self, ctx):
        return self.binaryop(ctx, ctx.op.text, self.visit(ctx.expr(0)), self.visit(ctx.expr(1)))

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

        bbstart = self.builder.basic_block
        bbend = ll.Block(self.builder.function)
        self.builder.position_at_end(bbend)
        phi = self.builder.phi(tBool)
        self.builder.position_at_end(bbstart)

        def emitIf(index):
            values.append(self.visit(exprs[index+1]))
            cond = self.cmp(ctx, ops[index], values[index], values[index+1])

            if len(exprs) == index+2:
                phi.add_incoming(cond, self.builder.basic_block)
                self.builder.branch(bbend)
                return

            phi.add_incoming(vFalse, self.builder.basic_block)
            bbif = self.builder.function.append_basic_block()
            self.builder.cbranch(cond, bbif, bbend)

            with self.builder._branch_helper(bbif, bbend):
                emitIf(index+1)

        emitIf(0)

        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)

        return phi

    def visitExprLogicalOp(self, ctx):
        op = ctx.op.text

        cond1 = self.visit(ctx.expr(0))
        bbstart = self.builder.basic_block
        bbif = self.builder.function.append_basic_block()
        bbend = ll.Block(self.builder.function)

        if op == 'and':
            self.builder.cbranch(cond1, bbif, bbend)
        elif op == 'or':
            self.builder.cbranch(cond1, bbend, bbif)

        self.builder.position_at_end(bbend)
        phi = self.builder.phi(tBool)
        if op == 'and':
            phi.add_incoming(vFalse, bbstart)
        elif op == 'or':
            phi.add_incoming(vTrue, bbstart)

        with self.builder._branch_helper(bbif, bbend):
            cond2 = self.visit(ctx.expr(1))
            if not cond1.type == cond2.type == tBool:
                self.throw(ctx, err.NoBinaryOperator(op, cond1.type, cond2.type))
            phi.add_incoming(cond2, self.builder.basic_block)

        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)

        return phi

    def visitExprTuple(self, ctx):
        exprs = []
        while True:
            exprs.append(ctx.expr(0))
            if not isinstance(ctx.expr(1), PyxellParser.ExprTupleContext):
                break
            ctx = ctx.expr(1)
        exprs.append(ctx.expr(1))

        values = [self.visit(expr) for expr in exprs]
        type = tTuple(value.type for value in values)

        tuple = self.malloc(type)

        for i, value in enumerate(values):
            ptr = self.builder.gep(tuple, [vIndex(0), vIndex(i)])
            self.builder.store(value, ptr)

        return self.builder.load(tuple)


    ### Atoms ###

    def visitAtomInt(self, ctx):
        return vInt(ctx.INT())

    def visitAtomBool(self, ctx):
        return vBool(ctx.getText() == 'true')

    def visitAtomChar(self, ctx):
        lit = ast.literal_eval(str(ctx.CHAR()))
        return vChar(lit)

    def visitAtomString(self, ctx):
        lit = ast.literal_eval(str(ctx.STRING()))
        value = ll.Constant(ll.ArrayType(tChar, len(lit)), [vChar(c) for c in lit])

        string = self.malloc(tString)

        pointer = self.builder.gep(string, [vIndex(0), vIndex(0)])
        array = ll.GlobalVariable(self.module, value.type, self.module.get_unique_name('str'))
        array.global_constant = True
        array.initializer = value
        self.builder.store(self.builder.gep(array, [vIndex(0), vIndex(0)]), pointer)

        length = self.builder.gep(string, [vIndex(0), vIndex(1)])
        self.builder.store(vInt(value.type.count), length)

        return self.builder.load(string)

    def visitAtomId(self, ctx):
        return self.builder.load(self.get(ctx, ctx.ID()))
