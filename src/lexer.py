
import re
from typing import NamedTuple, Tuple
import enum
# See also pyxell-syntax.js for regexes regarding syntax highlighting in the documentation.
# TODO: DRY
KEYWORDS = {
    '_', 'false', 'null', 'super', 'this', 'true',
    'abstract', 'and', 'as', 'break', 'by', 'class', 'constructor', 'continue', 'def', 'destructor', 'do', 'elif', 'else', 'extern', 'for', 'func', 'hiding', 'if', 'in', 'is', 'label', 'lambda', 'not', 'only', 'or', 'print', 'return', 'skip', 'super', 'until', 'use', 'while', 'yield',
}
ASSIGNMENT_OPERATORS = ['^=', '^^=', '/=', '//=', '%=', '*=', '&=', '+=', '-=', '??=']
MULTI_CHARACTER_OPERATORS = ['?.', '@(', '^^', '//', '%%', '?[', '??', '...:', '...', '..', '==', '!=', '<=', '>=', '->']

ID_REGEX = r'''[a-zA-Z_][\w']*'''
NUMBER_REGEX = r'''0b[01_]+|0o[0-7_]+|0x[\da-fA-F_]+|\d[\d_]*(?:r|(?:\.[\d_]+)?(?:[eE][-+]?[\d_]+|f)?)?'''
ESCAPE_SEQ_REGEX = r'''[\\abfnrt]|x[0-9a-fA-F]+'''
CHAR_REGEX = rf'''\'(?:[^\\']|\\(?:'|{ESCAPE_SEQ_REGEX}))\''''
STRING_REGEX = rf'''\"(?:[^\\"]|\\(?:"|{ESCAPE_SEQ_REGEX}))*\"'''

class TokenTypeEnum(enum.Enum):
    NUMBER = 'NUMBER'
    CHAR = 'CHAR'
    STRING = 'STRING'
    ID = 'ID'
    OTHER = 'OTHER'
    EOF = 'EOF'

class Token(NamedTuple):
    text: str
    type: TokenTypeEnum
    position: Tuple[int, int]


def tokenize(lines, start_position=(1, 1)):
    # Note that order matters here, e.g. longer operators must be before the ones that are their prefixes (like '...' and '..' or '??=' and '??').
    operator_regex = '|'.join(re.escape(op) for op in ASSIGNMENT_OPERATORS + MULTI_CHARACTER_OPERATORS) + r'|\W'
    regex = re.compile(f'({ID_REGEX}|{NUMBER_REGEX}|{CHAR_REGEX}|{STRING_REGEX}|{operator_regex}| +)')

    tokens = []
    for i, line in enumerate(lines, start_position[0]):
        j = start_position[1]
        for text in filter(None, re.split(regex, line)):
            # It's enough to look at the first character to decide which pattern (token type) has been matched.
            c = text[0]
            if c != ' ':  # only spaces are allowed as whitespace characters
                type = Token.OTHER
                if c.isidentifier() and text not in KEYWORDS:
                    type = TokenTypeEnum.ID
                elif c.isdigit():
                    type = TokenTypeEnum.NUMBER
                elif c == '\'' and len(text) > 1:
                    type = TokenTypeEnum.CHAR
                elif c == '"' and len(text) > 1:
                    type = TokenTypeEnum.STRING
                tokens.append(Token(text, type, (i, j)))
            j += len(text)

    tokens.append(Token('', TokenTypeEnum.EOF, (len(lines) - 1 + start_position[0], len(lines[-1]) + start_position[1])))
    return tokens
