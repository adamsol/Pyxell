
from contextlib import contextmanager

import llvmlite.ir as ll

from .antlr.PyxellVisitor import PyxellVisitor


### Types ###

tVoid = ll.VoidType()
tInt = ll.IntType(64)
tBool = ll.IntType(1)
tChar = ll.IntType(8)

def tFunc(args, ret=tVoid):
    return ll.FunctionType(ret, args)


### Visitor ###

class PyxellCompiler(PyxellVisitor):

    def __init__(self):
        self.env = {}
        self.builder = ll.IRBuilder()
        self.module = ll.Module()
        self.builtins = {
            'writeInt': ll.Function(self.module, tFunc([tInt]), 'func.writeInt'),
            'putchar': ll.Function(self.module, tFunc([tChar]), 'putchar'),
        }
        pass


    ### Helpers ###

    @contextmanager
    def local(self):
        tmp = self.env.copy()
        yield
        self.env = tmp

    def get(self, id):
        return self.env[str(id)]

    def assign(self, id, value):
        id = str(id)

        try:
            var = self.env[id]
        except KeyError:
            var = self.env[id] = self.builder.alloca(value.type)

        self.builder.store(value, var)


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
            self.assign(id, value)

    def visitStmtIf(self, ctx):
        exprs = ctx.expr()
        blocks = ctx.block()

        bbend = ll.Block(parent=self.builder.function)

        def emitIfElse(index):
            if len(exprs) <= index:
                if len(blocks) > index:
                    with self.local():
                        self.visit(blocks[index])
                return

            cond = self.visit(exprs[index])
            bbif = self.builder.function.append_basic_block()
            bbelse = self.builder.function.append_basic_block()
            self.builder.cbranch(cond, bbif, bbelse)

            with self.builder._branch_helper(bbif, bbend):
                with self.local():
                    self.visit(blocks[index])

            with self.builder._branch_helper(bbelse, bbend):
                emitIfElse(index+1)

        emitIfElse(0)
        self.builder.function.blocks.append(bbend)
        self.builder.position_at_end(bbend)

    ### Expressions ###

    def visitExprBinaryOp(self, ctx):
        instruction = {
            '*': self.builder.mul,
            '/': self.builder.sdiv,
            '%': self.builder.srem,
            '+': self.builder.add,
            '-': self.builder.sub,
        }[ctx.op.text]
        return instruction(self.visit(ctx.expr(0)), self.visit(ctx.expr(1)))

    def visitExprUnaryOp(self, ctx):
        instruction = {
            '+': self.builder.add,
            '-': self.builder.sub,
        }[ctx.op.text]
        return instruction(ll.Constant(tInt, 0), self.visit(ctx.expr()))

    def visitExprParentheses(self, ctx):
        return self.visit(ctx.expr())


    ### Atoms ###

    def visitAtomInt(self, ctx):
        return ll.Constant(tInt, ctx.INT())

    def visitAtomBool(self, ctx):
        return ll.Constant(tBool, int(ctx.getText() == 'true'))

    def visitAtomId(self, ctx):
        return self.builder.load(self.get(ctx.ID()))
