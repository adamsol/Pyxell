# Generated from Pyxell.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\30")
        buf.write("_\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\3\2\7\2\22\n\2\f\2\16\2\25\13\2\3\2\3\2\3\3\3\3\3")
        buf.write("\3\3\3\5\3\35\n\3\3\4\3\4\3\4\3\4\3\4\7\4$\n\4\f\4\16")
        buf.write("\4\'\13\4\3\4\5\4*\n\4\3\5\3\5\3\5\3\5\3\5\3\5\3\5\7\5")
        buf.write("\63\n\5\f\5\16\5\66\13\5\3\5\3\5\5\5:\n\5\3\6\3\6\3\6")
        buf.write("\6\6?\n\6\r\6\16\6@\3\6\3\6\3\7\3\7\3\7\3\7\3\7\3\7\3")
        buf.write("\7\3\7\5\7M\n\7\3\7\3\7\3\7\3\7\3\7\3\7\7\7U\n\7\f\7\16")
        buf.write("\7X\13\7\3\b\3\b\3\b\5\b]\n\b\3\b\2\3\f\t\2\4\6\b\n\f")
        buf.write("\16\2\5\3\2\20\21\3\2\r\17\3\2\24\25\2e\2\23\3\2\2\2\4")
        buf.write("\34\3\2\2\2\6)\3\2\2\2\b+\3\2\2\2\n;\3\2\2\2\fL\3\2\2")
        buf.write("\2\16\\\3\2\2\2\20\22\5\4\3\2\21\20\3\2\2\2\22\25\3\2")
        buf.write("\2\2\23\21\3\2\2\2\23\24\3\2\2\2\24\26\3\2\2\2\25\23\3")
        buf.write("\2\2\2\26\27\7\2\2\3\27\3\3\2\2\2\30\31\5\6\4\2\31\32")
        buf.write("\7\3\2\2\32\35\3\2\2\2\33\35\5\b\5\2\34\30\3\2\2\2\34")
        buf.write("\33\3\2\2\2\35\5\3\2\2\2\36*\7\4\2\2\37 \7\5\2\2 *\5\f")
        buf.write("\7\2!\"\7\27\2\2\"$\7\6\2\2#!\3\2\2\2$\'\3\2\2\2%#\3\2")
        buf.write("\2\2%&\3\2\2\2&(\3\2\2\2\'%\3\2\2\2(*\5\f\7\2)\36\3\2")
        buf.write("\2\2)\37\3\2\2\2)%\3\2\2\2*\7\3\2\2\2+,\7\7\2\2,-\5\f")
        buf.write("\7\2-\64\5\n\6\2./\7\b\2\2/\60\5\f\7\2\60\61\5\n\6\2\61")
        buf.write("\63\3\2\2\2\62.\3\2\2\2\63\66\3\2\2\2\64\62\3\2\2\2\64")
        buf.write("\65\3\2\2\2\659\3\2\2\2\66\64\3\2\2\2\678\7\t\2\28:\5")
        buf.write("\n\6\29\67\3\2\2\29:\3\2\2\2:\t\3\2\2\2;<\7\n\2\2<>\7")
        buf.write("\13\2\2=?\5\4\3\2>=\3\2\2\2?@\3\2\2\2@>\3\2\2\2@A\3\2")
        buf.write("\2\2AB\3\2\2\2BC\7\f\2\2C\13\3\2\2\2DE\b\7\1\2EF\t\2\2")
        buf.write("\2FM\5\f\7\5GH\7\22\2\2HI\5\f\7\2IJ\7\23\2\2JM\3\2\2\2")
        buf.write("KM\5\16\b\2LD\3\2\2\2LG\3\2\2\2LK\3\2\2\2MV\3\2\2\2NO")
        buf.write("\f\7\2\2OP\t\3\2\2PU\5\f\7\bQR\f\6\2\2RS\t\2\2\2SU\5\f")
        buf.write("\7\7TN\3\2\2\2TQ\3\2\2\2UX\3\2\2\2VT\3\2\2\2VW\3\2\2\2")
        buf.write("W\r\3\2\2\2XV\3\2\2\2Y]\7\26\2\2Z]\t\4\2\2[]\7\27\2\2")
        buf.write("\\Y\3\2\2\2\\Z\3\2\2\2\\[\3\2\2\2]\17\3\2\2\2\r\23\34")
        buf.write("%)\649@LTV\\")
        return buf.getvalue()


class PyxellParser ( Parser ):

    grammarFileName = "Pyxell.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "';'", "'skip'", "'print'", "'='", "'if'", 
                     "'elif'", "'else'", "'do'", "'{'", "'}'", "'*'", "'/'", 
                     "'%'", "'+'", "'-'", "'('", "')'", "'true'", "'false'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "INT", "ID", "WS" ]

    RULE_program = 0
    RULE_stmt = 1
    RULE_simple_stmt = 2
    RULE_compound_stmt = 3
    RULE_block = 4
    RULE_expr = 5
    RULE_atom = 6

    ruleNames =  [ "program", "stmt", "simple_stmt", "compound_stmt", "block", 
                   "expr", "atom" ]

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
    T__10=11
    T__11=12
    T__12=13
    T__13=14
    T__14=15
    T__15=16
    T__16=17
    T__17=18
    T__18=19
    INT=20
    ID=21
    WS=22

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
            self.state = 17
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PyxellParser.T__1) | (1 << PyxellParser.T__2) | (1 << PyxellParser.T__4) | (1 << PyxellParser.T__13) | (1 << PyxellParser.T__14) | (1 << PyxellParser.T__15) | (1 << PyxellParser.T__17) | (1 << PyxellParser.T__18) | (1 << PyxellParser.INT) | (1 << PyxellParser.ID))) != 0):
                self.state = 14
                self.stmt()
                self.state = 19
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 20
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

        def simple_stmt(self):
            return self.getTypedRuleContext(PyxellParser.Simple_stmtContext,0)


        def compound_stmt(self):
            return self.getTypedRuleContext(PyxellParser.Compound_stmtContext,0)


        def getRuleIndex(self):
            return PyxellParser.RULE_stmt

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmt" ):
                return visitor.visitStmt(self)
            else:
                return visitor.visitChildren(self)




    def stmt(self):

        localctx = PyxellParser.StmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_stmt)
        try:
            self.state = 26
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.T__1, PyxellParser.T__2, PyxellParser.T__13, PyxellParser.T__14, PyxellParser.T__15, PyxellParser.T__17, PyxellParser.T__18, PyxellParser.INT, PyxellParser.ID]:
                self.enterOuterAlt(localctx, 1)
                self.state = 22
                self.simple_stmt()
                self.state = 23
                self.match(PyxellParser.T__0)
                pass
            elif token in [PyxellParser.T__4]:
                self.enterOuterAlt(localctx, 2)
                self.state = 25
                self.compound_stmt()
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


    class Simple_stmtContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PyxellParser.RULE_simple_stmt

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class StmtAssgContext(Simple_stmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.Simple_stmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)

        def ID(self, i:int=None):
            if i is None:
                return self.getTokens(PyxellParser.ID)
            else:
                return self.getToken(PyxellParser.ID, i)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtAssg" ):
                return visitor.visitStmtAssg(self)
            else:
                return visitor.visitChildren(self)


    class StmtSkipContext(Simple_stmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.Simple_stmtContext
            super().__init__(parser)
            self.copyFrom(ctx)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtSkip" ):
                return visitor.visitStmtSkip(self)
            else:
                return visitor.visitChildren(self)


    class StmtPrintContext(Simple_stmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.Simple_stmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(PyxellParser.ExprContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtPrint" ):
                return visitor.visitStmtPrint(self)
            else:
                return visitor.visitChildren(self)



    def simple_stmt(self):

        localctx = PyxellParser.Simple_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_simple_stmt)
        try:
            self.state = 39
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.T__1]:
                localctx = PyxellParser.StmtSkipContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 28
                self.match(PyxellParser.T__1)
                pass
            elif token in [PyxellParser.T__2]:
                localctx = PyxellParser.StmtPrintContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 29
                self.match(PyxellParser.T__2)
                self.state = 30
                self.expr(0)
                pass
            elif token in [PyxellParser.T__13, PyxellParser.T__14, PyxellParser.T__15, PyxellParser.T__17, PyxellParser.T__18, PyxellParser.INT, PyxellParser.ID]:
                localctx = PyxellParser.StmtAssgContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 35
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt==1:
                        self.state = 31
                        self.match(PyxellParser.ID)
                        self.state = 32
                        self.match(PyxellParser.T__3) 
                    self.state = 37
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

                self.state = 38
                self.expr(0)
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


    class Compound_stmtContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PyxellParser.RULE_compound_stmt

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class StmtIfContext(Compound_stmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.Compound_stmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PyxellParser.ExprContext)
            else:
                return self.getTypedRuleContext(PyxellParser.ExprContext,i)

        def block(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PyxellParser.BlockContext)
            else:
                return self.getTypedRuleContext(PyxellParser.BlockContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStmtIf" ):
                return visitor.visitStmtIf(self)
            else:
                return visitor.visitChildren(self)



    def compound_stmt(self):

        localctx = PyxellParser.Compound_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_compound_stmt)
        self._la = 0 # Token type
        try:
            localctx = PyxellParser.StmtIfContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 41
            self.match(PyxellParser.T__4)
            self.state = 42
            self.expr(0)
            self.state = 43
            self.block()
            self.state = 50
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PyxellParser.T__5:
                self.state = 44
                self.match(PyxellParser.T__5)
                self.state = 45
                self.expr(0)
                self.state = 46
                self.block()
                self.state = 52
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 55
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PyxellParser.T__6:
                self.state = 53
                self.match(PyxellParser.T__6)
                self.state = 54
                self.block()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def stmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PyxellParser.StmtContext)
            else:
                return self.getTypedRuleContext(PyxellParser.StmtContext,i)


        def getRuleIndex(self):
            return PyxellParser.RULE_block

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlock" ):
                return visitor.visitBlock(self)
            else:
                return visitor.visitChildren(self)




    def block(self):

        localctx = PyxellParser.BlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_block)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 57
            self.match(PyxellParser.T__7)
            self.state = 58
            self.match(PyxellParser.T__8)
            self.state = 60 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 59
                self.stmt()
                self.state = 62 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PyxellParser.T__1) | (1 << PyxellParser.T__2) | (1 << PyxellParser.T__4) | (1 << PyxellParser.T__13) | (1 << PyxellParser.T__14) | (1 << PyxellParser.T__15) | (1 << PyxellParser.T__17) | (1 << PyxellParser.T__18) | (1 << PyxellParser.INT) | (1 << PyxellParser.ID))) != 0)):
                    break

            self.state = 64
            self.match(PyxellParser.T__9)
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
        _startState = 10
        self.enterRecursionRule(localctx, 10, self.RULE_expr, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.T__13, PyxellParser.T__14]:
                localctx = PyxellParser.ExprUnaryOpContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 67
                localctx.op = self._input.LT(1)
                _la = self._input.LA(1)
                if not(_la==PyxellParser.T__13 or _la==PyxellParser.T__14):
                    localctx.op = self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 68
                self.expr(3)
                pass
            elif token in [PyxellParser.T__15]:
                localctx = PyxellParser.ExprParenthesesContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 69
                self.match(PyxellParser.T__15)
                self.state = 70
                self.expr(0)
                self.state = 71
                self.match(PyxellParser.T__16)
                pass
            elif token in [PyxellParser.T__17, PyxellParser.T__18, PyxellParser.INT, PyxellParser.ID]:
                localctx = PyxellParser.ExprAtomContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 73
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 84
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,9,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 82
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,8,self._ctx)
                    if la_ == 1:
                        localctx = PyxellParser.ExprBinaryOpContext(self, PyxellParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 76
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 77
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PyxellParser.T__10) | (1 << PyxellParser.T__11) | (1 << PyxellParser.T__12))) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 78
                        self.expr(6)
                        pass

                    elif la_ == 2:
                        localctx = PyxellParser.ExprBinaryOpContext(self, PyxellParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 79
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 80
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==PyxellParser.T__13 or _la==PyxellParser.T__14):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 81
                        self.expr(5)
                        pass

             
                self.state = 86
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,9,self._ctx)

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



    class AtomBoolContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PyxellParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtomBool" ):
                return visitor.visitAtomBool(self)
            else:
                return visitor.visitChildren(self)


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
        self.enterRule(localctx, 12, self.RULE_atom)
        self._la = 0 # Token type
        try:
            self.state = 90
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PyxellParser.INT]:
                localctx = PyxellParser.AtomIntContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 87
                self.match(PyxellParser.INT)
                pass
            elif token in [PyxellParser.T__17, PyxellParser.T__18]:
                localctx = PyxellParser.AtomBoolContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 88
                _la = self._input.LA(1)
                if not(_la==PyxellParser.T__17 or _la==PyxellParser.T__18):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [PyxellParser.ID]:
                localctx = PyxellParser.AtomIdContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 89
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
        self._predicates[5] = self.expr_sempred
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
         




