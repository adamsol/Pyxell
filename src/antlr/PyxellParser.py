# Generated from Pyxell.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\17")
        buf.write("\67\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\3\2\7\2\f\n\2\f\2")
        buf.write("\16\2\17\13\2\3\2\3\2\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3")
        buf.write("\3\3\5\3\34\n\3\3\4\3\4\3\4\3\4\3\4\3\4\3\4\3\4\5\4&\n")
        buf.write("\4\3\4\3\4\3\4\3\4\3\4\3\4\7\4.\n\4\f\4\16\4\61\13\4\3")
        buf.write("\5\3\5\5\5\65\n\5\3\5\2\3\6\6\2\4\6\b\2\4\3\2\t\n\3\2")
        buf.write("\6\b\29\2\r\3\2\2\2\4\33\3\2\2\2\6%\3\2\2\2\b\64\3\2\2")
        buf.write("\2\n\f\5\4\3\2\13\n\3\2\2\2\f\17\3\2\2\2\r\13\3\2\2\2")
        buf.write("\r\16\3\2\2\2\16\20\3\2\2\2\17\r\3\2\2\2\20\21\7\2\2\3")
        buf.write("\21\3\3\2\2\2\22\23\7\3\2\2\23\24\5\6\4\2\24\25\7\4\2")
        buf.write("\2\25\34\3\2\2\2\26\27\7\16\2\2\27\30\7\5\2\2\30\31\5")
        buf.write("\6\4\2\31\32\7\4\2\2\32\34\3\2\2\2\33\22\3\2\2\2\33\26")
        buf.write("\3\2\2\2\34\5\3\2\2\2\35\36\b\4\1\2\36\37\t\2\2\2\37&")
        buf.write("\5\6\4\5 !\7\13\2\2!\"\5\6\4\2\"#\7\f\2\2#&\3\2\2\2$&")
        buf.write("\5\b\5\2%\35\3\2\2\2% \3\2\2\2%$\3\2\2\2&/\3\2\2\2\'(")
        buf.write("\f\7\2\2()\t\3\2\2).\5\6\4\b*+\f\6\2\2+,\t\2\2\2,.\5\6")
        buf.write("\4\7-\'\3\2\2\2-*\3\2\2\2.\61\3\2\2\2/-\3\2\2\2/\60\3")
        buf.write("\2\2\2\60\7\3\2\2\2\61/\3\2\2\2\62\65\7\r\2\2\63\65\7")
        buf.write("\16\2\2\64\62\3\2\2\2\64\63\3\2\2\2\65\t\3\2\2\2\b\r\33")
        buf.write("%-/\64")
        return buf.getvalue()


class PyxellParser ( Parser ):

    grammarFileName = "Pyxell.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'print'", "';'", "'='", "'*'", "'/'", 
                     "'%'", "'+'", "'-'", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "INT", "ID", 
                      "WS" ]

    RULE_program = 0
    RULE_stmt = 1
    RULE_expr = 2
    RULE_atom = 3

    ruleNames =  [ "program", "stmt", "expr", "atom" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    INT=11
    ID=12
    WS=13

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProgramContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(PyxellParser.EOF, 0)

        def stmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PyxellParser.StmtContext)
            else:
                return self.getTypedRuleContext(PyxellParser.StmtContext,i)


        def getRuleIndex(self):
            return PyxellParser.RULE_program

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProgram" ):
                return visitor.visitProgram(self)
            else:
                return visitor.visitChildren(self)




    def program(self):

        localctx = PyxellParser.ProgramContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_program)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 11
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PyxellParser.T__0 or _la==PyxellParser.ID:
                self.state = 8
                self.stmt()
                self.state = 13
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 14
            self.match(PyxellParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StmtContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PyxellParser.RULE_stmt

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class StmtAssgContext(StmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.StmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ID(self):
            return self.getToken(PyxellParser.ID, 0)
        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtAssg" ):
                return visitor.visitStmtAssg(self)
            else:
                return visitor.visitChildren(self)


    class StmtPrintContext(StmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.StmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtPrint" ):
                return visitor.visitStmtPrint(self)
            else:
                return visitor.visitChildren(self)



    def stmt(self):

        localctx = PyxellParser.StmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_stmt)
        try:
            self.state = 25
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.T__0]:
                localctx = PyxellParser.StmtPrintContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 16
                self.match(PyxellParser.T__0)
                self.state = 17
                self.expr(0)
                self.state = 18
                self.match(PyxellParser.T__1)
                pass
            elif token in [PyxellParser.ID]:
                localctx = PyxellParser.StmtAssgContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 20
                self.match(PyxellParser.ID)
                self.state = 21
                self.match(PyxellParser.T__2)
                self.state = 22
                self.expr(0)
                self.state = 23
                self.match(PyxellParser.T__1)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExprContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PyxellParser.RULE_expr

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class ExprUnaryOpContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.ExprContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExprUnaryOp" ):
                return visitor.visitExprUnaryOp(self)
            else:
                return visitor.visitChildren(self)


    class ExprAtomContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def atom(self):
            return self.getTypedRuleContext(PyxellParser.AtomContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExprAtom" ):
                return visitor.visitExprAtom(self)
            else:
                return visitor.visitChildren(self)


    class ExprParenthesesContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExprParentheses" ):
                return visitor.visitExprParentheses(self)
            else:
                return visitor.visitChildren(self)


    class ExprBinaryOpContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.ExprContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PyxellParser.ExprContext)
            else:
                return self.getTypedRuleContext(PyxellParser.ExprContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExprBinaryOp" ):
                return visitor.visitExprBinaryOp(self)
            else:
                return visitor.visitChildren(self)



    def expr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = PyxellParser.ExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 4
        self.enterRecursionRule(localctx, 4, self.RULE_expr, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 35
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.T__6, PyxellParser.T__7]:
                localctx = PyxellParser.ExprUnaryOpContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 28
                localctx.op = self._input.LT(1)
                _la = self._input.LA(1)
                if not(_la==PyxellParser.T__6 or _la==PyxellParser.T__7):
                    localctx.op = self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 29
                self.expr(3)
                pass
            elif token in [PyxellParser.T__8]:
                localctx = PyxellParser.ExprParenthesesContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 30
                self.match(PyxellParser.T__8)
                self.state = 31
                self.expr(0)
                self.state = 32
                self.match(PyxellParser.T__9)
                pass
            elif token in [PyxellParser.INT, PyxellParser.ID]:
                localctx = PyxellParser.ExprAtomContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 34
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 45
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,4,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 43
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
                    if la_ == 1:
                        localctx = PyxellParser.ExprBinaryOpContext(self, PyxellParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 37
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 38
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PyxellParser.T__3) | (1 << PyxellParser.T__4) | (1 << PyxellParser.T__5))) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 39
                        self.expr(6)
                        pass

                    elif la_ == 2:
                        localctx = PyxellParser.ExprBinaryOpContext(self, PyxellParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 40
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 41
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==PyxellParser.T__6 or _la==PyxellParser.T__7):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 42
                        self.expr(5)
                        pass

             
                self.state = 47
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,4,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class AtomContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PyxellParser.RULE_atom

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AtomIntContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def INT(self):
            return self.getToken(PyxellParser.INT, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtomInt" ):
                return visitor.visitAtomInt(self)
            else:
                return visitor.visitChildren(self)


    class AtomIdContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ID(self):
            return self.getToken(PyxellParser.ID, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtomId" ):
                return visitor.visitAtomId(self)
            else:
                return visitor.visitChildren(self)



    def atom(self):

        localctx = PyxellParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_atom)
        try:
            self.state = 50
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.INT]:
                localctx = PyxellParser.AtomIntContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 48
                self.match(PyxellParser.INT)
                pass
            elif token in [PyxellParser.ID]:
                localctx = PyxellParser.AtomIdContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 49
                self.match(PyxellParser.ID)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[2] = self.expr_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def expr_sempred(self, localctx:ExprContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 4)
         




