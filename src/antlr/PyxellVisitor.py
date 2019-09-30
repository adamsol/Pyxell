# Generated from Pyxell.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .PyxellParser import PyxellParser
else:
    from PyxellParser import PyxellParser

# This class defines a complete generic visitor for a parse tree produced by PyxellParser.

class PyxellVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PyxellParser#program.
    def visitProgram(self, ctx:PyxellParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#stmt.
    def visitStmt(self, ctx:PyxellParser.StmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtSkip.
    def visitStmtSkip(self, ctx:PyxellParser.StmtSkipContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtPrint.
    def visitStmtPrint(self, ctx:PyxellParser.StmtPrintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtAssg.
    def visitStmtAssg(self, ctx:PyxellParser.StmtAssgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtIf.
    def visitStmtIf(self, ctx:PyxellParser.StmtIfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#block.
    def visitBlock(self, ctx:PyxellParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprUnaryOp.
    def visitExprUnaryOp(self, ctx:PyxellParser.ExprUnaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprAtom.
    def visitExprAtom(self, ctx:PyxellParser.ExprAtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprParentheses.
    def visitExprParentheses(self, ctx:PyxellParser.ExprParenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprBinaryOp.
    def visitExprBinaryOp(self, ctx:PyxellParser.ExprBinaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomInt.
    def visitAtomInt(self, ctx:PyxellParser.AtomIntContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomBool.
    def visitAtomBool(self, ctx:PyxellParser.AtomBoolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomId.
    def visitAtomId(self, ctx:PyxellParser.AtomIdContext):
        return self.visitChildren(ctx)



del PyxellParser