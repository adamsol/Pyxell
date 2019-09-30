
from contextlib import contextmanager

import llvmlite.ir as ll

from .antlr.PyxellVisitor import PyxellVisitor


### Types ###

tVoid = ll.VoidType()
tInt = ll.IntType(64)
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

    def visitAtomId(self, ctx):
        return self.builder.load(self.get(ctx.ID()))
