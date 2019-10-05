
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
            'writeInt': ll.Function(self.module, tFunc([tInt]), 'func.writeInt'),
            'putchar': ll.Function(self.module, tFunc([tChar]), 'putchar'),
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

    def binop(self, ctx, op, left, right):
        if not left.type == right.type == tInt:
            self.throw(ctx, err.NoBinaryOperator(op, left.type, right.type))

        instruction = {
            '*': self.builder.mul,
            '/': self.builder.sdiv,
            '%': self.builder.srem,
            '+': self.builder.add,
            '-': self.builder.sub,
        }[op]
        return instruction(left, right)

    def cmp(self, ctx, op, left, right):
        if left.type != right.type:
            self.throw(ctx, err.NotComparable(left.type, right.type))

        if left.type == tBool:
            return self.builder.icmp_unsigned(op, left, right)
        else:
            return self.builder.icmp_signed(op, left, right)


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
        value = self.visit(ctx.expr())
        self.builder.call(self.builtins['writeInt'], [value])
        self.builder.call(self.builtins['putchar'], [ll.Constant(tChar, ord('\n'))])

    def visitStmtAssg(self, ctx):
        value = self.visit(ctx.expr())
        for id in ctx.ID():
            self.assign(ctx, id, value)

    def visitStmtAssgExpr(self, ctx):
        var = self.get(ctx, ctx.ID())
        value = self.binop(ctx, ctx.op.text, self.builder.load(var), self.visit(ctx.expr()))
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

    def visitExprUnaryOp(self, ctx):
        value = self.visit(ctx.expr())
        op = ctx.op.text

        if op == '+':
            if value.type != tInt:
                self.throw(ctx, err.NoUnaryOperator(op, value.type))
            return value
        elif op == '-':
            if value.type != tInt:
                self.throw(ctx, err.NoUnaryOperator(op, value.type))
            return self.builder.neg(value)
        elif op == 'not':
            if value.type != tBool:
                self.throw(ctx, err.NoUnaryOperator(op, value.type))
            return self.builder.not_(value)

    def visitExprBinaryOp(self, ctx):
        return self.binop(ctx, ctx.op.text, self.visit(ctx.expr(0)), self.visit(ctx.expr(1)))

    def visitExprCmp(self, ctx):
        ops = []
        exprs = []

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


    ### Atoms ###

    def visitAtomInt(self, ctx):
        return ll.Constant(tInt, ctx.INT())

    def visitAtomBool(self, ctx):
        return ll.Constant(tBool, int(ctx.getText() == 'true'))

    def visitAtomId(self, ctx):
        return self.builder.load(self.get(ctx, ctx.ID()))
