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


    # Visit a parse tree produced by PyxellParser#block.
    def visitBlock(self, ctx:PyxellParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtUse.
    def visitStmtUse(self, ctx:PyxellParser.StmtUseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtSkip.
    def visitStmtSkip(self, ctx:PyxellParser.StmtSkipContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtPrint.
    def visitStmtPrint(self, ctx:PyxellParser.StmtPrintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtDecl.
    def visitStmtDecl(self, ctx:PyxellParser.StmtDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtAssg.
    def visitStmtAssg(self, ctx:PyxellParser.StmtAssgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtAssgExpr.
    def visitStmtAssgExpr(self, ctx:PyxellParser.StmtAssgExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtLoopControl.
    def visitStmtLoopControl(self, ctx:PyxellParser.StmtLoopControlContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtReturn.
    def visitStmtReturn(self, ctx:PyxellParser.StmtReturnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtYield.
    def visitStmtYield(self, ctx:PyxellParser.StmtYieldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtIf.
    def visitStmtIf(self, ctx:PyxellParser.StmtIfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtWhile.
    def visitStmtWhile(self, ctx:PyxellParser.StmtWhileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtUntil.
    def visitStmtUntil(self, ctx:PyxellParser.StmtUntilContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtFor.
    def visitStmtFor(self, ctx:PyxellParser.StmtForContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtFunc.
    def visitStmtFunc(self, ctx:PyxellParser.StmtFuncContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#StmtClass.
    def visitStmtClass(self, ctx:PyxellParser.StmtClassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#FuncArg.
    def visitFuncArg(self, ctx:PyxellParser.FuncArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#func_args.
    def visitFunc_args(self, ctx:PyxellParser.Func_argsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ClassField.
    def visitClassField(self, ctx:PyxellParser.ClassFieldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ClassMethod.
    def visitClassMethod(self, ctx:PyxellParser.ClassMethodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ClassConstructor.
    def visitClassConstructor(self, ctx:PyxellParser.ClassConstructorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ClassDestructor.
    def visitClassDestructor(self, ctx:PyxellParser.ClassDestructorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprUnaryOp.
    def visitExprUnaryOp(self, ctx:PyxellParser.ExprUnaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprBy.
    def visitExprBy(self, ctx:PyxellParser.ExprByContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprSpread.
    def visitExprSpread(self, ctx:PyxellParser.ExprSpreadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprCmp.
    def visitExprCmp(self, ctx:PyxellParser.ExprCmpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprIndex.
    def visitExprIndex(self, ctx:PyxellParser.ExprIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprAtom.
    def visitExprAtom(self, ctx:PyxellParser.ExprAtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprAttr.
    def visitExprAttr(self, ctx:PyxellParser.ExprAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprParentheses.
    def visitExprParentheses(self, ctx:PyxellParser.ExprParenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprDict.
    def visitExprDict(self, ctx:PyxellParser.ExprDictContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprArray.
    def visitExprArray(self, ctx:PyxellParser.ExprArrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprLogicalOp.
    def visitExprLogicalOp(self, ctx:PyxellParser.ExprLogicalOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprArrayComprehension.
    def visitExprArrayComprehension(self, ctx:PyxellParser.ExprArrayComprehensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprSetComprehension.
    def visitExprSetComprehension(self, ctx:PyxellParser.ExprSetComprehensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprCall.
    def visitExprCall(self, ctx:PyxellParser.ExprCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprIsNull.
    def visitExprIsNull(self, ctx:PyxellParser.ExprIsNullContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprDictComprehension.
    def visitExprDictComprehension(self, ctx:PyxellParser.ExprDictComprehensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprIn.
    def visitExprIn(self, ctx:PyxellParser.ExprInContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprCond.
    def visitExprCond(self, ctx:PyxellParser.ExprCondContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprSlice.
    def visitExprSlice(self, ctx:PyxellParser.ExprSliceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprBinaryOp.
    def visitExprBinaryOp(self, ctx:PyxellParser.ExprBinaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprRange.
    def visitExprRange(self, ctx:PyxellParser.ExprRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprSet.
    def visitExprSet(self, ctx:PyxellParser.ExprSetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprLambda.
    def visitExprLambda(self, ctx:PyxellParser.ExprLambdaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#DictPair.
    def visitDictPair(self, ctx:PyxellParser.DictPairContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#DictSpread.
    def visitDictSpread(self, ctx:PyxellParser.DictSpreadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprTuple.
    def visitExprTuple(self, ctx:PyxellParser.ExprTupleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ExprInterpolation.
    def visitExprInterpolation(self, ctx:PyxellParser.ExprInterpolationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ComprehensionIteration.
    def visitComprehensionIteration(self, ctx:PyxellParser.ComprehensionIterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#ComprehensionPredicate.
    def visitComprehensionPredicate(self, ctx:PyxellParser.ComprehensionPredicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#CallArg.
    def visitCallArg(self, ctx:PyxellParser.CallArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomInt.
    def visitAtomInt(self, ctx:PyxellParser.AtomIntContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomFloat.
    def visitAtomFloat(self, ctx:PyxellParser.AtomFloatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomBool.
    def visitAtomBool(self, ctx:PyxellParser.AtomBoolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomChar.
    def visitAtomChar(self, ctx:PyxellParser.AtomCharContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomString.
    def visitAtomString(self, ctx:PyxellParser.AtomStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomNull.
    def visitAtomNull(self, ctx:PyxellParser.AtomNullContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomSelf.
    def visitAtomSelf(self, ctx:PyxellParser.AtomSelfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomSuper.
    def visitAtomSuper(self, ctx:PyxellParser.AtomSuperContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomDefault.
    def visitAtomDefault(self, ctx:PyxellParser.AtomDefaultContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#AtomId.
    def visitAtomId(self, ctx:PyxellParser.AtomIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#IdList.
    def visitIdList(self, ctx:PyxellParser.IdListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeParentheses.
    def visitTypeParentheses(self, ctx:PyxellParser.TypeParenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeArray.
    def visitTypeArray(self, ctx:PyxellParser.TypeArrayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeName.
    def visitTypeName(self, ctx:PyxellParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeTuple.
    def visitTypeTuple(self, ctx:PyxellParser.TypeTupleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeDict.
    def visitTypeDict(self, ctx:PyxellParser.TypeDictContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeFunc0.
    def visitTypeFunc0(self, ctx:PyxellParser.TypeFunc0Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeSet.
    def visitTypeSet(self, ctx:PyxellParser.TypeSetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeNullable.
    def visitTypeNullable(self, ctx:PyxellParser.TypeNullableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PyxellParser#TypeFunc.
    def visitTypeFunc(self, ctx:PyxellParser.TypeFuncContext):
        return self.visitChildren(ctx)



del PyxellParser