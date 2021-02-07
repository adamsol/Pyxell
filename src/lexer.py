
import re

# See also pyxell-syntax.js for regexes regarding syntax highlighting in the documentation.
# TODO: DRY
KEYWORDS = {
    'false', 'null', 'super', 'this', 'true',
    'abstract', 'and', 'as', 'break', 'by', 'class', 'constructor', 'continue', 'def', 'destructor', 'do', 'elif', 'else', 'extern', 'for', 'func', 'hiding', 'if', 'in', 'is', 'label', 'lambda', 'not', 'only', 'or', 'print', 'return', 'skip', 'super', 'until', 'use', 'while', 'yield',
}
ASSIGNMENT_OPERATORS = ['^=', '^^=', '/=', '//=', '%=', '*=', '&=', '+=', '-=', '??=']
MULTI_CHARACTER_OPERATORS = ['?.', '@(', '^^', '//', '%%', '?[', '??', '...:', '...', '..', '==', '!=', '<=', '>=', '->']

ID_REGEX = r'''[a-zA-Z_][\w']*'''
NUMBER_REGEX = r'''0b[01_]+|0o[0-7_]+|0x[\da-fA-F_]+|\d[\d_]*(?:r|(?:\.[\d_]+)?(?:[eE][-+]?[\d_]+|f)?)?'''
ESCAPE_SEQ_REGEX = r'''[\\abfnrt]|x[0-9a-fA-F]+'''
CHAR_REGEX = rf'''\'(?:[^\\']|\\(?:'|{ESCAPE_SEQ_REGEX}))\''''
STRING_REGEX = rf'''\"(?:[^\\"]|\\(?:"|{ESCAPE_SEQ_REGEX}))*\"'''


class Token:
    NUMBER = 'NUMBER'
    CHAR = 'CHAR'
    STRING = 'STRING'
    ID = 'ID'
    OTHER = 'OTHER'
    EOF = 'EOF'

    def __init__(self, text, type, position):
        self.text = text
        self.type = type
        self.position = position

    def __repr__(self):
        return f"Token('{self.text}', {self.type}, {self.position}))"

    def __eq__(self, other):
        raise TypeError("Use `text` property for comparing token strings.")


def tokenize(lines):
    # Note that order matters here, e.g. longer operators must be before the ones that are their prefixes (like '...' and '..' or '??=' and '??').
    operator_regex = '|'.join(re.escape(op) for op in ASSIGNMENT_OPERATORS + MULTI_CHARACTER_OPERATORS) + r'|\W'
    regex = re.compile(f'({ID_REGEX}|{NUMBER_REGEX}|{CHAR_REGEX}|{STRING_REGEX}|{operator_regex}| +)')

    tokens = []
    for i, line in enumerate(lines, 1):
        j = 1
        for text in filter(None, re.split(regex, line)):
            # It's enough to look at the first character to decide which pattern (token type) has been matched.
            c = text[0]
            if c != ' ':  # only spaces are allowed as whitespace characters
                type = Token.OTHER
                if (c.isalpha() or c == '_') and text not in KEYWORDS:
                    type = Token.ID
                elif c.isdigit():
                    type = Token.NUMBER
                elif c == '\'' and len(text) > 1:
                    type = Token.CHAR
                elif c == '"' and len(text) > 1:
                    type = Token.STRING
                tokens.append(Token(text, type, (i, j)))
            j += len(text)

    tokens.append(Token('', Token.EOF, (len(lines), len(lines[-1]))))
    return tokens
