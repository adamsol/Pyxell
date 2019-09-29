# Generated from Pyxell.g4 by ANTLR 4.7.2
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\17")
        buf.write("W\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\3\2\3\2\3\2\3\2\3")
        buf.write("\2\3\2\3\3\3\3\3\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b")
        buf.write("\3\t\3\t\3\n\3\n\3\13\3\13\3\f\6\f=\n\f\r\f\16\f>\3\r")
        buf.write("\3\r\7\rC\n\r\f\r\16\rF\13\r\3\16\3\16\3\17\3\17\3\20")
        buf.write("\3\20\3\20\5\20O\n\20\3\21\6\21R\n\21\r\21\16\21S\3\21")
        buf.write("\3\21\2\2\22\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13")
        buf.write("\25\f\27\r\31\16\33\2\35\2\37\2!\17\3\2\6\3\2\62;\5\2")
        buf.write("C\\aac|\4\2))aa\5\2\13\f\17\17\"\"\2X\2\3\3\2\2\2\2\5")
        buf.write("\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2")
        buf.write("\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2")
        buf.write("\2\2\27\3\2\2\2\2\31\3\2\2\2\2!\3\2\2\2\3#\3\2\2\2\5)")
        buf.write("\3\2\2\2\7+\3\2\2\2\t-\3\2\2\2\13/\3\2\2\2\r\61\3\2\2")
        buf.write("\2\17\63\3\2\2\2\21\65\3\2\2\2\23\67\3\2\2\2\259\3\2\2")
        buf.write("\2\27<\3\2\2\2\31@\3\2\2\2\33G\3\2\2\2\35I\3\2\2\2\37")
        buf.write("N\3\2\2\2!Q\3\2\2\2#$\7r\2\2$%\7t\2\2%&\7k\2\2&\'\7p\2")
        buf.write("\2\'(\7v\2\2(\4\3\2\2\2)*\7=\2\2*\6\3\2\2\2+,\7?\2\2,")
        buf.write("\b\3\2\2\2-.\7,\2\2.\n\3\2\2\2/\60\7\61\2\2\60\f\3\2\2")
        buf.write("\2\61\62\7\'\2\2\62\16\3\2\2\2\63\64\7-\2\2\64\20\3\2")
        buf.write("\2\2\65\66\7/\2\2\66\22\3\2\2\2\678\7*\2\28\24\3\2\2\2")
        buf.write("9:\7+\2\2:\26\3\2\2\2;=\5\33\16\2<;\3\2\2\2=>\3\2\2\2")
        buf.write("><\3\2\2\2>?\3\2\2\2?\30\3\2\2\2@D\5\35\17\2AC\5\37\20")
        buf.write("\2BA\3\2\2\2CF\3\2\2\2DB\3\2\2\2DE\3\2\2\2E\32\3\2\2\2")
        buf.write("FD\3\2\2\2GH\t\2\2\2H\34\3\2\2\2IJ\t\3\2\2J\36\3\2\2\2")
        buf.write("KO\5\35\17\2LO\5\33\16\2MO\t\4\2\2NK\3\2\2\2NL\3\2\2\2")
        buf.write("NM\3\2\2\2O \3\2\2\2PR\t\5\2\2QP\3\2\2\2RS\3\2\2\2SQ\3")
        buf.write("\2\2\2ST\3\2\2\2TU\3\2\2\2UV\b\21\2\2V\"\3\2\2\2\7\2>")
        buf.write("DNS\3\b\2\2")
        return buf.getvalue()


class PyxellLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    T__8 = 9
    T__9 = 10
    INT = 11
    ID = 12
    WS = 13

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'print'", "';'", "'='", "'*'", "'/'", "'%'", "'+'", "'-'", 
            "'('", "')'" ]

    symbolicNames = [ "<INVALID>",
            "INT", "ID", "WS" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "T__9", "INT", "ID", "DIGIT", "ID_START", 
                  "ID_CONT", "WS" ]

    grammarFileName = "Pyxell.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


